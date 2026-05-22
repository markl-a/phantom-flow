"""RAG (Retrieval-Augmented Generation) components."""

from ai_automation_framework.rag.embeddings import EmbeddingModel
from ai_automation_framework.rag.vector_store import VectorStore
from ai_automation_framework.rag.retriever import Retriever
from ai_automation_framework.rag.advanced_retriever import (
    AdvancedRetriever,
    HyDERetriever,
    MultiQueryRetriever,
    RerankedRetriever,
    BaseReranker,
    CrossEncoderReranker,
    CohereReranker,
    RetrievalResult,
)

__all__ = [
    # Basic components
    "EmbeddingModel",
    "VectorStore",
    "Retriever",
    # Advanced retrievers
    "AdvancedRetriever",
    "HyDERetriever",
    "MultiQueryRetriever",
    "RerankedRetriever",
    # Rerankers
    "BaseReranker",
    "CrossEncoderReranker",
    "CohereReranker",
    # Data classes
    "RetrievalResult",
]
