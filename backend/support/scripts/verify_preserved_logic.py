"""Compare algorithm ASTs against the original source; ignore moved imports."""
import argparse
import ast
from pathlib import Path


class ProviderNormalization(ast.NodeTransformer):
    """Ignore the provider wiring/model changes explicitly requested by the user."""
    def visit_ImportFrom(self, node):
        return None

    def visit_Call(self, node):
        node = self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id in {"ChatOpenAI", "create_chat_model"}:
            return ast.Call(func=ast.Name(id="configured_openai_chat", ctx=ast.Load()), args=[], keywords=[])
        if isinstance(node.func, ast.Name) and node.func.id in {"OpenAIEmbeddings", "create_embeddings"}:
            return ast.Call(func=ast.Name(id="configured_openai_embeddings", ctx=ast.Load()), args=[], keywords=[])
        return node


def algorithms(path):
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    tree = ProviderNormalization().visit(tree)
    return {node.name: ast.dump(node, include_attributes=False)
            for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    args = parser.parse_args()
    target = Path(__file__).resolve().parents[3]
    if not (args.source / "backend/app/modules/ai/rag/hybrid_retrieval.py").exists():
        backup_dir = args.source.parent / (args.source.name + "_backups")
        backups = sorted(backup_dir.glob("*"), reverse=True)
        baseline = next((b for b in backups if (b / "backend/app/modules/ai/rag/hybrid_retrieval.py").exists()), None)
        if baseline is None:
            parser.error("Original source or an original-source backup is required")
        args.source = baseline
    pairs = {
        "matching/embeddings.py": "matching/embeddings.py",
        "matching/ranking.py": "matching/ranking.py",
        "matching/service.py": "matching/service.py",
        "rag/graph.py": "rag/graph.py",
        "rag/state.py": "rag/state.py",
        "rag/validation.py": "rag/validation.py",
        "rag/reranking.py": "rag/reranking.py",
        "rag/hybrid_retrieval.py": "rag/retrieval/hybrid.py",
        "rag/prompt.py": "rag/generation/prompt.py",
        "rag/query_expansion.py": "rag/generation/query_expansion.py",
        "rag/evidence.py": "rag/generation/evidence.py",
        "rag/document_processing/parsing.py": "rag/ingestion/parsing.py",
    }
    total = 0
    for old, new in pairs.items():
        before = algorithms(args.source / "backend/app/modules/ai" / old)
        after = algorithms(target / "backend/app/modules/ai" / new)
        if old == "matching/embeddings.py":
            # The user explicitly requested reusing the OpenAI provider for matching.
            before.pop("get_embedder")
            after.pop("get_embedder")
            after.pop("OpenAIEmbedder", None)
        assert before == after, f"Algorithm changed: {old}"
        total += len(before)
    # Chunking functions moved to a storage adapter are compared individually.
    before = algorithms(args.source / "backend/app/modules/ai/rag/document_processing/chunking.py")
    after = algorithms(target / "backend/app/modules/ai/rag/ingestion/chunking.py")
    after.update(algorithms(target / "backend/app/modules/ai/rag/retrieval/qdrant_store.py"))
    for name, body in before.items():
        # save_chunks has only its local import path updated.
        if name == "save_chunks":
            body = body.replace("app.modules.ai.rag.indexing.embeddings", "app.modules.ai.rag.retrieval.embeddings")
        assert after.get(name) == body, f"Chunking/storage function changed: {name}"
        total += 1
    print(f"PASS: {total} original algorithm functions/classes match after normalizing imports and authorized OpenAI client configuration.")
    print(f"Baseline: {args.source}")


if __name__ == "__main__":
    main()
