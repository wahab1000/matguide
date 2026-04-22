"""
Utility helper functions.

This file currently contains a helper function to convert a normal
YouTube URL into an embeddable URL that can be used inside an iframe.
"""

from urllib.parse import urlparse, parse_qs


def youtube_embed_url(url: str) -> str | None:
    """
    Convert common YouTube URL formats into an embeddable URL.

    Supported formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID

    Returns:
        embeddable URL string if valid, otherwise None
    """
    if not url:
        return None

    try:
        parsed = urlparse(url)

        # Standard youtube.com/watch?v=...
        if "youtube.com" in parsed.netloc:
            query = parse_qs(parsed.query)
            video_id = query.get("v", [None])[0]
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"

        # Short youtu.be/...
        if "youtu.be" in parsed.netloc:
            video_id = parsed.path.lstrip("/")
            if video_id:
                return f"https://www.youtube.com/embed/{video_id}"

    except Exception:
        return None

    return None