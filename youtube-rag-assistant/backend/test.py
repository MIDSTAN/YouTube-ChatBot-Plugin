import re
from urllib.parse import urlparse, parse_qs

from youtube_transcript_api import YouTubeTranscriptApi


# --------------------------------------------------
# Demo YouTube video
# --------------------------------------------------

VIDEO_URL = "https://www.youtube.com/watch?v=jNQXAC9IVRw"


# --------------------------------------------------
# Extract video ID from URL
# --------------------------------------------------

def extract_video_id(url: str) -> str:
    parsed_url = urlparse(url)

    if parsed_url.hostname in ("youtube.com", "www.youtube.com", "m.youtube.com"):
        video_id = parse_qs(parsed_url.query).get("v", [None])[0]

    elif parsed_url.hostname == "youtu.be":
        video_id = parsed_url.path.strip("/")

    else:
        raise ValueError("Unsupported YouTube URL")

    if not video_id or not re.fullmatch(r"[A-Za-z0-9_-]{11}", video_id):
        raise ValueError("Invalid YouTube video ID")

    return video_id


# --------------------------------------------------
# Extract English transcript
# --------------------------------------------------

def extract_transcript(video_id: str):

    api = YouTubeTranscriptApi()

    # Prefer English captions.
    transcript = api.fetch(
        video_id,
        languages=["en"]
    )

    return transcript


# --------------------------------------------------
# Main execution
# --------------------------------------------------

def main():

    try:
        print("=" * 60)
        print("YOUTUBE TRANSCRIPT EXTRACTION TEST")
        print("=" * 60)

        print("\nVideo URL:")
        print(VIDEO_URL)

        video_id = extract_video_id(VIDEO_URL)

        print("\nExtracted Video ID:")
        print(video_id)

        print("\nFetching English transcript...")

        transcript = extract_transcript(video_id)

        print("\nTranscript Language:")
        print(transcript.language)

        print("\nLanguage Code:")
        print(transcript.language_code)

        print("\nAutomatically Generated:")
        print(transcript.is_generated)

        print("\nTotal Transcript Segments:")
        print(len(transcript))

        print("\n" + "=" * 60)
        print("FIRST 20 TRANSCRIPT SEGMENTS")
        print("=" * 60)

        for segment in list(transcript)[:20]:
            timestamp = int(segment.start)
            minutes = timestamp // 60
            seconds = timestamp % 60

            print(
                f"[{minutes:02d}:{seconds:02d}] "
                f"{segment.text}"
            )

        # Save the complete transcript.
        with open(
            "transcript.txt",
            "w",
            encoding="utf-8"
        ) as file:

            for segment in transcript:
                file.write(
                    f"[{segment.start:.2f}] {segment.text}\n"
                )

        print("\nComplete transcript saved to transcript.txt")

        print("\nTEST SUCCESSFUL")

    except Exception as error:

        print("\nTEST FAILED")
        print("Error type:", type(error).__name__)
        print("Error details:", error)


if __name__ == "__main__":
    main()