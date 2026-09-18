# Storage for Libro's want_to_read collection.
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


class WantToReadStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL,
            device="cpu"
        )
        # Get or create the want_to_read collection
        self.collection = self.client.get_or_create_collection(
            name="want_to_read",
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}  # default, but explicit
        )

    def add(self, book: dict) -> bool:
        """Add a book to the want_to_read collection.
        Returns True if added, False if duplicate (based on dedup threshold).
        """
        # Prepare document and metadata
        document = f"{book['title']} by {book.get('author', '')}. {book['summary']}"
        # Flatten metadata: chromaDB requires str/int/float/bool
        metadata = {
            "title": book["title"],
            "author": book.get("author") or "",
            "genre_tags": ",".join(book["genre_tags"]),  # store as comma-separated string
            "summary": book["summary"],
            "source_type": book["source_type"],
            "confidence": float(book["confidence"]),
            "verdict": book["verdict"],
            "available_in_cloud_library": bool(book["available_in_cloud_library"]),
            "cloud_library_match": book.get("cloud_library_match") or "",
            "book_type": book.get("book_type") or "",
            "source_url": book.get("source_url") or "",
            "reading_status": book.get("reading_status", "want_to_read"),
        }
        # Generate ID from title and author
        import hashlib
        id_string = f"{book['title']}{book.get('author') or ''}"
        book_id = hashlib.md5(id_string.encode()).hexdigest()

        # Dedup check: query by title (or ID?) and see if we have a close match
        # We'll do a query by the document text? Or by ID? The spec says: deduplication: query by title before inserting, skip if relevance_score >= 0.92
        # We'll query by the title and author? We can do a metadata query? ChromaDB doesn't support metadata queries directly.
        # Instead, we can query by the document text (which includes title and author) and see if we get a high similarity.
        # But note: we are using the same embedding function, so we can embed the document and search.
        # However, we don't have the embedding function handy? We do: self.embedding_function.
        # We can embed the document and then query the collection for similar documents.
        # But note: the collection already has the embedding function set, so we can just query by the document text.
        try:
            results = self.collection.query(
                query_texts=[document],
                n_results=1,
                include=["distances", "metadatas"]
            )
            if results["distances"] and results["distances"][0]:
                distance = results["distances"][0][0]
                # ChromaDB returns distance (lower is closer). Convert to similarity: 1 - distance?
                # But note: the spec uses relevance_score (which is 1 - distance) and threshold 0.92.
                similarity = 1.0 - distance
                if similarity >= 0.92:
                    # Duplicate found
                    return False
        except Exception:
            # If query fails, we'll just add anyway (maybe collection is empty)
            pass

        # Add the book
        self.collection.add(
            documents=[document],
            metadatas=[metadata],
            ids=[book_id]
        )
        return True

    def all(self) -> list[dict]:
        """Return all entries as list of metadata dicts."""
        results = self.collection.get(include=["metadatas"])
        books = []
        for metadata in results["metadatas"]:
            # Convert stored metadata back to book dict format
            book = {
                "title": metadata["title"],
                "author": metadata["author"] if metadata["author"] else None,
                "genre_tags": metadata["genre_tags"].split(",") if metadata["genre_tags"] else [],
                "summary": metadata["summary"],
                "source_type": metadata["source_type"],
                "confidence": metadata["confidence"],
                "verdict": metadata["verdict"],
                "book_type": metadata.get("book_type") if metadata.get("book_type") else None,
                "source_url": metadata.get("source_url") if metadata.get("source_url") else None,
                "available_in_cloud_library": bool(metadata["available_in_cloud_library"]),
                "cloud_library_match": metadata["cloud_library_match"] if metadata["cloud_library_match"] else None,
                "is_read": bool(metadata.get("is_read", False)),
                "is_loved": bool(metadata.get("is_loved", False)),
            }
            books.append(book)
        return books

    def delete(self, book_id: str) -> None:
        """Remove entry by ID."""
        self.collection.delete(ids=[book_id])

    def search(self, query: str, k: int = 10) -> list[dict]:
        """Semantic search for query, return top k results as list of metadata dicts."""
        results = self.collection.query(
            query_texts=[query],
            n_results=k,
            include=["metadatas", "distances"]
        )
        books = []
        for metadata, distance in zip(results["metadatas"][0], results["distances"][0]):
            book = {
                "title": metadata["title"],
                "author": metadata["author"] if metadata["author"] else None,
                "genre_tags": metadata["genre_tags"].split(",") if metadata["genre_tags"] else [],
                "summary": metadata["summary"],
                "source_type": metadata["source_type"],
                "book_type": metadata.get("book_type") if metadata.get("book_type") else None,
                "source_url": metadata.get("source_url") if metadata.get("source_url") else None,
                "confidence": metadata["confidence"],
                "verdict": metadata["verdict"],
                "available_in_cloud_library": bool(metadata["available_in_cloud_library"]),
                "cloud_library_match": metadata["cloud_library_match"] if metadata["cloud_library_match"] else None,
                "is_read": bool(metadata.get("is_read", False)),
                "is_loved": bool(metadata.get("is_loved", False)),
            }
            books.append(book)
        return books
    def toggle_read(self, book_id: str, current: bool) -> None:
        """Toggle read status."""
        self.collection.update(ids=[book_id], metadatas=[{"is_read": not current}])

    def toggle_loved(self, book_id: str, current: bool) -> None:
        """Toggle loved status."""
        self.collection.update(ids=[book_id], metadatas=[{"is_loved": not current}])
