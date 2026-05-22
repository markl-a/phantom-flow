"""Vector store for storing and retrieving embeddings."""

from typing import List, Optional, Dict, Any, Tuple
import chromadb
from chromadb.config import Settings
from pathlib import Path
from ai_automation_framework.core.base import BaseComponent
from ai_automation_framework.core.config import get_config


class VectorStore(BaseComponent):
    """
    Vector store for storing and retrieving document embeddings.

    Uses ChromaDB as the backend.
    """

    def __init__(
        self,
        collection_name: str = "default",
        persist_directory: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the vector store.

        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist data
            **kwargs: Additional configuration
        """
        super().__init__(name="VectorStore", **kwargs)

        config = get_config()
        self.collection_name = collection_name
        self.persist_directory = persist_directory or config.chroma_persist_directory
        self.client = None
        self.collection = None
        self._initialized = False

    def _initialize(self) -> None:
        """Initialize the ChromaDB client and collection."""
        # Skip if already initialized (performance optimization)
        if self._initialized:
            return

        # Create persist directory if it doesn't exist
        Path(self.persist_directory).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )

        self._initialized = True
        self.logger.info(f"Initialized VectorStore: {self.collection_name}")

    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> None:
        """
        Add documents to the vector store.

        Args:
            documents: List of document texts
            embeddings: List of embedding vectors
            metadatas: Optional metadata for each document
            ids: Optional IDs for documents (auto-generated if not provided)
        """
        self.initialize()

        if ids is None:
            ids = [f"doc_{i}" for i in range(len(documents))]

        if metadatas is None:
            metadatas = [{} for _ in range(len(documents))]

        self.collection.add(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )

        self.logger.info(f"Added {len(documents)} documents to {self.collection_name}")

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[float], List[Dict[str, Any]]]:
        """
        Search for similar documents.

        Args:
            query_embedding: Query embedding vector
            top_k: Number of results to return
            where: Optional metadata filters

        Returns:
            Tuple of (documents, distances, metadatas)
        """
        self.initialize()

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=where
        )

        documents = results["documents"][0] if results["documents"] else []
        distances = results["distances"][0] if results["distances"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []

        return documents, distances, metadatas

    def delete_collection(self) -> None:
        """Delete the collection."""
        self.initialize()
        self.client.delete_collection(name=self.collection_name)
        self.logger.info(f"Deleted collection: {self.collection_name}")

    def count(self) -> int:
        """Get the number of documents in the collection."""
        self.initialize()
        return self.collection.count()

    def get_all_documents(self) -> Dict[str, Any]:
        """Get all documents from the collection."""
        self.initialize()
        return self.collection.get()
