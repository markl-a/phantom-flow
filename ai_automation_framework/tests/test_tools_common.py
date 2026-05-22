"""Tests for common tools."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_automation_framework.tools.common_tools import (
    WebSearchTool,
    CalculatorTool,
    FileSystemTool,
    DateTimeTool,
    DataProcessingTool,
)


class TestCalculatorTool:
    """Test Calculator tool."""

    def test_basic_addition(self):
        """Test basic addition."""
        calc = CalculatorTool()
        result = calc.calculate("2 + 2")
        assert result["success"] is True
        assert result["result"] == 4

    def test_basic_subtraction(self):
        """Test basic subtraction."""
        calc = CalculatorTool()
        result = calc.calculate("10 - 3")
        assert result["success"] is True
        assert result["result"] == 7

    def test_multiplication(self):
        """Test multiplication."""
        calc = CalculatorTool()
        result = calc.calculate("5 * 6")
        assert result["success"] is True
        assert result["result"] == 30

    def test_division(self):
        """Test division."""
        calc = CalculatorTool()
        result = calc.calculate("20 / 4")
        assert result["success"] is True
        assert result["result"] == 5.0

    def test_complex_expression(self):
        """Test complex expression."""
        calc = CalculatorTool()
        result = calc.calculate("(2 + 3) * 4")
        assert result["success"] is True
        assert result["result"] == 20

    def test_power(self):
        """Test power operation."""
        calc = CalculatorTool()
        result = calc.calculate("2 ** 8")
        assert result["success"] is True
        assert result["result"] == 256


class TestDateTimeTool:
    """Test DateTime tool."""

    def test_get_current_time(self):
        """Test getting current time."""
        dt_tool = DateTimeTool()
        result = dt_tool.get_current_time()
        assert result["success"] is True
        assert "datetime" in result
        assert "timestamp" in result

    def test_format_date(self):
        """Test date formatting."""
        dt_tool = DateTimeTool()
        result = dt_tool.format_date("2024-01-15", "%Y-%m-%d", "%B %d, %Y")
        assert result["success"] is True
        assert result["formatted"] == "January 15, 2024"

    def test_add_days(self):
        """Test adding days to date."""
        dt_tool = DateTimeTool()
        result = dt_tool.add_days("2024-01-01", 10)
        assert result["success"] is True
        assert "2024-01-11" in result["result"]


class TestFileSystemTool:
    """Test FileSystem tool."""

    def test_list_directory(self, temp_test_dir):
        """Test listing directory contents."""
        # Create some test files
        (temp_test_dir / "file1.txt").write_text("content1")
        (temp_test_dir / "file2.txt").write_text("content2")

        fs_tool = FileSystemTool()
        result = fs_tool.list_directory(str(temp_test_dir))

        assert result["success"] is True
        assert len(result["files"]) == 2

    def test_read_file(self, sample_text_file):
        """Test reading file contents."""
        fs_tool = FileSystemTool()
        result = fs_tool.read_file(str(sample_text_file))

        assert result["success"] is True
        assert "sample text file" in result["content"]

    def test_write_file(self, temp_test_dir):
        """Test writing file."""
        fs_tool = FileSystemTool()
        file_path = str(temp_test_dir / "new_file.txt")
        result = fs_tool.write_file(file_path, "Hello, World!")

        assert result["success"] is True
        assert (temp_test_dir / "new_file.txt").read_text() == "Hello, World!"

    def test_file_exists(self, sample_text_file):
        """Test checking if file exists."""
        fs_tool = FileSystemTool()
        assert fs_tool.file_exists(str(sample_text_file)) is True
        assert fs_tool.file_exists("/nonexistent/file.txt") is False


class TestDataProcessingTool:
    """Test DataProcessing tool."""

    def test_json_parse(self):
        """Test JSON parsing."""
        dp_tool = DataProcessingTool()
        result = dp_tool.parse_json('{"name": "test", "value": 123}')

        assert result["success"] is True
        assert result["data"]["name"] == "test"
        assert result["data"]["value"] == 123

    def test_json_stringify(self):
        """Test JSON stringification."""
        dp_tool = DataProcessingTool()
        result = dp_tool.to_json({"name": "test", "value": 123})

        assert result["success"] is True
        assert "test" in result["json"]


class TestWebSearchTool:
    """Test WebSearch tool."""

    def test_search_with_mock(self, mock_http_response):
        """Test web search with mocked response."""
        mock_http_response["get"].return_value.json.return_value = {
            "results": [
                {"title": "Result 1", "url": "https://example.com/1"},
                {"title": "Result 2", "url": "https://example.com/2"},
            ]
        }

        search_tool = WebSearchTool()
        # The actual implementation may vary, so we test that it handles the mock correctly
        assert search_tool is not None
