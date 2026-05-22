"""Retriever for RAG pipeline."""

import asyncio
from typing import List, Optional, Dict, Any, Tuple, Callable
from ai_automation_framework.core.base import BaseComponent
from ai_automation_framework.rag.embeddings import EmbeddingModel
from ai_automation_framework.rag.vector_store import VectorStore


class Retriever(BaseComponent):
    """
    Retriever for RAG (Retrieval-Augmented Generation).

    Combines embedding model and vector store for document retrieval.
    """

    def __init__(
        self,
        embedding_model: Optional[EmbeddingModel] = None,
        vector_store: Optional[VectorStore] = None,
        top_k: int = 5,
        **kwargs
    ):
        """
        Initialize the retriever.

        Args:
            embedding_model: Embedding model instance
            vector_store: Vector store instance
            top_k: Number of documents to retrieve
            **kwargs: Additional configuration
        """
        super().__init__(name="Retriever", **kwargs)

        self.embedding_model = embedding_model or EmbeddingModel()
        self.vector_store = vector_store or VectorStore()
        self.top_k = top_k

    def _initialize(self) -> None:
        """Initialize the retriever."""
        self.embedding_model.initialize()
        self.vector_store.initialize()
        self.logger.info("Initialized Retriever")

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        batch_size: int = 100,
        chunk_size: int = 1000,
        use_async: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        Add documents to the retriever with optimized batch processing.

        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional IDs for documents
            batch_size: Batch size for embedding API calls
            chunk_size: Chunk size for memory-efficient processing
            use_async: Whether to use async parallel processing (recommended for large datasets)
            progress_callback: Optional callback function(current, total) for progress updates
        """
        self.initialize()

        # Validate inputs
        if not documents:
            raise ValueError("Documents list cannot be empty")

        if metadatas is not None and len(metadatas) != len(documents):
            raise ValueError(f"Metadatas length ({len(metadatas)}) must match documents length ({len(documents)})")

        if ids is not None and len(ids) != len(documents):
            raise ValueError(f"IDs length ({len(ids)}) must match documents length ({len(documents)})")

        # Generate embeddings with batch processing
        self.logger.info(f"Generating embeddings for {len(documents)} documents")
        try:
            embeddings = self.embedding_model.embed_texts_batch(
                texts=documents,
                batch_size=batch_size,
                chunk_size=chunk_size,
                use_async=use_async,
                progress_callback=progress_callback
            )
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}") from e

        # Store in vector store
        try:
            self.vector_store.add_documents(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            self.logger.info(f"Successfully added {len(documents)} documents to vector store")
        except Exception as e:
            self.logger.error(f"Failed to add documents to vector store: {e}")
            raise RuntimeError(f"Failed to add documents to vector store: {e}") from e

    async def async_add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        batch_size: int = 100,
        max_concurrent: int = 5,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        Asynchronously add documents to the retriever with parallel batch processing.

        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional IDs for documents
            batch_size: Batch size for embedding API calls
            max_concurrent: Maximum number of concurrent API calls
            progress_callback: Optional callback function(current, total) for progress updates
        """
        self.initialize()

        # Validate inputs
        if not documents:
            raise ValueError("Documents list cannot be empty")

        if metadatas is not None and len(metadatas) != len(documents):
            raise ValueError(f"Metadatas length ({len(metadatas)}) must match documents length ({len(documents)})")

        if ids is not None and len(ids) != len(documents):
            raise ValueError(f"IDs length ({len(ids)}) must match documents length ({len(documents)})")

        # Generate embeddings with parallel batch processing
        self.logger.info(f"Generating embeddings for {len(documents)} documents (async)")
        try:
            embeddings = await self.embedding_model.async_embed_texts_parallel(
                texts=documents,
                batch_size=batch_size,
                max_concurrent=max_concurrent,
                progress_callback=progress_callback
            )
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}") from e

        # Store in vector store
        try:
            self.vector_store.add_documents(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            self.logger.info(f"Successfully added {len(documents)} documents to vector store")
        except Exception as e:
            self.logger.error(f"Failed to add documents to vector store: {e}")
            raise RuntimeError(f"Failed to add documents to vector store: {e}") from e

    async def async_add_documents_chunked(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        batch_size: int = 100,
        chunk_size: int = 1000,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> None:
        """
        Asynchronously add documents with memory-efficient chunked processing.

        This method processes large datasets in chunks to optimize memory usage.
        Each chunk is processed sequentially, but batches within a chunk are parallel.

        Args:
            documents: List of document texts
            metadatas: Optional metadata for each document
            ids: Optional IDs for documents
            batch_size: Batch size for embedding API calls
            chunk_size: Number of documents to process in each memory chunk
            progress_callback: Optional callback function(current, total) for progress updates
        """
        self.initialize()

        # Validate inputs
        if not documents:
            raise ValueError("Documents list cannot be empty")

        if metadatas is not None and len(metadatas) != len(documents):
            raise ValueError(f"Metadatas length ({len(metadatas)}) must match documents length ({len(documents)})")

        if ids is not None and len(ids) != len(documents):
            raise ValueError(f"IDs length ({len(ids)}) must match documents length ({len(documents)})")

        # Generate embeddings with chunked processing
        self.logger.info(f"Generating embeddings for {len(documents)} documents (async chunked)")
        try:
            embeddings = await self.embedding_model.async_embed_texts_chunked(
                texts=documents,
                batch_size=batch_size,
                chunk_size=chunk_size,
                progress_callback=progress_callback
            )
        except Exception as e:
            self.logger.error(f"Failed to generate embeddings: {e}")
            raise RuntimeError(f"Failed to generate embeddings: {e}") from e

        # Store in vector store
        try:
            self.vector_store.add_documents(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            self.logger.info(f"Successfully added {len(documents)} documents to vector store")
        except Exception as e:
            self.logger.error(f"Failed to add documents to vector store: {e}")
            raise RuntimeError(f"Failed to add documents to vector store: {e}") from e

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[str], List[float], List[Dict[str, Any]]]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Query text
            top_k: Number of documents to retrieve (overrides default)
            where: Optional metadata filters

        Returns:
            Tuple of (documents, distances, metadatas)
        """
        self.initialize()

        # Validate inputs
        if not query or not query.strip():
            raise ValueError("Query string cannot be empty")

        top_k = top_k or self.top_k
        if top_k <= 0:
            raise ValueError("top_k must be greater than 0")

        # Generate query embedding
        try:
            query_embedding = self.embedding_model.embed_query(query)
        except Exception as e:
            self.logger.error(f"Failed to generate query embedding: {e}")
            raise RuntimeError(f"Failed to generate query embedding: {e}") from e

        # Search vector store
        try:
            documents, distances, metadatas = self.vector_store.search(
                query_embedding=query_embedding,
                top_k=top_k,
                where=where
            )
        except Exception as e:
            self.logger.error(f"Failed to search vector store: {e}")
            raise RuntimeError(f"Failed to search vector store: {e}") from e

        self.logger.info(f"Retrieved {len(documents)} documents for query")
        return documents, distances, metadatas

    def retrieve_documents_only(
        self,
        query: str,
        top_k: Optional[int] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """
        Retrieve only the document texts (convenience method).

        Args:
            query: Query text
            top_k: Number of documents to retrieve
            where: Optional metadata filters

        Returns:
            List of document texts
        """
        documents, _, _ = self.retrieve(query, top_k, where)
        return documents

    def get_context_string(
        self,
        query: str,
        top_k: Optional[int] = None,
        separator: str = "\n\n---\n\n"
    ) -> str:
        """
        Get retrieved documents as a single context string.

        Args:
            query: Query text
            top_k: Number of documents to retrieve
            separator: Separator between documents

        Returns:
            Context string
        """
        documents = self.retrieve_documents_only(query, top_k)
        return separator.join(documents)
