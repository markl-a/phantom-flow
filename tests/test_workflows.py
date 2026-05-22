"""Tests for the workflow modules (Chain and Pipeline)."""

import pytest
from unittest.mock import Mock, patch

from ai_automation_framework.workflows.chain import Chain
from ai_automation_framework.workflows.pipeline import Pipeline


class TestChain:
    """Tests for Chain class."""

    @patch('ai_automation_framework.core.base.get_logger')
    def test_chain_initialization(self, mock_logger):
        """Test chain initialization."""
        mock_logger.return_value = Mock()

        chain = Chain()

        assert chain.steps == []
        assert chain.name == "Chain"

    @patch('ai_automation_framework.core.base.get_logger')
    def test_chain_with_initial_steps(self, mock_logger):
        """Test chain initialization with steps."""
        mock_logger.return_value = Mock()

        def step1(x):
            return x + 1

        def step2(x):
            return x * 2

        chain = Chain(steps=[step1, step2])

        assert len(chain.steps) == 2

    @patch('ai_automation_framework.core.base.get_logger')
    def test_add_step(self, mock_logger):
        """Test adding a step to chain."""
        mock_logger.return_value = Mock()

        chain = Chain()

        def my_step(x):
            return x

        result = chain.add_step(my_step)

        assert len(chain.steps) == 1
        assert result is chain  # Should return self for chaining

    @patch('ai_automation_framework.core.base.get_logger')
    def test_add_non_callable_raises_error(self, mock_logger):
        """Test that adding non-callable raises TypeError."""
        mock_logger.return_value = Mock()

        chain = Chain()

        with pytest.raises(TypeError):
            chain.add_step("not a function")

    @patch('ai_automation_framework.core.base.get_logger')
    def test_run_single_step(self, mock_logger):
        """Test running chain with single step."""
        mock_logger.return_value = Mock()

        chain = Chain()
        chain.add_step(lambda x: x * 2)

        result = chain.run(5)

        assert result == 10

    @patch('ai_automation_framework.core.base.get_logger')
    def test_run_multiple_steps(self, mock_logger):
        """Test running chain with multiple steps."""
        mock_logger.return_value = Mock()

        chain = Chain()
        chain.add_step(lambda x: x + 1)  # 5 -> 6
        chain.add_step(lambda x: x * 2)  # 6 -> 12
        chain.add_step(lambda x: x - 4)  # 12 -> 8

        result = chain.run(5)

        assert result == 8

    @patch('ai_automation_framework.core.base.get_logger')
    def test_run_with_none_input_raises_error(self, mock_logger):
        """Test that None input raises ValueError."""
        mock_logger.return_value = Mock()

        chain = Chain()
        chain.add_step(lambda x: x)

        with pytest.raises(ValueError):
            chain.run(None)

    @patch('ai_automation_framework.core.base.get_logger')
    def test_run_empty_chain(self, mock_logger):
        """Test running empty chain returns input."""
        mock_logger.return_value = Mock()

        chain = Chain()
        result = chain.run("input")

        assert result == "input"

    @patch('ai_automation_framework.core.base.get_logger')
    def test_step_error_raises_runtime_error(self, mock_logger):
        """Test that step errors are wrapped in RuntimeError."""
        mock_logger.return_value = Mock()

        def failing_step(x):
            raise ValueError("Step failed")

        chain = Chain()
        chain.add_step(failing_step)

        with pytest.raises(RuntimeError) as exc_info:
            chain.run("input")

        assert "Step failed" in str(exc_info.value)

    @patch('ai_automation_framework.core.base.get_logger')
    def test_chain_callable(self, mock_logger):
        """Test chain is callable."""
        mock_logger.return_value = Mock()

        chain = Chain()
        chain.add_step(lambda x: x.upper())

        result = chain("hello")

        assert result == "HELLO"

    @patch('ai_automation_framework.core.base.get_logger')
    def test_chain_with_dict_data(self, mock_logger):
        """Test chain with dictionary data."""
        mock_logger.return_value = Mock()

        chain = Chain()
        chain.add_step(lambda d: {**d, "processed": True})
        chain.add_step(lambda d: {**d, "count": len(d)})

        result = chain.run({"name": "test"})

        assert result["name"] == "test"
        assert result["processed"] is True
        assert result["count"] == 2

    @patch('ai_automation_framework.core.base.get_logger')
    def test_chain_fluent_api(self, mock_logger):
        """Test chain fluent API for adding steps."""
        mock_logger.return_value = Mock()

        chain = Chain()
        chain.add_step(lambda x: x + 1).add_step(lambda x: x * 2).add_step(lambda x: x - 1)

        result = chain.run(5)

        assert result == 11  # (5+1)*2-1 = 11


class TestPipeline:
    """Tests for Pipeline class."""

    @patch('ai_automation_framework.core.base.get_logger')
    def test_pipeline_initialization(self, mock_logger):
        """Test pipeline initialization."""
        mock_logger.return_value = Mock()

        pipeline = Pipeline(name="TestPipeline")

        assert pipeline.name == "TestPipeline"
        assert pipeline.stages == {}
        assert pipeline.dependencies == {}

    @patch('ai_automation_framework.core.base.get_logger')
    def test_add_stage(self, mock_logger):
        """Test adding a stage to pipeline."""
        mock_logger.return_value = Mock()

        pipeline = Pipeline()

        def my_stage(data):
            return data

        result = pipeline.add_stage("stage1", my_stage)

        assert "stage1" in pipeline.stages
        assert result is pipeline  # Should return self

    @patch('ai_automation_framework.core.base.get_logger')
    def test_add_stage_with_dependencies(self, mock_logger):
        """Test adding a stage with dependencies."""
        mock_logger.return_value = Mock()

        pipeline = Pipeline()

        pipeline.add_stage("stage1", lambda d: d)
        pipeline.add_stage("stage2", lambda d: d, depends_on=["stage1"])

        assert pipeline.dependencies["stage2"] == ["stage1"]

    @patch('ai_automation_framework.core.base.get_logger')
    def test_execution_order_simple(self, mock_logger):
        """Test simple execution order."""
        mock_logger.return_value = Mock()

        pipeline = Pipeline()
        pipeline.add_stage("a", lambda d: d)
        pipeline.add_stage("b", lambda d: d, depends_on=["a"])
        pipeline.add_stage("c", lambda d: d, depends_on=["b"])

        order = pipeline._get_execution_order()

        # a should come before b, b before c
        assert order.index("a") < order.index("b")
        assert order.index("b") < order.index("c")

    @patch('ai_automation_framework.core.base.get_logger')
    def test_execution_order_parallel_stages(self, mock_logger):
        """Test execution order with parallel stages."""
        mock_logger.return_value = Mock()

        pipeline = Pipeline()
        pipeline.add_stage("a", lambda d: d)
        pipeline.add_stage("b", lambda d: d, depends_on=["a"])
        pipeline.add_stage("c", lambda d: d, depends_on=["a"])  # b and c are parallel
        pipeline.add_stage("d", lambda d: d, depends_on=["b", "c"])

        order = pipeline._get_execution_order()

        assert order.index("a") < order.index("b")
        assert order.index("a") < order.index("c")
        assert order.index("b") < order.index("d")
        assert order.index("c") < order.index("d")

    @patch('ai_automation_framework.core.base.get_logger')
    def test_circular_dependency_detection(self, mock_logger):
        """Test circular dependency detection."""
        mock_logger.return_value = Mock()

        pipeline = Pipeline()
        pipeline.add_stage("a", lambda d: d, depends_on=["b"])
        pipeline.add_stage("b", lambda d: d, depends_on=["a"])

        with pytest.raises(ValueError) as exc_info:
            pipeline._get_execution_order()

        assert "Circular dependency" in str(exc_info.value)

    @patch('ai_automation_framework.core.base.get_logger')
    def test_missing_dependency_detection(self, mock_logger):
        """Test missing dependency detection."""
        mock_logger.return_value = Mock()

        pipeline = Pipeline()
        pipeline.add_stage("a", lambda d: d, depends_on=["nonexistent"])

        with pytest.raises(ValueError) as exc_info:
            pipeline._get_execution_order()

        assert "not found" in str(exc_info.value)

    @patch('ai_automation_framework.core.base.get_logger')
    def test_run_simple_pipeline(self, mock_logger):
        """Test running a simple pipeline."""
        mock_logger.return_value = Mock()

        pipeline = Pipeline()

        def stage1(data):
            return {**data, "stage1": True}

        def stage2(data):
            return {**data, "stage2": True}

        pipeline.add_stage("stage1", stage1)
        pipeline.add_stage("stage2", stage2, depends_on=["stage1"])

        result = pipeline.run({"initial": True})

        assert result["stage1"]["stage1"] is True
        assert result["stage2"]["stage2"] is True

    @patch('ai_automation_framework.core.base.get_logger')
    def test_pipeline_no_stages(self, mock_logger):
        """Test running pipeline with no stages returns input-based result."""
        mock_logger.return_value = Mock()

        pipeline = Pipeline()
        result = pipeline.run({"test": True})

        # Pipeline stores input in results under 'input' key
        assert "input" in result or result == {}

    @patch('ai_automation_framework.core.base.get_logger')
    def test_pipeline_fluent_api(self, mock_logger):
        """Test pipeline fluent API."""
        mock_logger.return_value = Mock()

        pipeline = Pipeline()
        pipeline.add_stage("a", lambda d: d).add_stage("b", lambda d: d, depends_on=["a"])

        assert "a" in pipeline.stages
        assert "b" in pipeline.stages


class TestChainPipelineIntegration:
    """Integration tests combining Chain and Pipeline."""

    @pytest.mark.integration
    @patch('ai_automation_framework.core.base.get_logger')
    def test_chain_string_processing(self, mock_logger):
        """Test chain for string processing."""
        mock_logger.return_value = Mock()

        # Create a chain for text processing
        text_chain = Chain()
        text_chain.add_step(lambda x: x.lower())
        text_chain.add_step(lambda x: x.strip())
        text_chain.add_step(lambda x: x.replace(" ", "_"))

        result = text_chain("  Hello World  ")

        assert result == "hello_world"

    @pytest.mark.integration
    @patch('ai_automation_framework.core.base.get_logger')
    def test_chain_numeric_processing(self, mock_logger):
        """Test chain for numeric processing."""
        mock_logger.return_value = Mock()

        chain = Chain()
        chain.add_step(lambda x: x + 10)
        chain.add_step(lambda x: x * 2)
        chain.add_step(lambda x: x - 5)

        result = chain(5)

        # (5 + 10) * 2 - 5 = 25
        assert result == 25

    @pytest.mark.integration
    @patch('ai_automation_framework.core.base.get_logger')
    def test_pipeline_with_dependencies(self, mock_logger):
        """Test pipeline with stage dependencies."""
        mock_logger.return_value = Mock()

        pipeline = Pipeline()

        def stage_a(data):
            # data contains {"input": original_input, "results": previous_results}
            original_input = data.get("input", {})
            return {"value": original_input.get("number", 0) + 1}

        def stage_b(data):
            # Access previous stage results
            results = data.get("results", {})
            stage_a_result = results.get("stage_a", {})
            return {"value": stage_a_result.get("value", 0) * 2}

        pipeline.add_stage("stage_a", stage_a)
        pipeline.add_stage("stage_b", stage_b, depends_on=["stage_a"])

        result = pipeline.run({"number": 5})

        # stage_a: 5 + 1 = 6
        # stage_b: 6 * 2 = 12
        assert "stage_a" in result
        assert "stage_b" in result
        assert result["stage_a"]["value"] == 6
        assert result["stage_b"]["value"] == 12
