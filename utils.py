"""
Utility helper functions.

This file currently contains a helper function to convert a normal
YouTube URL into an embeddable URL that can be used inside an iframe.
"""

# Imports tools to break down and read parts of a URL
from urllib.parse import urlparse, parse_qs


# Function that converts a normal YouTube link into an embed link
def youtube_embed_url(url: str) -> str | None:
    """
    Convert common YouTube URL formats into an embeddable URL.

    Supported formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID

    Returns:
        embeddable URL string if valid, otherwise None
    """

    # If no URL is provided, return None (nothing to embed)
    if not url:
        return None

    try:
        # Breaks the URL into parts (domain, path, query, etc.)
        parsed = urlparse(url)

        # Handles standard YouTube links (youtube.com/watch?v=...)
        if "youtube.com" in parsed.netloc:

            # Gets the query part of the URL (everything after ?)
            query = parse_qs(parsed.query)

            # Extracts the video ID from the "v" parameter
            video_id = query.get("v", [None])[0]

            # If a video ID exists, return an embeddable URL
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"

        # Handles shortened YouTube links (youtu.be/VIDEO_ID)
        if "youtu.be" in parsed.netloc:

            # Gets the video ID from the URL path
            video_id = parsed.path.lstrip("/")

            # If a video ID exists, return an embeddable URL
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"

    # If anything goes wrong while parsing, return None safely
    except Exception:
        return None

    # If no valid format matched, return None
    return None