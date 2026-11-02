import argparse
import os
from collections import Counter
from typing import Any

from dotenv import load_dotenv
from qdrant_client import QdrantClient


load_dotenv()

COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION",
    "internship-connect-openai",
)


def _create_client() -> QdrantClient:
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")

    if not url:
        raise RuntimeError("Missing QDRANT_URL in environment/.env")

    return QdrantClient(
        url=url,
        api_key=api_key,
        prefer_grpc=False,
    )


def _iter_points(client: QdrantClient):
    offset = None

    while True:
        points, next_offset = client.scroll(
            collection_name=COLLECTION_NAME,
            offset=offset,
            limit=100,
            with_payload=True,
            with_vectors=False,
        )

        for point in points:
            yield point

        if next_offset is None:
            break

        offset = next_offset


def _parse_point(point: Any) -> dict[str, Any]:
    payload = point.payload or {}

    content = (
        payload.get("page_content")
        or payload.get("content")
        or payload.get("text")
        or ""
    )

    metadata = payload.get("metadata")

    if not isinstance(metadata, dict):
        metadata = {}

    merged_metadata = dict(metadata)

    for key in (
        "source",
        "page",
        "page_number",
        "chunk_id",
        "chunk_index",
        "document_id",
    ):
        if key in payload and key not in merged_metadata:
            merged_metadata[key] = payload[key]

    return {
        "point_id": str(point.id),
        "content": str(content),
        "metadata": merged_metadata,
    }


def inspect_collection(
    client: QdrantClient,
    show: int = 0,
    full: bool = False,
    source: str | None = None,
    contains: str | None = None,
) -> None:

    info = client.get_collection(COLLECTION_NAME)

    chunks = [
        _parse_point(point)
        for point in _iter_points(client)
    ]

    # Filter source
    if source:
        source_lower = source.lower()

        chunks = [
            chunk
            for chunk in chunks
            if source_lower
            in str(
                chunk["metadata"].get("source", "")
            ).lower()
        ]

    # Filter content
    if contains:
        contains_lower = contains.lower()

        chunks = [
            chunk
            for chunk in chunks
            if contains_lower
            in chunk["content"].lower()
        ]

    print("=" * 80)
    print("COLLECTION INFO")
    print("=" * 80)

    print(f"Collection : {COLLECTION_NAME}")
    print(f"Points     : {info.points_count}")
    print(f"Status     : {info.status}")

    print("=" * 80)

    print(f"Chunks loaded : {len(chunks)}")

    # Statistics by source
    if chunks:

        sources = Counter(
            str(
                chunk["metadata"].get(
                    "source",
                    "UNKNOWN"
                )
            )
            for chunk in chunks
        )

        print("\nChunks by source:")

        for source_name, count in sources.most_common():
            print(
                f"  {source_name}: {count}"
            )

    if source:
        print(f"Filter source : {source}")

    if contains:
        print(f"Filter text   : {contains}")

    # Show chunks
    if show > 0:

        count = min(
            show,
            len(chunks)
        )

        print("\n" + "=" * 80)
        print(f"{count} CHUNK(S)")
        print("=" * 80)

        for index, chunk in enumerate(
            chunks[:count],
            start=1
        ):

            metadata = chunk["metadata"]

            text = chunk["content"].strip()

            if (
                not full
                and len(text) > 300
            ):
                text = text[:300] + " ..."

            print(f"\n[{index}]")

            print(
                f"Point ID   : "
                f"{chunk['point_id']}"
            )

            print(
                f"Chunk ID   : "
                f"{metadata.get('chunk_id', 'N/A')}"
            )

            print(
                f"Document   : "
                f"{metadata.get('document_id', 'N/A')}"
            )

            print(
                f"Source     : "
                f"{metadata.get('source', 'N/A')}"
            )

            print(
                f"Page       : "
                f"{metadata.get(
                    'page',
                    metadata.get(
                        'page_number',
                        'N/A'
                    )
                )}"
            )

            print(
                f"Chunk idx  : "
                f"{metadata.get(
                    'chunk_index',
                    'N/A'
                )}"
            )

            print("-" * 80)

            print(text)


def main() -> None:

    parser = argparse.ArgumentParser(
        description=(
            "Inspect chunks stored in Qdrant."
        )
    )

    parser.add_argument(
        "--show",
        type=int,
        default=0,
        help=(
            "Number of chunks to print."
        ),
    )

    parser.add_argument(
        "--full",
        action="store_true",
        help=(
            "Print full chunk content."
        ),
    )

    parser.add_argument(
        "--source",
        type=str,
        default=None,
        help=(
            "Only show chunks whose "
            "source contains this text."
        ),
    )

    parser.add_argument(
        "--contains",
        type=str,
        default=None,
        help=(
            "Only show chunks whose "
            "content contains this text."
        ),
    )

    args = parser.parse_args()

    client = _create_client()

    inspect_collection(
        client=client,
        show=args.show,
        full=args.full,
        source=args.source,
        contains=args.contains,
    )


if __name__ == "__main__":
    main()
