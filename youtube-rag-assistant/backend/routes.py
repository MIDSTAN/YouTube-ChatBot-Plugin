from typing import Literal
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from backend.transcript import get_english_transcript
from rag.chunking import create_transcript_chunks
from rag.vector_store import index_video_chunks
from rag.pipeline import answer_question


router = APIRouter()

# Limit concurrent indexing jobs to avoid excessive CPU/RAM use.
_index_executor = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="transcript-index",
)


class TranscriptRequest(BaseModel):
    video_id: str = Field(
        pattern=r"^[A-Za-z0-9_-]{11}$"
    )

    language: Literal["en"] = "en"


class ChatRequest(BaseModel):
    video_id: str = Field(
        pattern=r"^[A-Za-z0-9_-]{11}$"
    )

    question: str = Field(
        min_length=1,
        max_length=2000,
    )


def _index_transcript(video_id: str) -> int:
    """
    Perform transcript retrieval and indexing.

    Runs outside the main async event loop.
    """

    segments = get_english_transcript(video_id)

    chunks = create_transcript_chunks(
        segments=segments,
        video_id=video_id,
    )

    count = index_video_chunks(
        video_id=video_id,
        documents=chunks,
    )

    return count


@router.post("/transcript")
async def prepare_transcript(request: TranscriptRequest):
    """
    Extract and index a video's English transcript.
    """

    try:
        loop_future = __import__("asyncio").get_running_loop()

        count = await loop_future.run_in_executor(
            _index_executor,
            _index_transcript,
            request.video_id,
        )

        return {
            "status": "ready",
            "video_id": request.video_id,
            "language": request.language,
            "chunks_indexed": count,
            "message": "Transcript indexed successfully.",
        }

    except Exception as error:
        raise HTTPException(
            status_code=422,
            detail=f"Transcript processing failed: {error}",
        ) from error


@router.post("/chat")
async def chat(request: ChatRequest):
    """
    Answer a question using the selected video's transcript.
    """

    try:
        result = await run_in_threadpool(
            answer_question,
            request.video_id,
            request.question,
        )

        return result

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Answer generation failed: {error}",
        ) from error