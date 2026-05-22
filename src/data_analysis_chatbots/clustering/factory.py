from typing import Type, Dict, Any, List, Optional
from loguru import logger

from .base import BaseClusterer

class ClustererFactory:
    """聚類器工廠類 - 統一創建和管理聚類器"""

    _registry: Dict[str, Type[BaseClusterer]] = {}

    @classmethod
    def _ensure_registry(cls):
        """確保註冊表已初始化"""
        if not cls._registry:
            from .kmeans_clusterer import KMeansClusterer
            from .dbscan_clusterer import DBSCANClusterer
            from .gmm_clusterer import GMMClusterer
            from .hierarchical_clusterer import HierarchicalClusterer

            cls._registry = {
                'kmeans': KMeansClusterer,
                'dbscan': DBSCANClusterer,
                'gmm': GMMClusterer,
                'hierarchical': HierarchicalClusterer,
            }

    @classmethod
    def create(cls, algorithm: str, **kwargs) -> BaseClusterer:
        """創建聚類器實例

        Args:
            algorithm: 聚類算法名稱 (kmeans, dbscan, gmm, hierarchical)
            **kwargs: 傳遞給聚類器的參數

        Returns:
            BaseClusterer: 聚類器實例

        Raises:
            ValueError: 如果算法名稱無效
        """
        if not algorithm or not isinstance(algorithm, str):
            raise ValueError("Algorithm name must be a non-empty string")

        cls._ensure_registry()

        algorithm = algorithm.lower()
        if algorithm not in cls._registry:
            raise ValueError(
                f"Unknown algorithm: {algorithm}. "
                f"Available: {list(cls._registry.keys())}"
            )

        logger.info(f"Creating {algorithm} clusterer with params: {kwargs}")
        return cls._registry[algorithm](**kwargs)

    @classmethod
    def register(cls, name: str, clusterer_class: Type[BaseClusterer]):
        """註冊新的聚類算法"""
        cls._ensure_registry()
        cls._registry[name.lower()] = clusterer_class
        logger.info(f"Registered new clusterer: {name}")

    @classmethod
    def list_algorithms(cls) -> List[str]:
        """列出所有可用算法"""
        cls._ensure_registry()
        return list(cls._registry.keys())

    @classmethod
    def get_algorithm_info(cls, algorithm: str) -> Optional[Dict[str, Any]]:
        """獲取算法信息"""
        cls._ensure_registry()
        clusterer_class = cls._registry.get(algorithm.lower())
        if not clusterer_class:
            return None
        return {
            'name': algorithm,
            'class': clusterer_class.__name__,
            'doc': clusterer_class.__doc__,
        }
