def test_matching_reuses_rag_embedding_provider(monkeypatch):
    from app.modules.ai.matching import embeddings
    from app.modules.ai.providers import openai_client
    calls = []
    class Model:
        def embed_query(self, value):
            calls.append(value)
            return [0.6, 0.8]
    monkeypatch.setattr(openai_client, "create_embeddings", lambda: Model())
    embedder = embeddings.OpenAIEmbedder()
    assert embedder.embed("Python SQL") == [0.6, 0.8]
    assert embedder.dim == 2
    assert calls == ["Python SQL"]
