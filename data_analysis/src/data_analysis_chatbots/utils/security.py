"""安全相關工具函數"""
import re
from typing import List, Tuple


class SensitiveDataFilter:
    """敏感數據過濾器"""

    PATTERNS: List[Tuple[str, str]] = [
        (r'api[_-]?key\s*[=:]\s*["\']?([^"\'\s]+)["\']?', 'api_key=***'),
        (r'password\s*[=:]\s*["\']?([^"\'\s]+)["\']?', 'password=***'),
        (r'token\s*[=:]\s*["\']?([^"\'\s]+)["\']?', 'token=***'),
        (r'secret\s*[=:]\s*["\']?([^"\'\s]+)["\']?', 'secret=***'),
        (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),
    ]

    @classmethod
    def filter(cls, text: str) -> str:
        """過濾文本中的敏感信息"""
        for pattern, replacement in cls.PATTERNS:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text
