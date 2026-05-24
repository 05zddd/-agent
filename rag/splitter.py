from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter


class DocumentSplitter:
    """Split long documents into smaller overlapping chunks for RAG."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: list = None,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", ".", "；", ";", " ", ""]

        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            length_function=len,
        )

    def split(self, text: str) -> List[str]:
        """Split text into chunks.

        Args:
            text: The document text to split

        Returns:
            List of text chunks
        """
        if not text.strip():
            return []
        return self.splitter.split_text(text)

    def split_with_metadata(self, text: str, metadata: dict = None) -> List[dict]:
        """Split text and attach metadata to each chunk.

        Args:
            text: Document text
            metadata: Base metadata to attach

        Returns:
            List of {"text": str, "metadata": dict} records
        """
        chunks = self.split(text)
        base_meta = metadata or {}
        return [
            {"text": chunk, "metadata": {**base_meta, "chunk_index": i}}
            for i, chunk in enumerate(chunks)
        ]
