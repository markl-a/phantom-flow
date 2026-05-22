"""Tests for data processing tools."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestExcelAutomationTool:
    """Test Excel automation tool."""

    def test_read_excel_mock(self, temp_test_dir):
        """Test reading Excel file with mock."""
        with patch("pandas.read_excel") as mock_read:
            mock_df = MagicMock()
            mock_df.__len__ = Mock(return_value=5)
            mock_df.columns = ["name", "age", "city"]
            mock_df.to_dict.return_value = [
                {"name": "Alice", "age": 30, "city": "NYC"},
            ]
            mock_df.head.return_value = mock_df
            mock_read.return_value = mock_df

            from ai_automation_framework.tools.data_processing import ExcelAutomationTool

            result = ExcelAutomationTool.read_excel(str(temp_test_dir / "test.xlsx"))

            assert result["success"] is True
            assert result["rows"] == 5
            assert "name" in result["columns"]

    def test_write_excel_mock(self, temp_test_dir):
        """Test writing Excel file with mock."""
        with patch("pandas.DataFrame") as mock_df_class, \
             patch("pandas.ExcelWriter") as mock_writer:
            mock_df = MagicMock()
            mock_df_class.return_value = mock_df

            mock_writer_instance = MagicMock()
            mock_writer.return_value.__enter__ = Mock(return_value=mock_writer_instance)
            mock_writer.return_value.__exit__ = Mock(return_value=None)
            mock_writer_instance.sheets = {"Sheet1": MagicMock()}

            from ai_automation_framework.tools.data_processing import ExcelAutomationTool

            data = [{"name": "Alice", "age": 30}]
            result = ExcelAutomationTool.write_excel(
                str(temp_test_dir / "output.xlsx"),
                data
            )

            assert result["success"] is True


class TestCSVProcessingTool:
    """Test CSV processing tool."""

    def test_read_csv(self, sample_csv_file):
        """Test reading CSV file."""
        from ai_automation_framework.tools.data_processing import CSVProcessingTool

        result = CSVProcessingTool.read_csv(str(sample_csv_file))

        assert result["success"] is True
        assert result["rows"] == 2
        assert "name" in result["columns"]

    def test_write_csv(self, temp_test_dir):
        """Test writing CSV file."""
        from ai_automation_framework.tools.data_processing import CSVProcessingTool

        data = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25},
        ]
        output_path = str(temp_test_dir / "output.csv")

        result = CSVProcessingTool.write_csv(output_path, data)

        assert result["success"] is True
        assert (temp_test_dir / "output.csv").exists()

    def test_filter_csv(self, sample_csv_file):
        """Test filtering CSV data."""
        from ai_automation_framework.tools.data_processing import CSVProcessingTool

        result = CSVProcessingTool.filter_csv(
            str(sample_csv_file),
            column="age",
            value="30"
        )

        assert result["success"] is True


class TestDataAnalysisTool:
    """Test data analysis tool."""

    def test_basic_statistics(self):
        """Test basic statistics calculation."""
        from ai_automation_framework.tools.data_processing import DataAnalysisTool

        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        result = DataAnalysisTool.calculate_statistics(data)

        assert result["success"] is True
        assert result["mean"] == 5.5
        assert result["min"] == 1
        assert result["max"] == 10

    def test_aggregation(self):
        """Test data aggregation."""
        from ai_automation_framework.tools.data_processing import DataAnalysisTool

        data = [
            {"category": "A", "value": 10},
            {"category": "A", "value": 20},
            {"category": "B", "value": 30},
        ]

        result = DataAnalysisTool.aggregate(data, group_by="category", agg_column="value")

        assert result["success"] is True
