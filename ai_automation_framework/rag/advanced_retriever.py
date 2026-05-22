"""
Advanced Retriever with HyDE, MultiQuery, and Reranking support.

This module provides enhanced retrieval techniques for improved RAG performance:
- HyDE (Hypothetical Document Embeddings): Generate hypothetical answers to improve retrieval
- MultiQuery: Generate multiple query variations for better coverage
- Reranking: Re-score retrieved documents using cross-encoder models
- Contextual Compression: Compress retrieved content to most relevant parts
"""

import asyncio
from typing import List, Optional, Dict, Any, Tuple, Callable, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from ai_automation_framework.core.base import BaseComponent
from ai_automation_framework.rag.retriever import Retriever
from ai_automation_framework.rag.embeddings import EmbeddingModel
from ai_automation_framework.rag.vector_store import VectorStore


@dataclass
class RetrievalResult:
    """Container for retrieval results with scores."""
    document: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    original_score: Optional[float] = None  # Score before reranking


class BaseReranker(ABC):
    """Abstract base class for rerankers."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """
        Rerank documents based on relevance to query.

        Args:
            query: The query string
            documents: List of documents to rerank
            top_k: Number of top documents to return

        Returns:
            List of (document, score) tuples sorted by relevance
        """
        pass

    @abstractmethod
    async def arerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """Async version of rerank."""
        pass


class CrossEncoderReranker(BaseReranker):
    """
    Reranker using cross-encoder models.

    Cross-encoders process query-document pairs together, providing
    more accurate relevance scores than bi-encoders.

    Supported models:
    - cross-encoder/ms-marco-MiniLM-L-6-v2 (fast, good quality)
    - cross-encoder/ms-marco-MiniLM-L-12-v2 (balanced)
    - BAAI/bge-reranker-v2-m3 (multilingual, high quality)
    - BAAI/bge-reranker-large (high quality)
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device: Optional[str] = None,
        batch_size: int = 32
    ):
        """
        Initialize cross-encoder reranker.

        Args:
            model_name: Name of the cross-encoder model
            device: Device to use (cuda, cpu, or None for auto)
            batch_size: Batch size for processing
        """
        self.model_name = model_name
        self.device = device
        self.batch_size = batch_size
        self._model = None

    def _load_model(self):
        """Lazy load the cross-encoder model."""
        if self._model is None:
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(
                    self.model_name,
                    device=self.device
                )
            except ImportError:
                raise ImportError(
                    "sentence-transformers is required for CrossEncoderReranker. "
                    "Install it with: pip install sentence-transformers"
                )
        return self._model

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """
        Rerank documents using cross-encoder.

        Args:
            query: Query string
            documents: List of documents
            top_k: Number of top results to return

        Returns:
            List of (document, score) tuples
        """
        if not documents:
            return []

        model = self._load_model()

        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Get scores
        scores = model.predict(pairs, batch_size=self.batch_size)

        # Combine with documents and sort
        doc_scores = list(zip(documents, scores))
        doc_scores.sort(key=lambda x: x[1], reverse=True)

        if top_k:
            doc_scores = doc_scores[:top_k]

        return doc_scores

    async def arerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """Async version of rerank (runs in executor)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.rerank, query, documents, top_k
        )


class CohereReranker(BaseReranker):
    """
    Reranker using Cohere's rerank API.

    Requires a Cohere API key.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "rerank-english-v3.0",
        top_n: int = 10
    ):
        """
        Initialize Cohere reranker.

        Args:
            api_key: Cohere API key (default: from environment)
            model: Rerank model name
            top_n: Default number of results to return
        """
        import os
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        self.model = model
        self.top_n = top_n
        self._client = None

    def _get_client(self):
        """Get or create Cohere client."""
        if self._client is None:
            try:
                import cohere
                self._client = cohere.Client(self.api_key)
            except ImportError:
                raise ImportError(
                    "cohere package is required for CohereReranker. "
                    "Install it with: pip install cohere"
                )
        return self._client

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """Rerank using Cohere API."""
        if not documents:
            return []

        client = self._get_client()
        top_n = top_k or self.top_n

        response = client.rerank(
            model=self.model,
            query=query,
            documents=documents,
            top_n=min(top_n, len(documents))
        )

        results = []
        for result in response.results:
            doc = documents[result.index]
            results.append((doc, result.relevance_score))

        return results

    async def arerank(
        self,
        query: str,
        documents: List[str],
        top_k: Optional[int] = None
    ) -> List[Tuple[str, float]]:
        """Async version using executor."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.rerank, query, documents, top_k
        )


class AdvancedRetriever(BaseComponent):
    """
    Advanced Retriever with HyDE, MultiQuery, and Reranking support.

    Features:
    - HyDE (Hypothetical Document Embeddings): Use LLM to generate
      hypothetical answers, then use those for retrieval
    - MultiQuery: Generate multiple query variations for better coverage
    - Reranking: Re-score retrieved documents with cross-encoders
    - Fusion: Combine results from multiple retrieval strategies

    Example:
        >>> from ai_automation_framework.rag import AdvancedRetriever
        >>> from ai_automation_framework.llm import OpenAIClient
        >>>
        >>> retriever = AdvancedRetriever(
        ...     llm_client=OpenAIClient(),
        ...     use_hyde=True,
        ...     use_reranking=True
        ... )
        >>> retriever.add_documents(["doc1", "doc2", "doc3"])
        >>> results = retriever.retrieve("What is machine learning?")
    """

    # Default prompts
    HYDE_PROMPT = """Given the following question, write a short passage that would answer it.
The passage should be factual and informative.

Question: {query}

Passage:"""

    MULTIQUERY_PROMPT = """You are an AI assistant that generates alternative versions of a search query.
Generate {n_queries} different versions of the following query to help retrieve relevant documents.
Each version should capture a different aspect or phrasing of the original question.

Original query: {query}

Alternative queries (one per line):"""

    def __init__(
        self,
        base_retriever: Optional[Retriever] = None,
        embedding_model: Optional[EmbeddingModel] = None,
        vector_store: Optional[VectorStore] = None,
        llm_client: Optional[Any] = None,
        reranker: Optional[BaseReranker] = None,
        use_hyde: bool = False,
        use_multiquery: bool = False,
        use_reranking: bool = False,
        top_k: int = 5,
        initial_k: int = 20,
        n_queries: int = 3,
        hyde_prompt: Optional[str] = None,
        multiquery_prompt: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize Advanced Retriever.

        Args:
            base_retriever: Base retriever instance (or creates one)
            embedding_model: Embedding model for retrieval
            vector_store: Vector store for documents
            llm_client: LLM client for HyDE and MultiQuery
            reranker: Reranker instance (or creates default if use_reranking=True)
            use_hyde: Enable HyDE retrieval
            use_multiquery: Enable MultiQuery retrieval
            use_reranking: Enable reranking of results
            top_k: Final number of documents to return
            initial_k: Initial retrieval count before reranking
            n_queries: Number of query variations for MultiQuery
            hyde_prompt: Custom HyDE prompt template
            multiquery_prompt: Custom MultiQuery prompt template
        """
        super().__init__(name="AdvancedRetriever", **kwargs)

        # Initialize base retriever
        if base_retriever:
            self.base_retriever = base_retriever
        else:
            self.base_retriever = Retriever(
                embedding_model=embedding_model,
                vector_store=vector_store,
                top_k=initial_k
            )

        self.llm_client = llm_client
        self.use_hyde = use_hyde
        self.use_multiquery = use_multiquery
        self.use_reranking = use_reranking
        self.top_k = top_k
        self.initial_k = initial_k
        self.n_queries = n_queries
        self.hyde_prompt = hyde_prompt or self.HYDE_PROMPT
        self.multiquery_prompt = multiquery_prompt or self.MULTIQUERY_PROMPT

        # Initialize reranker
        if use_reranking:
            self.reranker = reranker or CrossEncoderReranker()
        else:
            self.reranker = reranker

    def _initialize(self) -> None:
        """Initialize the retriever."""
        self.base_retriever.initialize()

        if (self.use_hyde or self.use_multiquery) and not self.llm_client:
            raise ValueError(
                "LLM client is required for HyDE or MultiQuery retrieval. "
                "Please provide an llm_client parameter."
            )

        self.logger.info(
            f"Initialized AdvancedRetriever (hyde={self.use_hyde}, "
            f"multiquery={self.use_multiquery}, reranking={self.use_reranking})"
        )

    def add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        """Add documents to the retriever."""
        self.initialize()
        self.base_retriever.add_documents(documents, metadatas, ids, **kwargs)

    async def async_add_documents(
        self,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
        **kwargs
    ) -> None:
        """Async add documents."""
        self.initialize()
        await self.base_retriever.async_add_documents(documents, metadatas, ids, **kwargs)

    def _generate_hyde_document(self, query: str) -> str:
        """
        Generate a hypothetical document using HyDE technique.

        HyDE works by:
        1. Using LLM to generate a hypothetical answer to the query
        2. Using that answer for embedding-based retrieval
        3. The hypothesis captures semantic meaning better than the question

        Args:
            query: Original query

        Returns:
            Hypothetical document text
        """
        from ai_automation_framework.core.base import Message

        prompt = self.hyde_prompt.format(query=query)
        messages = [Message(role="user", content=prompt)]

        response = self.llm_client.chat(messages)
        return response.content

    async def _agenerate_hyde_document(self, query: str) -> str:
        """Async version of HyDE generation."""
        from ai_automation_framework.core.base import Message

        prompt = self.hyde_prompt.format(query=query)
        messages = [Message(role="user", content=prompt)]

        response = await self.llm_client.achat(messages)
        return response.content

    def _generate_multi_queries(self, query: str) -> List[str]:
        """
        Generate multiple query variations.

        MultiQuery works by:
        1. Using LLM to generate alternative phrasings of the query
        2. Retrieving documents for each variation
        3. Combining and deduplicating results

        Args:
            query: Original query

        Returns:
            List of query variations including original
        """
        from ai_automation_framework.core.base import Message

        prompt = self.multiquery_prompt.format(query=query, n_queries=self.n_queries)
        messages = [Message(role="user", content=prompt)]

        response = self.llm_client.chat(messages)

        # Parse queries from response
        queries = [query]  # Include original
        for line in response.content.strip().split('\n'):
            line = line.strip()
            # Remove numbering if present
            if line and line[0].isdigit():
                line = line.lstrip('0123456789.-) ').strip()
            if line and line not in queries:
                queries.append(line)

        return queries[:self.n_queries + 1]

    async def _agenerate_multi_queries(self, query: str) -> List[str]:
        """Async version of multi-query generation."""
        from ai_automation_framework.core.base import Message

        prompt = self.multiquery_prompt.format(query=query, n_queries=self.n_queries)
        messages = [Message(role="user", content=prompt)]

        response = await self.llm_client.achat(messages)

        queries = [query]
        for line in response.content.strip().split('\n'):
            line = line.strip()
            if line and line[0].isdigit():
                line = line.lstrip('0123456789.-) ').strip()
            if line and line not in queries:
                queries.append(line)

        return queries[:self.n_queries + 1]

    def _reciprocal_rank_fusion(
        self,
        result_lists: List[List[Tuple[str, float]]],
        k: int = 60
    ) -> List[Tuple[str, float]]:
        """
        Combine results using Reciprocal Rank Fusion (RRF).

        RRF is a robust method for combining ranked lists that:
        - Doesn't require score normalization
        - Handles varying score scales
        - Gives diminishing returns for lower ranks

        Args:
            result_lists: List of result lists, each containing (doc, score) tuples
            k: RRF constant (default 60, as in original paper)

        Returns:
            Combined and re-ranked results
        """
        doc_scores: Dict[str, float] = {}

        for results in result_lists:
            for rank, (doc, _) in enumerate(results, 1):
                if doc not in doc_scores:
                    doc_scores[doc] = 0.0
                doc_scores[doc] += 1.0 / (k + rank)

        # Sort by combined score
        combined = sorted(doc_scores.items(), key=lambda x: x[1], reverse=True)
        return combined

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        where: Optional[Dict[str, Any]] = None,
        return_scores: bool = False
    ) -> Union[List[str], List[RetrievalResult]]:
        """
        Retrieve documents using advanced techniques.

        Args:
            query: Query string
            top_k: Number of documents to return
            where: Metadata filters
            return_scores: If True, return RetrievalResult objects with scores

        Returns:
            List of documents or RetrievalResult objects
        """
        self.initialize()

        top_k = top_k or self.top_k
        results: List[Tuple[str, float]] = []

        # Strategy 1: HyDE
        if self.use_hyde:
            self.logger.debug("Generating HyDE document...")
            hyde_doc = self._generate_hyde_document(query)

            # Retrieve using hypothetical document
            docs, distances, metas = self.base_retriever.retrieve(
                hyde_doc, self.initial_k, where
            )
            results.extend(list(zip(docs, [1.0 / (d + 1) for d in distances])))

        # Strategy 2: MultiQuery
        if self.use_multiquery:
            self.logger.debug("Generating multi-queries...")
            queries = self._generate_multi_queries(query)

            all_results = []
            for q in queries:
                docs, distances, metas = self.base_retriever.retrieve(
                    q, self.initial_k, where
                )
                all_results.append(list(zip(docs, [1.0 / (d + 1) for d in distances])))

            # Fuse results using RRF
            fused = self._reciprocal_rank_fusion(all_results)
            results.extend(fused)

        # Strategy 3: Standard retrieval (if no advanced techniques or as baseline)
        if not self.use_hyde and not self.use_multiquery:
            docs, distances, metas = self.base_retriever.retrieve(
                query, self.initial_k, where
            )
            results = list(zip(docs, [1.0 / (d + 1) for d in distances]))

        # Deduplicate
        seen = set()
        unique_results = []
        for doc, score in results:
            if doc not in seen:
                seen.add(doc)
                unique_results.append((doc, score))

        # Reranking
        if self.use_reranking and self.reranker and unique_results:
            self.logger.debug("Reranking results...")
            docs_to_rerank = [doc for doc, _ in unique_results[:self.initial_k]]
            reranked = self.reranker.rerank(query, docs_to_rerank, top_k)
            unique_results = reranked

        # Limit to top_k
        final_results = unique_results[:top_k]

        if return_scores:
            return [
                RetrievalResult(document=doc, score=score)
                for doc, score in final_results
            ]
        else:
            return [doc for doc, _ in final_results]

    async def aretrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        where: Optional[Dict[str, Any]] = None,
        return_scores: bool = False
    ) -> Union[List[str], List[RetrievalResult]]:
        """Async version of retrieve."""
        self.initialize()

        top_k = top_k or self.top_k
        results: List[Tuple[str, float]] = []

        # Strategy 1: HyDE
        if self.use_hyde:
            self.logger.debug("Generating HyDE document (async)...")
            hyde_doc = await self._agenerate_hyde_document(query)

            docs, distances, metas = self.base_retriever.retrieve(
                hyde_doc, self.initial_k, where
            )
            results.extend(list(zip(docs, [1.0 / (d + 1) for d in distances])))

        # Strategy 2: MultiQuery
        if self.use_multiquery:
            self.logger.debug("Generating multi-queries (async)...")
            queries = await self._agenerate_multi_queries(query)

            all_results = []
            for q in queries:
                docs, distances, metas = self.base_retriever.retrieve(
                    q, self.initial_k, where
                )
                all_results.append(list(zip(docs, [1.0 / (d + 1) for d in distances])))

            fused = self._reciprocal_rank_fusion(all_results)
            results.extend(fused)

        if not self.use_hyde and not self.use_multiquery:
            docs, distances, metas = self.base_retriever.retrieve(
                query, self.initial_k, where
            )
            results = list(zip(docs, [1.0 / (d + 1) for d in distances]))

        # Deduplicate
        seen = set()
        unique_results = []
        for doc, score in results:
            if doc not in seen:
                seen.add(doc)
                unique_results.append((doc, score))

        # Reranking
        if self.use_reranking and self.reranker and unique_results:
            self.logger.debug("Reranking results (async)...")
            docs_to_rerank = [doc for doc, _ in unique_results[:self.initial_k]]
            reranked = await self.reranker.arerank(query, docs_to_rerank, top_k)
            unique_results = reranked

        final_results = unique_results[:top_k]

        if return_scores:
            return [
                RetrievalResult(document=doc, score=score)
                for doc, score in final_results
            ]
        else:
            return [doc for doc, _ in final_results]

    def get_context_string(
        self,
        query: str,
        top_k: Optional[int] = None,
        separator: str = "\n\n---\n\n"
    ) -> str:
        """Get retrieved documents as a single context string."""
        documents = self.retrieve(query, top_k)
        return separator.join(documents)

    async def aget_context_string(
        self,
        query: str,
        top_k: Optional[int] = None,
        separator: str = "\n\n---\n\n"
    ) -> str:
        """Async version of get_context_string."""
        documents = await self.aretrieve(query, top_k)
        return separator.join(documents)


class HyDERetriever(AdvancedRetriever):
    """
    Convenience class for HyDE-only retrieval.

    HyDE (Hypothetical Document Embeddings) improves retrieval by:
    1. Using an LLM to generate a hypothetical answer to the query
    2. Embedding the hypothetical answer instead of the query
    3. Finding documents similar to the hypothetical answer

    This works because:
    - Questions and answers have different semantic structures
    - Answers are closer in embedding space to relevant documents
    - The LLM can generate relevant context even without seeing documents
    """

    def __init__(self, llm_client: Any, **kwargs):
        kwargs['use_hyde'] = True
        kwargs['use_multiquery'] = False
        kwargs['llm_client'] = llm_client
        super().__init__(**kwargs)


class MultiQueryRetriever(AdvancedRetriever):
    """
    Convenience class for MultiQuery-only retrieval.

    MultiQuery improves retrieval by:
    1. Generating multiple variations of the user's query
    2. Retrieving documents for each variation
    3. Combining results using Reciprocal Rank Fusion
    """

    def __init__(self, llm_client: Any, n_queries: int = 3, **kwargs):
        kwargs['use_hyde'] = False
        kwargs['use_multiquery'] = True
        kwargs['llm_client'] = llm_client
        kwargs['n_queries'] = n_queries
        super().__init__(**kwargs)


class RerankedRetriever(AdvancedRetriever):
    """
    Convenience class for retrieval with reranking.

    Reranking improves precision by:
    1. Retrieving a larger set of candidate documents
    2. Using a cross-encoder to score query-document pairs
    3. Returning the top-k highest-scoring documents
    """

    def __init__(
        self,
        reranker: Optional[BaseReranker] = None,
        initial_k: int = 20,
        **kwargs
    ):
        kwargs['use_hyde'] = False
        kwargs['use_multiquery'] = False
        kwargs['use_reranking'] = True
        kwargs['reranker'] = reranker
        kwargs['initial_k'] = initial_k
        super().__init__(**kwargs)
