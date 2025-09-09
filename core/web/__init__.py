"""Web search utilities."""

from .search import (
    DEFAULT_TRUSTED_DOMAINS,
    BraveSearchError,
    WebResult,
    brave_search,
)

__all__ = ["WebResult", "brave_search", "BraveSearchError", "DEFAULT_TRUSTED_DOMAINS"]
