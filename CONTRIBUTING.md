# 貢獻指南

感謝你考慮為 **Data Analysis with Chatbots** 做出貢獻！

## 📋 目錄

- [行為準則](#行為準則)
- [如何貢獻](#如何貢獻)
- [開發環境設置](#開發環境設置)
- [提交規範](#提交規範)
- [測試要求](#測試要求)
- [文檔](#文檔)
- [問題回報](#問題回報)

## 行為準則

本專案遵循 [Contributor Covenant](CODE_OF_CONDUCT.md) 行為準則。參與本專案即表示你同意遵守此準則。

## 如何貢獻

### 報告 Bug

如果你發現 Bug，請在 GitHub Issues 中創建新的 issue：

1. 使用清晰描述性的標題
2. 詳細描述重現步驟
3. 提供預期行為和實際行為
4. 包含環境信息（OS、Python 版本等）
5. 如果可能，提供最小可重現範例

### 建議新功能

我們歡迎新功能建議！請：

1. 檢查是否已有類似建議
2. 清楚說明功能用途和使用場景
3. 提供範例代碼或使用案例
4. 解釋為什麼此功能對其他用戶有用

### 提交代碼

#### 第一次貢獻？

1. Fork 本倉庫
2. 克隆你的 fork
3. 創建新分支（`git checkout -b feature/amazing-feature`）
4. 進行你的修改
5. 提交你的更改
6. 推送到分支
7. 開啟 Pull Request

#### Pull Request 流程

1. 確保所有測試通過
2. 更新相關文檔
3. 遵循代碼風格指南
4. 撰寫清晰的提交信息
5. 在 PR 描述中引用相關 issue

## 開發環境設置

### 1. 克隆倉庫

```bash
git clone https://github.com/markl-a/Data-Analysis-with-Chatbots.git
cd Data-Analysis-with-Chatbots
```

### 2. 創建虛擬環境

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows
```

### 3. 安裝依賴

```bash
# 安裝開發依賴
pip install -e ".[dev]"

# 安裝 pre-commit hooks
pre-commit install
```

### 4. 運行測試

```bash
# 運行所有測試
pytest

# 運行特定測試
pytest tests/test_clustering.py

# 生成覆蓋率報告
pytest --cov=src/data_analysis_chatbots --cov-report=html
```

## 代碼風格

我們使用以下工具確保代碼質量：

### 格式化

```bash
# Black (代碼格式化)
black src/ tests/

# isort (導入排序)
isort src/ tests/
```

### 檢查

```bash
# Flake8 (代碼檢查)
flake8 src/ tests/ --max-line-length=100

# MyPy (類型檢查)
mypy src/ --ignore-missing-imports

# Bandit (安全檢查)
bandit -r src/
```

### 使用 Makefile

```bash
# 格式化代碼
make format

# 運行所有檢查
make lint

# 運行測試
make test

# 完整 CI 流程
make ci
```

## 提交規範

我們遵循 [Conventional Commits](https://www.conventionalcommits.org/) 規範：

### 提交信息格式

```
<類型>[可選範圍]: <描述>

[可選正文]

[可選頁腳]
```

### 類型

- `feat`: 新功能
- `fix`: Bug 修復
- `docs`: 文檔更新
- `style`: 代碼格式（不影響代碼運行）
- `refactor`: 重構（既不是新功能也不是修復）
- `perf`: 性能優化
- `test`: 添加或修改測試
- `chore`: 構建過程或輔助工具的變動

### 範例

```bash
feat(clustering): add DBSCAN clustering algorithm
fix(rfm): correct recency calculation for edge cases
docs: update installation instructions
test(marketing): add tests for CLV predictor
```

## 測試要求

### 測試覆蓋率

- 所有新代碼必須有相應測試
- 維持測試覆蓋率至少 60%
- 關鍵功能應達到 80%+ 覆蓋率

### 測試類型

1. **單元測試**: 測試單個函數/方法
2. **集成測試**: 測試模塊間交互
3. **端到端測試**: 測試完整工作流

### 編寫測試

```python
import pytest
from data_analysis_chatbots import YourClass

class TestYourClass:
    @pytest.fixture
    def sample_data(self):
        return {"key": "value"}

    def test_your_feature(self, sample_data):
        result = YourClass().method(sample_data)
        assert result == expected_value
```

## 文檔

### Docstring 風格

我們使用 Google 風格的 docstrings：

```python
def function(arg1: int, arg2: str) -> bool:
    """函數的簡短描述。

    更詳細的描述（如果需要）。

    Args:
        arg1: 參數1的描述
        arg2: 參數2的描述

    Returns:
        返回值的描述

    Raises:
        ValueError: 錯誤情況的描述

    Examples:
        >>> function(1, "test")
        True
    """
    pass
```

### 更新文檔

- 添加新功能時更新 README.md
- 更新相關的教程文檔
- 更新 API 文檔（Sphinx）
- 在 CHANGELOG.md 中記錄變更

## 發布流程

### 版本號規則

我們遵循 [Semantic Versioning](https://semver.org/)：

- `MAJOR.MINOR.PATCH`
- MAJOR: 不兼容的 API 變更
- MINOR: 向後兼容的新功能
- PATCH: 向後兼容的 Bug 修復

### 發布步驟

1. 更新版本號（`setup.py`, `pyproject.toml`, `__init__.py`）
2. 更新 `CHANGELOG.md`
3. 創建 Git tag
4. 推送到 GitHub
5. 創建 GitHub Release
6. 自動發布到 PyPI（GitHub Actions）

## 需要幫助？

- 📧 創建 [GitHub Issue](https://github.com/markl-a/Data-Analysis-with-Chatbots/issues)
- 💬 參與 [Discussions](https://github.com/markl-a/Data-Analysis-with-Chatbots/discussions)
- 📖 閱讀 [文檔](https://github.com/markl-a/Data-Analysis-with-Chatbots#readme)

## 致謝

感謝所有貢獻者！你們的努力讓這個專案變得更好。

---

再次感謝你的貢獻！🎉
