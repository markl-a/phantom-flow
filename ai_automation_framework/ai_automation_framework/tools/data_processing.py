"""Excel, CSV, and data processing automation tools."""

import pandas as pd
import csv
from typing import Dict, Any, List, Optional
from pathlib import Path
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
import json


class ExcelAutomationTool:
    """Advanced Excel/CSV processing tool."""

    @staticmethod
    def read_excel(
        file_path: str,
        sheet_name: Optional[str] = None,
        header: int = 0
    ) -> Dict[str, Any]:
        """
        Read Excel file.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name to read (None for first sheet)
            header: Row number to use as header

        Returns:
            Data and metadata
        """
        try:
            # Validate file exists
            if not Path(file_path).exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header)

            return {
                "success": True,
                "rows": len(df),
                "columns": list(df.columns),
                "data": df.to_dict('records'),
                "preview": df.head(5).to_dict('records')
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except ValueError as e:
            return {"success": False, "error": f"Invalid Excel format or sheet: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def write_excel(
        file_path: str,
        data: List[Dict[str, Any]],
        sheet_name: str = "Sheet1",
        auto_format: bool = True
    ) -> Dict[str, Any]:
        """
        Write data to Excel file.

        Args:
            file_path: Output file path
            data: Data to write
            sheet_name: Sheet name
            auto_format: Apply auto-formatting

        Returns:
            Result
        """
        try:
            df = pd.DataFrame(data)

            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)

                if auto_format:
                    worksheet = writer.sheets[sheet_name]

                    # Format header
                    for cell in worksheet[1]:
                        cell.font = Font(bold=True)
                        cell.fill = PatternFill(start_color="CCE5FF",
                                              end_color="CCE5FF",
                                              fill_type="solid")
                        cell.alignment = Alignment(horizontal='center')

                    # Auto-adjust column widths
                    for column in worksheet.columns:
                        max_length = 0
                        column_letter = column[0].column_letter
                        for cell in column:
                            try:
                                if len(str(cell.value)) > max_length:
                                    max_length = len(str(cell.value))
                            except (TypeError, AttributeError):
                                pass
                        adjusted_width = min(max_length + 2, 50)
                        worksheet.column_dimensions[column_letter].width = adjusted_width

            return {
                "success": True,
                "file": file_path,
                "rows": len(data),
                "columns": len(data[0]) if data else 0
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def merge_excel_files(
        file_paths: List[str],
        output_path: str
    ) -> Dict[str, Any]:
        """
        Merge multiple Excel files.

        Args:
            file_paths: List of Excel files to merge
            output_path: Output file path

        Returns:
            Merge result
        """
        try:
            # Validate all files exist
            for file_path in file_paths:
                if not Path(file_path).exists():
                    return {"success": False, "error": f"File not found: {file_path}"}

            dfs = []
            for file_path in file_paths:
                df = pd.read_excel(file_path)
                dfs.append(df)

            merged_df = pd.concat(dfs, ignore_index=True)
            merged_df.to_excel(output_path, index=False)

            return {
                "success": True,
                "files_merged": len(file_paths),
                "total_rows": len(merged_df),
                "output": output_path
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except ValueError as e:
            return {"success": False, "error": f"Error merging files: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def excel_to_csv(excel_path: str, csv_path: str) -> Dict[str, Any]:
        """Convert Excel to CSV."""
        try:
            # Validate file exists
            if not Path(excel_path).exists():
                return {"success": False, "error": f"File not found: {excel_path}"}

            df = pd.read_excel(excel_path)
            df.to_csv(csv_path, index=False)

            return {
                "success": True,
                "input": excel_path,
                "output": csv_path,
                "rows": len(df)
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except ValueError as e:
            return {"success": False, "error": f"Invalid file format: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def csv_to_excel(csv_path: str, excel_path: str) -> Dict[str, Any]:
        """Convert CSV to Excel."""
        try:
            # Validate file exists
            if not Path(csv_path).exists():
                return {"success": False, "error": f"File not found: {csv_path}"}

            df = pd.read_csv(csv_path)
            df.to_excel(excel_path, index=False)

            return {
                "success": True,
                "input": csv_path,
                "output": excel_path,
                "rows": len(df)
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except ValueError as e:
            return {"success": False, "error": f"Invalid file format: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class CSVProcessingTool:
    """CSV processing and manipulation tool."""

    @staticmethod
    def read_csv(
        file_path: str,
        delimiter: str = ',',
        encoding: str = 'utf-8'
    ) -> Dict[str, Any]:
        """Read CSV file."""
        try:
            # Validate file exists
            if not Path(file_path).exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            df = pd.read_csv(file_path, delimiter=delimiter, encoding=encoding)

            return {
                "success": True,
                "rows": len(df),
                "columns": list(df.columns),
                "data": df.to_dict('records'),
                "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except UnicodeDecodeError as e:
            return {"success": False, "error": f"Encoding error: {str(e)}"}
        except pd.errors.ParserError as e:
            return {"success": False, "error": f"CSV parsing error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def write_csv(
        file_path: str,
        data: List[Dict[str, Any]],
        delimiter: str = ',',
        encoding: str = 'utf-8'
    ) -> Dict[str, Any]:
        """Write CSV file."""
        try:
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False, sep=delimiter, encoding=encoding)

            return {
                "success": True,
                "file": file_path,
                "rows": len(df),
                "columns": len(df.columns)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def filter_csv(
        file_path: str,
        column: str,
        value: Any,
        output_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Filter CSV by column value."""
        try:
            # Validate file exists
            if not Path(file_path).exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            df = pd.read_csv(file_path)

            # Validate column exists
            if column not in df.columns:
                return {
                    "success": False,
                    "error": f"Column '{column}' not found. Available columns: {list(df.columns)}"
                }

            filtered_df = df[df[column] == value]

            if output_path:
                filtered_df.to_csv(output_path, index=False)

            return {
                "success": True,
                "original_rows": len(df),
                "filtered_rows": len(filtered_df),
                "data": filtered_df.to_dict('records')
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except KeyError as e:
            return {"success": False, "error": f"Column error: {str(e)}"}
        except pd.errors.ParserError as e:
            return {"success": False, "error": f"CSV parsing error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def aggregate_csv(
        file_path: str,
        group_by: str,
        aggregations: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Aggregate CSV data.

        Args:
            file_path: CSV file path
            group_by: Column to group by
            aggregations: {column: operation} e.g., {'sales': 'sum', 'price': 'mean'}

        Returns:
            Aggregated data
        """
        try:
            # Validate file exists
            if not Path(file_path).exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            df = pd.read_csv(file_path)

            # Validate group_by column exists
            if group_by not in df.columns:
                return {
                    "success": False,
                    "error": f"Group by column '{group_by}' not found. Available columns: {list(df.columns)}"
                }

            # Validate aggregation columns exist
            invalid_cols = [col for col in aggregations.keys() if col not in df.columns]
            if invalid_cols:
                return {
                    "success": False,
                    "error": f"Aggregation columns not found: {invalid_cols}. Available columns: {list(df.columns)}"
                }

            # Validate aggregation operations
            valid_operations = ['sum', 'mean', 'median', 'min', 'max', 'count', 'std', 'var']
            invalid_ops = [op for op in aggregations.values() if op not in valid_operations]
            if invalid_ops:
                return {
                    "success": False,
                    "error": f"Invalid aggregation operations: {invalid_ops}. Valid operations: {valid_operations}"
                }

            result = df.groupby(group_by).agg(aggregations).reset_index()

            return {
                "success": True,
                "groups": len(result),
                "data": result.to_dict('records')
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except KeyError as e:
            return {"success": False, "error": f"Column error: {str(e)}"}
        except pd.errors.ParserError as e:
            return {"success": False, "error": f"CSV parsing error: {str(e)}"}
        except ValueError as e:
            return {"success": False, "error": f"Aggregation error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class DataAnalysisTool:
    """Data analysis and statistics tool."""

    @staticmethod
    def get_statistics(data: List[Dict[str, Any]], column: str) -> Dict[str, Any]:
        """Get statistical summary for a column."""
        try:
            df = pd.DataFrame(data)

            if column not in df.columns:
                return {"success": False, "error": f"Column '{column}' not found"}

            stats = df[column].describe().to_dict()

            return {
                "success": True,
                "column": column,
                "count": int(stats.get('count', 0)),
                "mean": float(stats.get('mean', 0)),
                "std": float(stats.get('std', 0)),
                "min": float(stats.get('min', 0)),
                "max": float(stats.get('max', 0)),
                "25%": float(stats.get('25%', 0)),
                "50%": float(stats.get('50%', 0)),
                "75%": float(stats.get('75%', 0))
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def detect_outliers(
        data: List[Dict[str, Any]],
        column: str,
        method: str = 'iqr'
    ) -> Dict[str, Any]:
        """
        Detect outliers in data.

        Args:
            data: Data list
            column: Column to analyze
            method: Detection method ('iqr' or 'zscore')

        Returns:
            Outliers information
        """
        try:
            df = pd.DataFrame(data)

            # Validate column exists
            if column not in df.columns:
                return {
                    "success": False,
                    "error": f"Column '{column}' not found. Available columns: {list(df.columns)}"
                }

            # Validate column is numeric
            if not pd.api.types.is_numeric_dtype(df[column]):
                return {
                    "success": False,
                    "error": f"Column '{column}' must be numeric for outlier detection"
                }

            if method == 'iqr':
                Q1 = df[column].quantile(0.25)
                Q3 = df[column].quantile(0.75)
                IQR = Q3 - Q1
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR

                outliers = df[(df[column] < lower_bound) | (df[column] > upper_bound)]
            else:  # zscore
                from scipy import stats
                z_scores = stats.zscore(df[column])
                outliers = df[abs(z_scores) > 3]

            return {
                "success": True,
                "method": method,
                "total_records": len(df),
                "outlier_count": len(outliers),
                "outliers": outliers.to_dict('records')
            }
        except KeyError as e:
            return {"success": False, "error": f"Column error: {str(e)}"}
        except ValueError as e:
            return {"success": False, "error": f"Value error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @staticmethod
    def pivot_data(
        data: List[Dict[str, Any]],
        index: str,
        columns: str,
        values: str,
        aggfunc: str = 'sum'
    ) -> Dict[str, Any]:
        """Create pivot table from data."""
        try:
            df = pd.DataFrame(data)

            # Validate all required columns exist
            required_columns = [index, columns, values]
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                return {
                    "success": False,
                    "error": f"Required columns not found: {missing_columns}. Available columns: {list(df.columns)}"
                }

            # Validate aggfunc
            valid_aggfuncs = ['sum', 'mean', 'median', 'min', 'max', 'count', 'std', 'var']
            if aggfunc not in valid_aggfuncs:
                return {
                    "success": False,
                    "error": f"Invalid aggregation function: {aggfunc}. Valid options: {valid_aggfuncs}"
                }

            pivot = pd.pivot_table(
                df,
                index=index,
                columns=columns,
                values=values,
                aggfunc=aggfunc
            )

            return {
                "success": True,
                "data": pivot.to_dict()
            }
        except KeyError as e:
            return {"success": False, "error": f"Column error: {str(e)}"}
        except ValueError as e:
            return {"success": False, "error": f"Pivot error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Tool schemas
DATA_PROCESSING_SCHEMAS = {
    "read_excel": {
        "type": "function",
        "function": {
            "name": "read_excel",
            "description": "Read data from Excel file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "sheet_name": {"type": "string"}
                },
                "required": ["file_path"]
            }
        }
    },
    "write_excel": {
        "type": "function",
        "function": {
            "name": "write_excel",
            "description": "Write data to Excel file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "data": {"type": "array"}
                },
                "required": ["file_path", "data"]
            }
        }
    }
}
