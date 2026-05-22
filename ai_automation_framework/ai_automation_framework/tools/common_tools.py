"""Common tools for agents."""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# 导入新的工具基类
from ai_automation_framework.core.tool_registry import (
    BaseTool,
    ToolMetadata,
    register_tool
)


class WebSearchTool:
    """Tool for web searching (simulated)."""

    @staticmethod
    def search(query: str, num_results: int = 5) -> List[Dict[str, str]]:
        """
        Search the web for information.

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of search results
        """
        # In production, integrate with real search API (SerpAPI, Google Custom Search, etc.)
        return [
            {
                "title": f"Result {i+1} for: {query}",
                "url": f"https://example.com/result{i+1}",
                "snippet": f"This is a sample search result for '{query}'"
            }
            for i in range(num_results)
        ]


class CalculatorTool:
    """Tool for mathematical calculations."""

    @staticmethod
    def calculate(expression: str) -> Dict[str, Any]:
        """
        Evaluate a mathematical expression safely.

        Args:
            expression: Mathematical expression as string

        Returns:
            Calculation result
        """
        import ast
        import operator

        # Define allowed operators
        operators = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
            ast.USub: operator.neg,
            ast.UAdd: operator.pos,
        }

        def safe_eval(node):
            """Safely evaluate an AST node."""
            if isinstance(node, ast.Constant):  # Python 3.8+
                if isinstance(node.value, (int, float)):
                    return node.value
                raise ValueError(f"Invalid constant: {node.value}")
            elif isinstance(node, ast.Num):  # Python 3.7 compatibility
                return node.n
            elif isinstance(node, ast.BinOp):
                op_type = type(node.op)
                if op_type not in operators:
                    raise ValueError(f"Unsupported operator: {op_type.__name__}")
                left = safe_eval(node.left)
                right = safe_eval(node.right)
                return operators[op_type](left, right)
            elif isinstance(node, ast.UnaryOp):
                op_type = type(node.op)
                if op_type not in operators:
                    raise ValueError(f"Unsupported operator: {op_type.__name__}")
                return operators[op_type](safe_eval(node.operand))
            elif isinstance(node, ast.Expression):
                return safe_eval(node.body)
            else:
                raise ValueError(f"Unsupported expression type: {type(node).__name__}")

        try:
            # Parse expression into AST
            tree = ast.parse(expression, mode='eval')
            result = safe_eval(tree)
            return {
                "expression": expression,
                "result": result,
                "success": True
            }
        except (ValueError, SyntaxError, TypeError, ZeroDivisionError) as e:
            return {
                "expression": expression,
                "error": str(e),
                "success": False
            }
        except Exception as e:
            return {
                "expression": expression,
                "error": f"Evaluation error: {str(e)}",
                "success": False
            }

    @staticmethod
    def calculate_percentage(value: float, percentage: float) -> float:
        """Calculate percentage of a value."""
        return (value * percentage) / 100

    @staticmethod
    def calculate_compound_interest(
        principal: float,
        rate: float,
        time: float,
        n: int = 1
    ) -> Dict[str, float]:
        """
        Calculate compound interest.

        Args:
            principal: Initial amount
            rate: Annual interest rate (as percentage)
            time: Time in years
            n: Number of times interest is compounded per year

        Returns:
            Dictionary with calculation details
        """
        amount = principal * (1 + (rate/100)/n) ** (n * time)
        interest = amount - principal

        return {
            "principal": principal,
            "rate": rate,
            "time": time,
            "compound_frequency": n,
            "final_amount": round(amount, 2),
            "interest_earned": round(interest, 2)
        }


class FileSystemTool:
    """Tool for file system operations."""

    # Class-level configuration for allowed base directories
    # Can be set by application to restrict file access
    ALLOWED_BASE_DIRS: Optional[List[str]] = None  # None means no restriction

    @staticmethod
    def _validate_file_path(file_path: str, operation: str = "access") -> Path:
        """
        Validate file path to prevent path traversal attacks.

        Security checks:
        1. Null byte injection prevention
        2. Path traversal prevention (../)
        3. Symbolic link validation
        4. Base directory restriction (if configured)

        Args:
            file_path: File path to validate
            operation: Operation type for error messages

        Returns:
            Validated Path object

        Raises:
            ValueError: If path is invalid or unsafe
        """
        if not file_path or not file_path.strip():
            raise ValueError("file_path cannot be empty")

        # Check for null byte injection
        if '\0' in file_path:
            raise ValueError(
                f"Path contains null byte - potential security attack detected. "
                f"Operation '{operation}' denied."
            )

        try:
            # Convert to Path object and resolve to absolute path
            path = Path(file_path).resolve()
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid file path: {str(e)}")

        # Check if path is within allowed base directories (if configured)
        if FileSystemTool.ALLOWED_BASE_DIRS is not None:
            allowed = False
            for base_dir in FileSystemTool.ALLOWED_BASE_DIRS:
                try:
                    base_path = Path(base_dir).resolve()
                    # Check if path is within base directory
                    path.relative_to(base_path)
                    allowed = True
                    break
                except ValueError:
                    # path.relative_to raises ValueError if path is not relative to base
                    continue

            if not allowed:
                raise ValueError(
                    f"Access denied: Path '{file_path}' is outside allowed directories. "
                    f"Allowed base directories: {FileSystemTool.ALLOWED_BASE_DIRS}"
                )

        # Check for symbolic links (optional security measure)
        # Symbolic links can be used to bypass directory restrictions
        if path.exists() and path.is_symlink():
            # Resolve the symlink and validate the target
            real_path = path.resolve()

            # If base directories are configured, ensure symlink target is also within allowed paths
            if FileSystemTool.ALLOWED_BASE_DIRS is not None:
                allowed = False
                for base_dir in FileSystemTool.ALLOWED_BASE_DIRS:
                    try:
                        base_path = Path(base_dir).resolve()
                        real_path.relative_to(base_path)
                        allowed = True
                        break
                    except ValueError:
                        continue

                if not allowed:
                    raise ValueError(
                        f"Access denied: Symbolic link target '{real_path}' is outside allowed directories. "
                        f"Allowed base directories: {FileSystemTool.ALLOWED_BASE_DIRS}"
                    )

        return path

    @staticmethod
    def read_file(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
        """
        Read a text file with security validation.

        Security: This method validates file paths to prevent path traversal attacks.
        Configure ALLOWED_BASE_DIRS to restrict access to specific directories.

        Args:
            file_path: Path to the file
            encoding: File encoding

        Returns:
            File content and metadata
        """
        # Validate encoding parameter
        if not encoding or not encoding.strip():
            return {"error": "encoding cannot be empty", "success": False}

        try:
            # Test if encoding is valid
            "".encode(encoding)
        except LookupError:
            return {"error": f"Invalid encoding: {encoding}", "success": False}

        try:
            # Validate file path for security
            path = FileSystemTool._validate_file_path(file_path, "read")

            if not path.exists():
                return {"error": f"File not found: {file_path}", "success": False}

            if not path.is_file():
                return {"error": f"Not a file: {file_path}", "success": False}

            content = path.read_text(encoding=encoding)

            return {
                "path": str(path.absolute()),
                "content": content,
                "size": path.stat().st_size,
                "lines": len(content.splitlines()),
                "success": True
            }
        except ValueError as e:
            # Security validation error
            return {"error": f"Security validation failed: {str(e)}", "success": False}
        except UnicodeDecodeError as e:
            return {"error": f"Encoding error: {str(e)}", "success": False}
        except PermissionError as e:
            return {"error": f"Permission denied: {str(e)}", "success": False}
        except OSError as e:
            return {"error": f"OS error: {str(e)}", "success": False}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    @staticmethod
    def write_file(
        file_path: str,
        content: str,
        encoding: str = "utf-8"
    ) -> Dict[str, Any]:
        """
        Write content to a file with security validation.

        Security: This method validates file paths to prevent path traversal attacks.
        Configure ALLOWED_BASE_DIRS to restrict access to specific directories.

        Args:
            file_path: Path to the file
            content: Content to write
            encoding: File encoding

        Returns:
            Operation result
        """
        # Validate encoding parameter
        if not encoding or not encoding.strip():
            return {"error": "encoding cannot be empty", "success": False}

        try:
            # Test if encoding is valid
            "".encode(encoding)
        except LookupError:
            return {"error": f"Invalid encoding: {encoding}", "success": False}

        try:
            # Validate file path for security
            path = FileSystemTool._validate_file_path(file_path, "write")

            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding=encoding)

            return {
                "path": str(path.absolute()),
                "size": path.stat().st_size,
                "success": True
            }
        except ValueError as e:
            # Security validation error
            return {"error": f"Security validation failed: {str(e)}", "success": False}
        except UnicodeEncodeError as e:
            return {"error": f"Encoding error: {str(e)}", "success": False}
        except PermissionError as e:
            return {"error": f"Permission denied: {str(e)}", "success": False}
        except OSError as e:
            return {"error": f"OS error: {str(e)}", "success": False}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "success": False}

    @staticmethod
    def list_directory(dir_path: str) -> Dict[str, Any]:
        """
        List contents of a directory.

        Args:
            dir_path: Directory path

        Returns:
            Directory contents
        """
        # Validate dir_path parameter
        if not dir_path or not dir_path.strip():
            return {"error": "dir_path cannot be empty", "success": False}

        try:
            path = Path(dir_path)

            if not path.exists():
                return {"error": f"Directory not found: {dir_path}", "success": False}

            if not path.is_dir():
                return {"error": f"Not a directory: {dir_path}", "success": False}

            files = []
            directories = []

            for item in path.iterdir():
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "size": item.stat().st_size,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
                elif item.is_dir():
                    directories.append(item.name)

            return {
                "path": str(path.absolute()),
                "files": files,
                "directories": directories,
                "total_items": len(files) + len(directories),
                "success": True
            }
        except PermissionError as e:
            return {"error": f"Permission denied: {str(e)}", "success": False}
        except OSError as e:
            return {"error": f"OS error: {str(e)}", "success": False}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "success": False}


class DateTimeTool:
    """Tool for date and time operations."""

    @staticmethod
    def get_current_datetime(timezone: str = "UTC") -> Dict[str, str]:
        """
        Get current date and time.

        Args:
            timezone: Timezone (currently only UTC)

        Returns:
            Current datetime information
        """
        now = datetime.now()

        return {
            "datetime": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timestamp": int(now.timestamp()),
            "weekday": now.strftime("%A"),
            "timezone": timezone
        }

    @staticmethod
    def calculate_date_difference(
        date1: str,
        date2: str,
        date_format: str = "%Y-%m-%d"
    ) -> Dict[str, Any]:
        """
        Calculate difference between two dates.

        Args:
            date1: First date string
            date2: Second date string
            date_format: Date format string

        Returns:
            Date difference information
        """
        try:
            d1 = datetime.strptime(date1, date_format)
            d2 = datetime.strptime(date2, date_format)
            diff = abs((d2 - d1).days)

            return {
                "date1": date1,
                "date2": date2,
                "difference_days": diff,
                "difference_weeks": diff // 7,
                "difference_months": diff // 30,
                "success": True
            }
        except ValueError as e:
            return {"error": f"Date parsing error: {str(e)}", "success": False}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "success": False}


class DataProcessingTool:
    """Tool for data processing operations."""

    @staticmethod
    def parse_json(json_string: str) -> Dict[str, Any]:
        """
        Parse JSON string.

        Args:
            json_string: JSON string

        Returns:
            Parsed data or error
        """
        try:
            data = json.loads(json_string)
            return {"data": data, "success": True}
        except json.JSONDecodeError as e:
            return {"error": str(e), "success": False}

    @staticmethod
    def to_json(data: Any, indent: int = 2) -> Dict[str, Any]:
        """
        Convert data to JSON string.

        Args:
            data: Data to convert
            indent: JSON indentation

        Returns:
            JSON string or error
        """
        try:
            json_string = json.dumps(data, indent=indent)
            return {"json": json_string, "success": True}
        except Exception as e:
            return {"error": str(e), "success": False}

    @staticmethod
    def count_words(text: str) -> Dict[str, Any]:
        """
        Count words in text.

        Args:
            text: Text to analyze

        Returns:
            Word count statistics
        """
        words = text.split()
        unique_words = set(word.lower() for word in words)

        return {
            "total_words": len(words),
            "unique_words": len(unique_words),
            "characters": len(text),
            "characters_no_spaces": len(text.replace(" ", "")),
            "lines": len(text.splitlines()),
            "success": True
        }


# Tool schemas for OpenAI function calling
TOOL_SCHEMAS = {
    "web_search": {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    "calculator": {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Calculate a mathematical expression",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2+2', '10*5')"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    "read_file": {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read content from a text file",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the file to read"
                    }
                },
                "required": ["file_path"]
            }
        }
    },
    "get_datetime": {
        "type": "function",
        "function": {
            "name": "get_datetime",
            "description": "Get current date and time",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }
}


# Tool registry mapping
TOOL_REGISTRY = {
    "web_search": WebSearchTool.search,
    "calculator": CalculatorTool.calculate,
    "read_file": FileSystemTool.read_file,
    "write_file": FileSystemTool.write_file,
    "list_directory": FileSystemTool.list_directory,
    "get_datetime": DateTimeTool.get_current_datetime,
    "parse_json": DataProcessingTool.parse_json,
    "count_words": DataProcessingTool.count_words,
}
