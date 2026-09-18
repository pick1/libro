# Read-only interface to AI Librarian's books collection.
# Uses ChromaDB with pysqlite3 swap.

try:
    import pysqlite3
    import sys
    sys.modules["sqlite3"] = pysqlite3
except ImportError:
    pass

import chromadb
from chromadb.utils import embedding_functions

from libro.config import CHROMA_PERSIST_DIR, EMBEDDING_MODEL


class LibrarianIndex:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL,
            device="cpu"
        )
        # Load the books collection as read-only (we assume it exists)
        self.collection = self.client.get_collection(
            name="books",
            embedding_function=self.embedding_function
        )
        # Do not use get_or_create_collection because we must not create it.

    def check_availability(self, title: str, author: str | None) -> tuple[bool, str | None]:
        """Check if a book is available in the AI Librarian's books collection.
        Returns (available_in_cloud_library: bool, matched_title: str | None).
        """
        if not title:
            return False, None

        # Embed the query: f\"{title} {author}\" (if author is not None)
        query_text = f"{title} {author or ''}".strip()
        if not query_text:
            return False, None

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=3,
                include=["distances", "metadatas"]
            )
            if not results["distances"] or not results["distances"][0]:
                return False, None

            # Check the top result
            distance = results["distances"][0][0]
            # Convert distance to relevance score: relevance = 1 - distance
            relevance = 1.0 - distance
            if relevance >= 0.85:
                # Match found
                matched_title = results["metadatas"][0][0].get("title")
                return True, matched_title
            else:
                return False, None
        except Exception:
            # If anything goes wrong, assume not available
            return False, None