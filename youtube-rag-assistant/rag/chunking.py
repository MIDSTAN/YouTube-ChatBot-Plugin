from langchain_core.documents import Document


def create_transcript_chunks(
    segments: list,
    video_id: str,
) -> list[Document]:
    """
    Group timestamped transcript segments into approximately
    60-second chunks.

    Each chunk stores its video ID and timestamps as metadata.
    """

    if not segments:
        raise ValueError("Transcript contains no segments.")

    chunk_duration = 60.0

    documents = []

    current_segments = []
    chunk_start = None
    chunk_end = None

    for segment in segments:
        text = str(segment.text).strip()

        if not text:
            continue

        start = float(segment.start)
        end = start + float(segment.duration)

        if (
            current_segments
            and start >= chunk_start + chunk_duration
        ):
            documents.append(
                _build_document(
                    current_segments,
                    video_id,
                    chunk_start,
                    chunk_end,
                )
            )

            current_segments = []
            chunk_start = None
            chunk_end = None

        if chunk_start is None:
            chunk_start = start

        current_segments.append(text)
        chunk_end = end

    if current_segments:
        documents.append(
            _build_document(
                current_segments,
                video_id,
                chunk_start,
                chunk_end,
            )
        )

    if not documents:
        raise ValueError("No usable transcript text was found.")

    return documents


def _build_document(
    segments: list[str],
    video_id: str,
    start_time: float,
    end_time: float,
) -> Document:

    return Document(
        page_content=" ".join(segments),
        metadata={
            "video_id": video_id,
            "start_time": float(start_time),
            "end_time": float(end_time),
        },
    )