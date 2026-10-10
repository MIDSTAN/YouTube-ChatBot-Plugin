import re
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi


def validate_video_id(video_id: str) -> str:
    """
    Validate a YouTube video ID.
    """

    if not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Invalid YouTube video ID.")

    return video_id


def extract_video_id(video_url: str) -> str:
    """
    Extract a video ID from a YouTube URL.
    """

    parsed = urlparse(video_url)

    hostname = parsed.hostname or ""

    if hostname in (
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
    ):
        video_id = parse_qs(
            parsed.query
        ).get("v", [None])[0]

    elif hostname == "youtu.be":
        video_id = parsed.path.strip("/")

    else:
        raise ValueError("Unsupported YouTube URL.")

    return validate_video_id(video_id or "")


def get_english_transcript(video_id: str):
    """
    Fetch English captions for a YouTube video.

    Returns timestamped transcript segments.
    """

    validate_video_id(video_id)

    api = YouTubeTranscriptApi()

    transcript = api.fetch(
        video_id,
        languages=["en"],
    )

    segments = list(transcript)

    if not segments:
        raise ValueError(
            "No English transcript segments were found."
        )

    return segments