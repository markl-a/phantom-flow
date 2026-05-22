"""Customer clustering and segmentation modules.

此模塊提供多種聚類算法:
- KMeansClusterer: K-均值聚類(快速,適合球形聚類)
- DBSCANClusterer: 密度聚類(發現任意形狀,自動檢測異常)
- GMMClusterer: 高斯混合模型(概率性軟聚類)
- HierarchicalClusterer: 層次聚類(樹狀結構,可視化佳)
- RFMAnalyzer: RFM客戶分析
"""

from .base import BaseClusterer
from .factory import ClustererFactory
from .kmeans_clusterer import KMeansClusterer
from .rfm_analyzer import RFMAnalyzer
from .dbscan_clusterer import DBSCANClusterer
from .gmm_clusterer import GMMClusterer
from .hierarchical_clusterer import HierarchicalClusterer
from .evaluator import ClusteringEvaluator, find_optimal_k

__all__ = [
    "BaseClusterer",
    "ClustererFactory",
    "KMeansClusterer",
    "RFMAnalyzer",
    "DBSCANClusterer",
    "GMMClusterer",
    "HierarchicalClusterer",
    "ClusteringEvaluator",
    "find_optimal_k",
]
