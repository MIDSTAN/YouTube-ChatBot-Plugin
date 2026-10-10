from pathlib import Path

from langchain_chroma import Chroma
from langchain_core.documents import Document

from rag.embeddings import get_embeddings


# Stored inside the project root.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIRECTORY = PROJECT_ROOT / "chroma_db"

COLLECTION_NAME = "youtube_transcripts"


def get_vector_store() -> Chroma:
    """
    Return the shared Chroma vector store.
    """

    CHROMA_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=get_embeddings(),
        persist_directory=str(CHROMA_DIRECTORY),
    )


def index_video_chunks(
    video_id: str,
    documents: list[Document],
) -> int:
    """
    Replace previously indexed chunks for this video,
    then store its new chunks.
    """

    if not documents:
        raise ValueError("No chunks supplied for indexing.")

    store = get_vector_store()

    # Remove older chunks for this video to prevent duplicates.
    store.delete(
        where={"video_id": video_id}
    )

    # Use deterministic IDs for the new chunks.
    ids = [
        f"{video_id}_{index}"
        for index in range(len(documents))
    ]

    store.add_documents(
        documents=documents,
        ids=ids,
    )

    return len(documents)


def retrieve_relevant_chunks(
    video_id: str,
    question: str,
    k: int = 5,
) -> list[Document]:
    """
    Search only within the current video's chunks.
    """

    store = get_vector_store()

    return store.similarity_search(
        query=question,
        k=k,
        filter={"video_id": video_id},
    )