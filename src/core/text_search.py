"""
Text Search Engine - Finds all occurrences of words/phrases across all pages.
This is the core of the manual redaction workflow.
"""

from dataclasses import dataclass


@dataclass
class SearchResult:
    """A search match: which block on which page."""
    block_index: int  # global block index
    page: int
    text: str


class TextSearchEngine:
    """Searches across all extracted text blocks."""

    def __init__(self):
        self._blocks = []  # flat list of all TextBlocks
        self._page_offsets = []  # (start, end) per page

    def set_blocks(self, pages_blocks: list[list]) -> None:
        """Load blocks from all pages into the search index."""
        self._blocks = []
        self._page_offsets = []
        for page_blocks in pages_blocks:
            start = len(self._blocks)
            self._blocks.extend(page_blocks)
            self._page_offsets.append((start, len(self._blocks)))

    @property
    def total_blocks(self) -> int:
        return len(self._blocks)

    def get_block(self, global_idx: int):
        if 0 <= global_idx < len(self._blocks):
            return self._blocks[global_idx]
        return None

    def get_page_range(self, page_idx: int) -> tuple[int, int]:
        """Return (start, end) global indices for a page."""
        if 0 <= page_idx < len(self._page_offsets):
            return self._page_offsets[page_idx]
        return (0, 0)

    def search(self, query: str, case_sensitive: bool = False) -> list[SearchResult]:
        """Find all blocks whose text matches the query."""
        if not query:
            return []

        results: list[SearchResult] = []
        q = query if case_sensitive else query.lower()

        for idx, block in enumerate(self._blocks):
            text = block.text if case_sensitive else block.text.lower()
            if q in text:
                results.append(SearchResult(
                    block_index=idx, page=block.page, text=block.text,
                ))
        return results

    def search_exact_word(self, word: str) -> list[int]:
        """Find all block indices where the block text matches exactly (case-insensitive)."""
        if not word:
            return []
        w = word.strip().lower()
        return [
            idx for idx, block in enumerate(self._blocks)
            if block.text.strip().lower() == w
        ]

    def search_multi_words(self, words: list[str]) -> set[int]:
        """Find all block indices matching any of the given words."""
        indices: set[int] = set()
        for word in words:
            indices.update(self.search_exact_word(word))
        return indices
