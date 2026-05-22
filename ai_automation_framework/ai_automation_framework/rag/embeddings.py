"""Embedding models for text vectorization."""

import asyncio
from typing import List, Optional, Callable, Any
from openai import OpenAI, AsyncOpenAI
from ai_automation_framework.core.base import BaseComponent
from ai_automation_framework.core.config import get_config


class EmbeddingModel(BaseComponent):
    """
    Embedding model for converting text to vectors.

    Supports OpenAI embeddings and can be extended for other providers.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize the embedding model.

        Args:
            model: Model name (default: from config)
            api_key: API key (default: from config)
            **kwargs: Additional configuration
        """
        super().__init__(name="EmbeddingModel", **kwargs)

        config = get_config()
        self.model = model or config.default_embedding_model
        self.api_key = api_key or config.openai_api_key
        self.client = None
        self.async_client = None

    def _initialize(self) -> None:
        """Initialize the embedding client."""
        try:
            self.client = OpenAI(api_key=self.api_key)
            self.async_client = AsyncOpenAI(api_key=self.api_key)
            self.logger.info(f"Initialized EmbeddingModel with {self.model}")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
            raise RuntimeError(f"Failed to initialize OpenAI client: {e}") from e

    def embed_text(self, text: str) -> List[float]:
        """
        Embed a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        self.initialize()

        # Validate input
        if not text or not text.strip():
            raise ValueError("Text parameter cannot be empty")

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            self.logger.error(f"Failed to embed text: {e}")
            raise RuntimeError(f"Failed to embed text: {e}") from e

    def embed_texts(
        self,
        texts: List[str],
        batch_size: int = 100,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[List[float]]:
        """
        Embed multiple texts in batches.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            progress_callback: Optional callback function(current, total) for progress updates

        Returns:
            List of embedding vectors
        """
        self.initialize()

        # Validate inputs
        if not texts:
            raise ValueError("Texts parameter cannot be empty")
        if batch_size <= 0:
            raise ValueError("Batch size must be greater than 0")

        all_embeddings = []
        total_batches = (len(texts) + batch_size - 1) // batch_size

        try:
            for batch_idx, i in enumerate(range(0, len(texts), batch_size), 1):
                batch = texts[i:i + batch_size]
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                embeddings = [data.embedding for data in response.data]
                all_embeddings.extend(embeddings)

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(batch_idx, total_batches)

            return all_embeddings
        except Exception as e:
            self.logger.error(f"Failed to embed texts: {e}")
            raise RuntimeError(f"Failed to embed texts: {e}") from e

    async def async_embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Asynchronously embed a single batch of texts.

        Args:
            texts: List of texts to embed (should be pre-batched)

        Returns:
            List of embedding vectors
        """
        if not self.async_client:
            raise RuntimeError("Async client not initialized. Call initialize() first.")

        try:
            response = await self.async_client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            self.logger.error(f"Failed to embed batch: {e}")
            raise RuntimeError(f"Failed to embed batch: {e}") from e

    async def async_embed_texts_parallel(
        self,
        texts: List[str],
        batch_size: int = 100,
        max_concurrent: int = 5,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[List[float]]:
        """
        Asynchronously embed multiple texts with parallel batch processing.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for processing
            max_concurrent: Maximum number of concurrent API calls
            progress_callback: Optional callback function(current, total) for progress updates

        Returns:
            List of embedding vectors
        """
        self.initialize()

        # Validate inputs
        if not texts:
            raise ValueError("Texts parameter cannot be empty")
        if batch_size <= 0:
            raise ValueError("Batch size must be greater than 0")
        if max_concurrent <= 0:
            raise ValueError("max_concurrent must be greater than 0")

        # Create batches
        batches = [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]
        total_batches = len(batches)
        all_embeddings = []
        completed_batches = 0

        try:
            # Process batches with concurrency control
            for i in range(0, len(batches), max_concurrent):
                chunk = batches[i:i + max_concurrent]

                # Process chunk in parallel
                results = await asyncio.gather(*[self.async_embed_batch(batch) for batch in chunk])

                # Flatten results
                for batch_embeddings in results:
                    all_embeddings.extend(batch_embeddings)
                    completed_batches += 1

                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(completed_batches, total_batches)

            return all_embeddings
        except Exception as e:
            self.logger.error(f"Failed to embed texts in parallel: {e}")
            raise RuntimeError(f"Failed to embed texts in parallel: {e}") from e

    async def async_embed_texts_chunked(
        self,
        texts: List[str],
        batch_size: int = 100,
        chunk_size: int = 1000,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[List[float]]:
        """
        Asynchronously embed texts with memory-efficient chunked processing.

        This method processes large datasets in chunks to optimize memory usage.
        Each chunk is processed sequentially, but batches within a chunk are parallel.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for API calls
            chunk_size: Number of texts to process in each memory chunk
            progress_callback: Optional callback function(current, total) for progress updates

        Returns:
            List of embedding vectors
        """
        self.initialize()

        # Validate inputs
        if not texts:
            raise ValueError("Texts parameter cannot be empty")
        if batch_size <= 0:
            raise ValueError("Batch size must be greater than 0")
        if chunk_size <= 0:
            raise ValueError("Chunk size must be greater than 0")

        all_embeddings = []
        total_texts = len(texts)
        processed_texts = 0

        try:
            # Process in chunks for memory efficiency
            for chunk_start in range(0, len(texts), chunk_size):
                chunk_end = min(chunk_start + chunk_size, len(texts))
                chunk = texts[chunk_start:chunk_end]

                # Process chunk with parallel batches
                chunk_embeddings = await self.async_embed_texts_parallel(
                    texts=chunk,
                    batch_size=batch_size,
                    max_concurrent=5,
                    progress_callback=None  # We'll handle progress at chunk level
                )

                all_embeddings.extend(chunk_embeddings)
                processed_texts += len(chunk)

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(processed_texts, total_texts)

                # Log progress
                self.logger.info(
                    f"Processed {processed_texts}/{total_texts} texts "
                    f"({processed_texts / total_texts * 100:.1f}%)"
                )

            return all_embeddings
        except Exception as e:
            self.logger.error(f"Failed to embed texts in chunks: {e}")
            raise RuntimeError(f"Failed to embed texts in chunks: {e}") from e

    def embed_texts_batch(
        self,
        texts: List[str],
        batch_size: int = 100,
        chunk_size: int = 1000,
        use_async: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[List[float]]:
        """
        Embed texts with optimized batch processing.

        This is a high-level convenience method that automatically chooses
        the best processing strategy based on dataset size.

        Args:
            texts: List of texts to embed
            batch_size: Batch size for API calls
            chunk_size: Chunk size for memory-efficient processing
            use_async: Whether to use async parallel processing (recommended for large datasets)
            progress_callback: Optional callback function(current, total) for progress updates

        Returns:
            List of embedding vectors
        """
        self.initialize()

        if not texts:
            raise ValueError("Texts parameter cannot be empty")

        # For small datasets, use simple sync processing
        if len(texts) <= batch_size:
            return self.embed_texts(texts, batch_size, progress_callback)

        # For larger datasets, use async processing if enabled
        if use_async:
            try:
                # Use asyncio.run if not already in an event loop
                try:
                    loop = asyncio.get_running_loop()
                    # We're already in an async context
                    raise RuntimeError(
                        "Cannot use embed_texts_batch with use_async=True from within "
                        "an async context. Use async_embed_texts_chunked directly instead."
                    )
                except RuntimeError:
                    # No running loop, we can create one
                    return asyncio.run(
                        self.async_embed_texts_chunked(
                            texts=texts,
                            batch_size=batch_size,
                            chunk_size=chunk_size,
                            progress_callback=progress_callback
                        )
                    )
            except Exception as e:
                self.logger.warning(f"Async processing failed, falling back to sync: {e}")
                return self.embed_texts(texts, batch_size, progress_callback)
        else:
            # Use synchronous batch processing
            return self.embed_texts(texts, batch_size, progress_callback)

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        """
        Embed documents (convenience method).

        Args:
            documents: List of documents

        Returns:
            List of embedding vectors
        """
        return self.embed_texts(documents)

    def embed_query(self, query: str) -> List[float]:
        """
        Embed a query (convenience method).

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        return self.embed_text(query)
