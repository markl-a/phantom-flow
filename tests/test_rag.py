"""Tests for RAG components."""

import pytest
from unittest.mock import Mock, patch
from ai_automation_framework.rag import EmbeddingModel, VectorStore, Retriever


class TestEmbeddingModel:
    """Test embedding model."""

    @patch('ai_automation_framework.rag.embeddings.OpenAI')
    def test_embed_text(self, mock_openai):
        """Test embedding a single text."""
        # Mock the OpenAI response
        mock_response = Mock()
        mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3])]
        mock_openai.return_value.embeddings.create.return_value = mock_response

        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test_key'}):
            model = EmbeddingModel(api_key="test_key")
            model.initialize()

            embedding = model.embed_text("test text")
            assert embedding == [0.1, 0.2, 0.3]


class TestVectorStore:
    """Test vector store."""

    def test_vector_store_initialization(self):
        """Test vector store initialization."""
        store = VectorStore(collection_name="test")
        assert store.collection_name == "test"


class TestRetriever:
    """Test retriever."""

    def test_retriever_initialization(self):
        """Test retriever initialization."""
        retriever = Retriever(top_k=5)
        assert retriever.top_k == 5
