"""Web search and fetch tools for Scout agent."""
from __future__ import annotations

import httpx
import logging
from pydantic import BaseModel
from typing import Literal

logger = logging.getLogger(__name__)

# Anthropic tool definitions (passed directly to Claude API)
WEB_SEARCH_TOOL = {
    "name": "web_search",
    "description": "Search the web for patents, scientific articles, industry news, and competitor information.",
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "Search query"},
            "source_type": {
                "type": "string",
                "enum": ["patents", "scientific", "news", "competitors", "general"],
                "description": "Type of source to search",
            },
        },
        "required": ["query"],
    },
}

WEB_FETCH_TOOL = {
    "name": "web_fetch",
    "description": "Fetch the content of a specific URL and return its text.",
    "input_schema": {
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to fetch"},
        },
        "required": ["url"],
    },
}


async def web_fetch(url: str, timeout: int = 30) -> str:
    """Fetch URL content as text. Used as tool implementation."""
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            resp = await client.get(url, headers={"User-Agent": "Compass-Scout/1.0"})
            resp.raise_for_status()
            return resp.text[:50_000]  # cap at 50k chars
    except Exception as e:
        logger.warning("web_fetch failed for %s: %s", url, e)
        return f"ERROR: {e}"


TOOL_DEFINITIONS = [WEB_SEARCH_TOOL, WEB_FETCH_TOOL]
