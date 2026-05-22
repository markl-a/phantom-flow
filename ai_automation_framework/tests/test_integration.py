"""Integration tests for AI Automation Framework."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os


@pytest.mark.integration
class TestLLMIntegration:
    """Integration tests for LLM clients."""

    def test_openai_client_workflow(self, mock_openai_client):
        """Test complete OpenAI client workflow."""
        from ai_automation_framework.llm import OpenAIClient
        from ai_automation_framework.core.base import Message

        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            client = OpenAIClient(api_key="test_key")

            # Create a conversation
            messages = [
                Message(role="system", content="You are a helpful assistant."),
                Message(role="user", content="Hello!"),
            ]

            # The client should be properly initialized
            assert client.api_key == "test_key"
            assert client.model is not None

    def test_anthropic_client_workflow(self, mock_anthropic_client):
        """Test complete Anthropic client workflow."""
        from ai_automation_framework.llm import AnthropicClient
        from ai_automation_framework.core.base import Message

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test_key"}):
            client = AnthropicClient(api_key="test_key")

            messages = [
                Message(role="user", content="Hello!"),
            ]

            assert client.api_key == "test_key"
            assert client.model is not None


@pytest.mark.integration
class TestAgentIntegration:
    """Integration tests for agent system."""

    def test_base_agent_conversation(self, mock_openai_client):
        """Test base agent conversation flow."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            from ai_automation_framework.agents import BaseAgent

            agent = BaseAgent(
                name="TestAgent",
                system_message="You are a test agent."
            )

            assert agent.name == "TestAgent"
            assert len(agent.memory) >= 1  # System message

    def test_tool_agent_with_tools(self, mock_openai_client):
        """Test tool agent with registered tools."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            from ai_automation_framework.agents import ToolAgent
            from ai_automation_framework.tools import CalculatorTool

            agent = ToolAgent(
                name="CalculatorAgent",
                system_message="You can help with calculations."
            )

            # Register a tool
            calc = CalculatorTool()
            agent.register_tool("calculate", calc.calculate)

            assert "calculate" in agent.tools


@pytest.mark.integration
class TestRAGIntegration:
    """Integration tests for RAG system."""

    def test_rag_pipeline(self, temp_test_dir):
        """Test complete RAG pipeline."""
        with patch("chromadb.Client") as mock_chroma:
            mock_collection = MagicMock()
            mock_client = MagicMock()
            mock_client.get_or_create_collection.return_value = mock_collection
            mock_chroma.return_value = mock_client

            from ai_automation_framework.rag import VectorStore

            # Create vector store
            store = VectorStore(collection_name="test_collection")
            assert store is not None

    def test_document_loading_pipeline(self, sample_text_file):
        """Test document loading and processing."""
        from ai_automation_framework.tools import TextLoader

        loader = TextLoader(str(sample_text_file))
        documents = loader.load()

        assert len(documents) > 0
        assert "sample text file" in documents[0].content.lower()


@pytest.mark.integration
class TestToolsIntegration:
    """Integration tests for tools working together."""

    def test_data_processing_pipeline(self, sample_csv_file, temp_test_dir):
        """Test data processing pipeline."""
        from ai_automation_framework.tools import CSVProcessingTool, DataAnalysisTool

        # Read CSV
        csv_result = CSVProcessingTool.read_csv(str(sample_csv_file))
        assert csv_result["success"] is True

        # Analyze data
        ages = [int(row["age"]) for row in csv_result["data"]]
        stats = DataAnalysisTool.calculate_statistics(ages)

        assert stats["success"] is True
        assert "mean" in stats

    def test_file_and_datetime_tools(self, temp_test_dir):
        """Test file operations with datetime."""
        from ai_automation_framework.tools import FileSystemTool, DateTimeTool

        fs = FileSystemTool()
        dt = DateTimeTool()

        # Get current time
        time_result = dt.get_current_time()
        assert time_result["success"] is True

        # Write file with timestamp
        timestamp = time_result["timestamp"]
        content = f"Created at: {timestamp}"
        file_path = str(temp_test_dir / "timestamped.txt")

        write_result = fs.write_file(file_path, content)
        assert write_result["success"] is True

        # Read back
        read_result = fs.read_file(file_path)
        assert read_result["success"] is True
        assert str(timestamp) in read_result["content"]


@pytest.mark.integration
class TestWorkflowIntegration:
    """Integration tests for workflow components."""

    def test_chain_workflow(self):
        """Test chain workflow execution."""
        from ai_automation_framework.workflows import Chain

        results = []

        def step1(data):
            results.append("step1")
            return {"value": data["value"] + 1}

        def step2(data):
            results.append("step2")
            return {"value": data["value"] * 2}

        chain = Chain([step1, step2])
        final = chain.run({"value": 5})

        assert results == ["step1", "step2"]
        assert final["value"] == 12  # (5+1)*2

    def test_pipeline_parallel_execution(self):
        """Test pipeline parallel execution."""
        from ai_automation_framework.workflows import Pipeline

        def task1(data):
            return {"result1": data["input"] + "_processed1"}

        def task2(data):
            return {"result2": data["input"] + "_processed2"}

        pipeline = Pipeline([task1, task2])
        results = pipeline.run({"input": "test"})

        assert "result1" in results or "result2" in results


@pytest.mark.integration
class TestEndToEndScenarios:
    """End-to-end scenario tests."""

    def test_document_qa_scenario(self, sample_text_file, mock_openai_client):
        """Test document Q&A scenario."""
        with patch.dict(os.environ, {"OPENAI_API_KEY": "test_key"}):
            from ai_automation_framework.tools import TextLoader
            from ai_automation_framework.llm import OpenAIClient

            # Load document
            loader = TextLoader(str(sample_text_file))
            docs = loader.load()

            # Initialize LLM
            client = OpenAIClient(api_key="test_key")

            assert len(docs) > 0
            assert client is not None

    def test_automation_scenario(self, temp_test_dir, mock_http_response):
        """Test automation scenario with multiple tools."""
        from ai_automation_framework.tools import (
            FileSystemTool,
            DateTimeTool,
            CalculatorTool,
        )

        # Initialize tools
        fs = FileSystemTool()
        dt = DateTimeTool()
        calc = CalculatorTool()

        # Get current time
        time_info = dt.get_current_time()
        assert time_info["success"] is True

        # Do some calculations
        calc_result = calc.calculate("100 * 1.1")
        assert calc_result["success"] is True

        # Write report
        report = f"""
        Automation Report
        Time: {time_info['datetime']}
        Calculation Result: {calc_result['result']}
        """

        write_result = fs.write_file(
            str(temp_test_dir / "report.txt"),
            report
        )
        assert write_result["success"] is True

        # Verify report exists
        assert fs.file_exists(str(temp_test_dir / "report.txt"))


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Performance-related integration tests."""

    def test_batch_processing(self, temp_test_dir):
        """Test batch file processing."""
        from ai_automation_framework.tools import FileSystemTool

        fs = FileSystemTool()

        # Create multiple files
        for i in range(10):
            fs.write_file(
                str(temp_test_dir / f"file_{i}.txt"),
                f"Content {i}"
            )

        # List and verify
        result = fs.list_directory(str(temp_test_dir))
        assert result["success"] is True
        assert len(result["files"]) == 10

    def test_concurrent_tool_usage(self):
        """Test concurrent tool usage."""
        import concurrent.futures
        from ai_automation_framework.tools import CalculatorTool, DateTimeTool

        calc = CalculatorTool()
        dt = DateTimeTool()

        def calc_task(expr):
            return calc.calculate(expr)

        def time_task():
            return dt.get_current_time()

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            calc_futures = [
                executor.submit(calc_task, f"{i} + {i}")
                for i in range(5)
            ]
            time_futures = [
                executor.submit(time_task)
                for _ in range(5)
            ]

            all_futures = calc_futures + time_futures
            results = [f.result() for f in all_futures]

            assert all(r["success"] for r in results)
