"""模型保存和加載工具

此模塊提供統一的接口用於保存和加載訓練好的聚類模型。

支持功能:
- 保存/加載聚類模型
- 模型元數據管理
- 版本控制
- 模型註冊表
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime
import json
import joblib
from loguru import logger

from .exceptions import ModelSaveError, ModelLoadError


class ModelRegistry:
    """模型註冊表

    管理所有已保存的模型,提供查詢和管理功能。
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """初始化模型註冊表

        Args:
            registry_path: 註冊表文件路徑(默認: models/registry.json)
        """
        if registry_path is None:
            registry_path = Path('models') / 'registry.json'

        self.registry_path = Path(registry_path)
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Any]:
        """從文件加載註冊表"""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"無法加載註冊表: {e}")
                return {'models': {}}
        return {'models': {}}

    def _save_registry(self):
        """保存註冊表到文件"""
        try:
            with open(self.registry_path, 'w', encoding='utf-8') as f:
                json.dump(self.registry, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存註冊表失敗: {e}")

    def register_model(
        self,
        model_id: str,
        metadata: Dict[str, Any]
    ) -> None:
        """註冊新模型

        Args:
            model_id: 模型唯一標識符
            metadata: 模型元數據
        """
        self.registry['models'][model_id] = {
            **metadata,
            'registered_at': datetime.now().isoformat()
        }
        self._save_registry()
        logger.info(f"模型已註冊: {model_id}")

    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """獲取模型信息

        Args:
            model_id: 模型標識符

        Returns:
            模型元數據,如果不存在則返回None
        """
        return self.registry['models'].get(model_id)

    def list_models(
        self,
        algorithm: Optional[str] = None,
        dataset: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """列出所有模型

        Args:
            algorithm: 篩選算法類型(可選)
            dataset: 篩選數據集(可選)

        Returns:
            模型列表
        """
        models = []
        for model_id, metadata in self.registry['models'].items():
            # 應用篩選條件
            if algorithm and metadata.get('algorithm') != algorithm:
                continue
            if dataset and metadata.get('dataset') != dataset:
                continue

            models.append({
                'model_id': model_id,
                **metadata
            })

        return models

    def delete_model(self, model_id: str, remove_file: bool = False) -> bool:
        """從註冊表刪除模型

        Args:
            model_id: 模型標識符
            remove_file: 是否同時刪除模型文件

        Returns:
            是否成功刪除
        """
        if model_id not in self.registry['models']:
            logger.warning(f"模型不存在: {model_id}")
            return False

        model_info = self.registry['models'][model_id]

        # 刪除文件
        if remove_file and 'path' in model_info:
            model_path = Path(model_info['path'])
            if model_path.exists():
                try:
                    model_path.unlink()
                    logger.info(f"已刪除模型文件: {model_path}")
                except Exception as e:
                    logger.error(f"刪除模型文件失敗: {e}")

        # 從註冊表移除
        del self.registry['models'][model_id]
        self._save_registry()
        logger.info(f"模型已從註冊表移除: {model_id}")

        return True


def save_model(
    clusterer,
    model_path: Optional[Path] = None,
    model_name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    register: bool = True
) -> Path:
    """保存聚類模型

    Args:
        clusterer: 已訓練的聚類器
        model_path: 保存路徑(如果為None則自動生成)
        model_name: 模型名稱(用於註冊表)
        metadata: 額外的元數據
        register: 是否註冊到模型註冊表

    Returns:
        保存的文件路徑

    Raises:
        ModelSaveError: 保存失敗時

    Examples:
        >>> clusterer = KMeansClusterer(n_clusters=5)
        >>> clusterer.fit(df, features)
        >>> path = save_model(clusterer, model_name='customer_segmentation')
    """
    try:
        # 生成模型路徑
        if model_path is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            algorithm_name = clusterer.__class__.__name__.replace('Clusterer', '').lower()
            filename = f"{algorithm_name}_{timestamp}.pkl"
            model_path = Path('models') / filename

        model_path = Path(model_path)
        model_path.parent.mkdir(parents=True, exist_ok=True)

        # 保存模型
        joblib.dump(clusterer, model_path)
        logger.success(f"模型已保存到: {model_path}")

        # 準備元數據
        full_metadata = {
            'algorithm': clusterer.__class__.__name__,
            'path': str(model_path),
            'size_bytes': model_path.stat().st_size,
            'saved_at': datetime.now().isoformat()
        }

        # 添加模型特定的元數據
        if hasattr(clusterer, 'n_clusters'):
            full_metadata['n_clusters'] = clusterer.n_clusters
        if hasattr(clusterer, 'n_components'):
            full_metadata['n_components'] = clusterer.n_components
        if hasattr(clusterer, 'eps'):
            full_metadata['eps'] = clusterer.eps
        if hasattr(clusterer, 'linkage'):
            full_metadata['linkage'] = clusterer.linkage

        # 合併用戶提供的元數據
        if metadata:
            full_metadata.update(metadata)

        # 註冊模型
        if register:
            model_id = model_name or model_path.stem
            registry = ModelRegistry()
            registry.register_model(model_id, full_metadata)

        return model_path

    except Exception as e:
        raise ModelSaveError(
            f"保存模型失敗: {str(e)}",
            file_path=str(model_path) if model_path else None
        ) from e


def load_model(
    model_path: Optional[Path] = None,
    model_name: Optional[str] = None
):
    """加載聚類模型

    Args:
        model_path: 模型文件路徑(與model_name二選一)
        model_name: 模型名稱(從註冊表查找)

    Returns:
        加載的聚類器對象

    Raises:
        ModelLoadError: 加載失敗時

    Examples:
        >>> # 從路徑加載
        >>> clusterer = load_model(model_path='models/kmeans_20250118.pkl')

        >>> # 從註冊表加載
        >>> clusterer = load_model(model_name='customer_segmentation')
    """
    try:
        # 從註冊表查找路徑
        if model_name and not model_path:
            registry = ModelRegistry()
            model_info = registry.get_model_info(model_name)

            if not model_info:
                raise ModelLoadError(
                    f"模型未在註冊表中找到: {model_name}"
                )

            model_path = Path(model_info['path'])

        if not model_path:
            raise ModelLoadError("必須提供 model_path 或 model_name")

        model_path = Path(model_path)

        if not model_path.exists():
            raise ModelLoadError(
                f"模型文件不存在: {model_path}",
                file_path=str(model_path)
            )

        # 加載模型
        clusterer = joblib.load(model_path)
        logger.success(f"模型已加載: {model_path}")

        return clusterer

    except Exception as e:
        if isinstance(e, ModelLoadError):
            raise
        raise ModelLoadError(
            f"加載模型失敗: {str(e)}",
            file_path=str(model_path) if model_path else None
        ) from e


def export_model_metadata(
    model_name: str,
    output_path: Optional[Path] = None,
    registry: Optional[ModelRegistry] = None,
) -> Path:
    """導出模型元數據為JSON

    Args:
        model_name: 模型名稱
        output_path: 輸出路徑(默認: models/{model_name}_metadata.json)
        registry: 指定 ModelRegistry 實例。預設 None 會建立新的（使用預設 registry path），
            測試或多 registry 場景下可傳入自訂的 registry。

    Returns:
        導出的文件路徑

    Examples:
        >>> export_model_metadata('customer_segmentation')
    """
    if registry is None:
        registry = ModelRegistry()
    model_info = registry.get_model_info(model_name)

    if not model_info:
        raise ModelLoadError(f"模型未找到: {model_name}")

    if output_path is None:
        output_path = Path('models') / f"{model_name}_metadata.json"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(model_info, f, indent=2, ensure_ascii=False)

    logger.info(f"元數據已導出到: {output_path}")
    return output_path


def compare_models(
    model_names: List[str],
    registry: Optional[ModelRegistry] = None,
) -> None:
    """比較多個模型的元數據

    Args:
        model_names: 模型名稱列表
        registry: 指定 ModelRegistry 實例。預設 None 會建立新的。

    Examples:
        >>> compare_models(['model_v1', 'model_v2', 'model_v3'])
    """
    import pandas as pd

    if registry is None:
        registry = ModelRegistry()
    models_info = []

    for name in model_names:
        info = registry.get_model_info(name)
        if info:
            models_info.append({
                'Model Name': name,
                **info
            })

    # Print to stdout (not logger) so callers can capture output via
    # standard stdout-redirection mechanisms (pytest's capsys, shell
    # piping, etc.). The original implementation used logger.info which
    # writes to stderr by default and bypasses capsys.out.
    if not models_info:
        print("沒有找到任何模型")
        return

    df = pd.DataFrame(models_info)
    print()
    print("=" * 80)
    print("模型比較")
    print("=" * 80)
    print(df.to_string(index=False))
    print("=" * 80)


def cleanup_old_models(
    days: int = 30,
    dry_run: bool = True,
    registry: Optional[ModelRegistry] = None,
) -> List[str]:
    """清理舊模型

    Args:
        days: 保留最近N天的模型
        dry_run: 僅模擬,不實際刪除
        registry: 指定 ModelRegistry 實例。預設 None 會建立新的。

    Returns:
        刪除(或將要刪除)的模型ID列表

    Examples:
        >>> # 查看將被刪除的模型
        >>> to_delete = cleanup_old_models(days=30, dry_run=True)

        >>> # 實際刪除
        >>> deleted = cleanup_old_models(days=30, dry_run=False)
    """
    from datetime import timedelta

    if registry is None:
        registry = ModelRegistry()
    cutoff_date = datetime.now() - timedelta(days=days)
    to_delete = []

    # Snapshot the keys upfront because delete_model() mutates the
    # underlying dict — iterating over the live dict while deleting
    # raises RuntimeError on Python 3.x.
    for model_id in list(registry.registry['models'].keys()):
        metadata = registry.registry['models'][model_id]
        registered_at_str = metadata.get('registered_at', '')
        if not registered_at_str:
            continue
        registered_at = datetime.fromisoformat(registered_at_str)

        if registered_at < cutoff_date:
            to_delete.append(model_id)

            if not dry_run:
                registry.delete_model(model_id, remove_file=True)

    if dry_run:
        logger.info(f"[模擬模式] 將刪除 {len(to_delete)} 個模型")
        for model_id in to_delete:
            logger.info(f"  - {model_id}")
    else:
        logger.success(f"已刪除 {len(to_delete)} 個舊模型")

    return to_delete


# 便捷函數別名
save = save_model
load = load_model


if __name__ == '__main__':
    # 示例用法
    logger.info("Model Utils - 使用示例")
    logger.info("="*50)

    # 列出所有模型
    registry = ModelRegistry()
    models = registry.list_models()
    logger.info(f"\n找到 {len(models)} 個已註冊的模型")

    for model in models:
        logger.info(f"  - {model['model_id']} ({model.get('algorithm', 'Unknown')})")
