import urllib.parse
from typing import List, Dict, Any

def get_tutorial_videos(scheme_name: str, state: str = "National") -> List[Dict[str, Any]]:
    """
    Returns a YouTube search link for the given scheme.
    Uses a live YouTube search query so the result is always fresh.
    """
    query = f"{scheme_name} scheme application process guide {state}"
    encoded_query = urllib.parse.quote(query)

    return [
        {
            "title": f"How to Apply for {scheme_name} - Search YouTube",
            "video_url": f"https://www.youtube.com/results?search_query={encoded_query}",
            "thumbnail_url": None,
            "duration": None,
            "channel": "YouTube"
        }
    ]
