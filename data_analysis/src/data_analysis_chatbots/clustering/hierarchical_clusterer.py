"""層次聚類分析器

Hierarchical Clustering 是一種構建聚類層次結構的算法。

優勢:
- 不需要預先指定聚類數量
- 提供樹狀圖(dendrogram)可視化
- 可以在不同層次切割得到不同數量的聚類
- 適合發現數據的層次結構

適用場景:
- 需要探索不同層次的聚類結構
- 數據具有自然的層次關係
- 需要可視化聚類過程
- 小到中等規模數據集
"""

from typing import List, Optional, Dict, Tuple
import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering
from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import dendrogram, linkage
from loguru import logger

from .base import BaseClusterer
from ..exceptions import ClusteringError, ValidationError, raise_if_empty_dataframe, raise_if_columns_missing


class HierarchicalClusterer(BaseClusterer):
    """層次聚類分析器

    使用凝聚式(Agglomerative)層次聚類算法,從下到上構建聚類層次。

    Parameters:
        n_clusters (int): 最終聚類數量(可選,可通過樹狀圖確定)
        linkage (str): 連接方法
            - 'ward': 最小化方差(默認,適用於大多數情況)
            - 'complete': 最大距離
            - 'average': 平均距離
            - 'single': 最小距離
        metric (str): 距離度量方法
        normalize (bool): 是否標準化數據

    Attributes:
        model (AgglomerativeClustering): 訓練好的模型
        scaler (StandardScaler): 數據標準化器
        labels_ (np.ndarray): 聚類標籤
        linkage_matrix_ (np.ndarray): 連接矩陣(用於繪製樹狀圖)

    Examples:
        >>> clusterer = HierarchicalClusterer(n_clusters=4, linkage='ward')
        >>> labels = clusterer.fit_predict(df, ['Age', 'Income'])
        >>> clusterer.plot_dendrogram()
    """

    def __init__(
        self,
        n_clusters: Optional[int] = 2,
        linkage: str = 'ward',
        metric: str = 'euclidean',
        normalize: bool = True,
        random_state: int = 42
    ):
        """初始化層次聚類器

        Args:
            n_clusters: 聚類數量(None表示不切割)
            linkage: 連接方法(ward/complete/average/single)
            metric: 距離度量(euclidean/manhattan/cosine等)
            normalize: 是否標準化特徵
            random_state: 隨機種子

        Raises:
            ClusteringError: 當參數無效時
        """
        super().__init__(normalize=normalize, random_state=random_state)

        if n_clusters is not None and n_clusters < 1:
            raise ClusteringError(
                "n_clusters必須至少為1或None",
                algorithm="Hierarchical",
                n_clusters=n_clusters
            )

        if linkage not in ['ward', 'complete', 'average', 'single']:
            raise ClusteringError(
                f"無效的linkage方法: {linkage}",
                algorithm="Hierarchical"
            )

        # ward只支持euclidean距離
        if linkage == 'ward' and metric != 'euclidean':
            logger.warning("ward連接只支持euclidean距離,已自動調整")
            metric = 'euclidean'

        self.n_clusters = n_clusters
        self.linkage = linkage
        self.metric = metric

        self.model: Optional[AgglomerativeClustering] = None
        self.linkage_matrix_: Optional[np.ndarray] = None

        logger.info(
            f"初始化層次聚類器: n_clusters={n_clusters}, "
            f"linkage={linkage}, metric={metric}"
        )

    def fit(self, df: pd.DataFrame, feature_columns: List[str]) -> 'HierarchicalClusterer':
        """訓練層次聚類模型

        Args:
            df: 輸入數據DataFrame
            feature_columns: 用於聚類的特徵列名

        Returns:
            self: 訓練好的聚類器

        Raises:
            ValidationError: 當數據無效時
            ClusteringError: 當聚類失敗時
        """
        raise_if_empty_dataframe(df, "層次聚類")
        raise_if_columns_missing(df, feature_columns, "層次聚類")

        logger.info(
            f"開始層次聚類: 特徵={feature_columns}, "
            f"n_clusters={self.n_clusters}"
        )

        # 保存特徵列名
        self.feature_columns = feature_columns

        # 提取特徵
        X = df[feature_columns].values

        # 檢查NaN值
        if np.isnan(X).any():
            raise ValidationError("特徵數據包含NaN值,請先處理缺失值")

        # 標準化
        if self.normalize:
            self.scaler = StandardScaler()
            X = self.scaler.fit_transform(X)
            logger.debug("特徵已標準化")

        # 保存訓練數據用於評估和繪製樹狀圖
        self._X_fitted = X

        # 訓練模型
        try:
            self.model = AgglomerativeClustering(
                n_clusters=self.n_clusters,
                linkage=self.linkage,
                metric=self.metric
            )

            self.labels_ = self.model.fit_predict(X)

            # 計算連接矩陣(用於樹狀圖)
            self.linkage_matrix_ = linkage(X, method=self.linkage, metric=self.metric)

            logger.success(f"層次聚類完成: {self.n_clusters} 個聚類")

            return self

        except Exception as e:
            raise ClusteringError(
                f"層次聚類失敗: {str(e)}",
                algorithm="Hierarchical",
                n_clusters=self.n_clusters
            )

    def predict(self, df: pd.DataFrame, feature_columns: List[str]) -> np.ndarray:
        """預測新數據的聚類標籤

        注意: 層次聚類不直接支持預測。此方法使用最近質心方法。

        Args:
            df: 新數據DataFrame
            feature_columns: 特徵列名

        Returns:
            預測的聚類標籤

        Raises:
            ClusteringError: 當模型未訓練時
        """
        if self.model is None or self.labels_ is None:
            raise ClusteringError("模型尚未訓練,請先調用fit()", algorithm="Hierarchical")

        raise_if_empty_dataframe(df, "層次聚類預測")
        raise_if_columns_missing(df, feature_columns, "層次聚類預測")

        logger.warning("層次聚類使用最近質心方法預測,可能不夠準確")

        X_new = df[feature_columns].values

        if self.normalize and self.scaler is not None:
            X_new = self.scaler.transform(X_new)

        # 計算訓練數據的聚類質心
        if self._X_fitted is None:
            raise ClusteringError("缺少訓練數據,無法預測", algorithm="Hierarchical")

        centroids = []
        for i in range(self.n_clusters):
            mask = self.labels_ == i
            if mask.any():
                centroids.append(self._X_fitted[mask].mean(axis=0))
            else:
                logger.warning(f"聚類 {i} 為空,跳過")

        centroids = np.array(centroids)

        # 為每個新樣本分配最近的聚類
        from scipy.spatial.distance import cdist
        distances = cdist(X_new, centroids, metric=self.metric)
        predictions = distances.argmin(axis=1)

        return predictions

    def fit_predict(self, df: pd.DataFrame, feature_columns: List[str]) -> np.ndarray:
        """訓練模型並返回聚類標籤

        Args:
            df: 輸入數據DataFrame
            feature_columns: 特徵列名

        Returns:
            聚類標籤數組
        """
        self.fit(df, feature_columns)
        return self.labels_

    # 注意: evaluate_clustering() 和 get_cluster_summary() 現在繼承自 BaseClusterer

    def plot_dendrogram(
        self,
        max_d: Optional[float] = None,
        figsize: Tuple[int, int] = (12, 6),
        save_path: Optional[str] = None
    ):
        """繪製樹狀圖

        Args:
            max_d: 在此高度繪製水平線(可視化切割點)
            figsize: 圖形大小
            save_path: 保存路徑(可選)

        Raises:
            ClusteringError: 當模型未訓練時
        """
        if self.linkage_matrix_ is None:
            raise ClusteringError("模型尚未訓練,無法繪製樹狀圖", algorithm="Hierarchical")

        try:
            import matplotlib.pyplot as plt

            plt.figure(figsize=figsize)
            dendrogram(
                self.linkage_matrix_,
                truncate_mode='lastp',
                p=30,  # 顯示最後30次合併
                leaf_rotation=90,
                leaf_font_size=10,
                show_contracted=True
            )

            plt.title(f'層次聚類樹狀圖 (linkage={self.linkage})')
            plt.xlabel('樣本索引或聚類大小')
            plt.ylabel('距離')

            if max_d is not None:
                plt.axhline(y=max_d, c='red', linestyle='--', label=f'切割線 (距離={max_d})')
                plt.legend()

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path, dpi=300, bbox_inches='tight')
                logger.info(f"樹狀圖已保存到: {save_path}")

            plt.show()
            logger.success("樹狀圖繪製完成")

        except ImportError:
            logger.error("需要matplotlib來繪製樹狀圖")
            raise ClusteringError("matplotlib未安裝", algorithm="Hierarchical")
        except Exception as e:
            raise ClusteringError(f"繪製樹狀圖失敗: {str(e)}", algorithm="Hierarchical")

    def find_optimal_clusters(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        max_clusters: int = 10
    ) -> Tuple[int, List[float]]:
        """使用輪廓係數找到最優聚類數

        Args:
            df: 輸入數據DataFrame
            feature_columns: 特徵列名
            max_clusters: 最大嘗試的聚類數

        Returns:
            (最優聚類數, 輪廓係數列表)

        Raises:
            ValidationError: 當數據無效時
        """
        raise_if_empty_dataframe(df, "尋找最優聚類數")
        raise_if_columns_missing(df, feature_columns, "尋找最優聚類數")

        X = df[feature_columns].values

        if self.normalize:
            scaler = StandardScaler()
            X = scaler.fit_transform(X)

        silhouette_scores = []
        n_clusters_range = range(2, min(max_clusters + 1, len(X)))

        logger.info(f"開始搜索最優聚類數(2-{max_clusters}),使用輪廓係數")

        for n in n_clusters_range:
            clusterer = AgglomerativeClustering(
                n_clusters=n,
                linkage=self.linkage,
                metric=self.metric
            )
            labels = clusterer.fit_predict(X)

            try:
                score = silhouette_score(X, labels)
                silhouette_scores.append(score)
                logger.debug(f"n_clusters={n}, silhouette={score:.4f}")
            except Exception as e:
                logger.warning(f"n_clusters={n} 評估失敗: {e}")
                silhouette_scores.append(0)

        # 找到最大值
        optimal_n = int(np.argmax(silhouette_scores) + 2)

        logger.success(
            f"最優聚類數: {optimal_n} "
            f"(輪廓係數={silhouette_scores[optimal_n - 2]:.4f})"
        )

        return optimal_n, silhouette_scores

    def cut_tree(self, n_clusters: int) -> np.ndarray:
        """在不同高度切割樹得到不同數量的聚類

        Args:
            n_clusters: 目標聚類數量

        Returns:
            新的聚類標籤

        Raises:
            ClusteringError: 當模型未訓練時
        """
        if self.linkage_matrix_ is None or self._X_fitted is None:
            raise ClusteringError("模型尚未訓練,無法切割樹", algorithm="Hierarchical")

        from scipy.cluster.hierarchy import fcluster

        labels = fcluster(self.linkage_matrix_, n_clusters, criterion='maxclust')

        # 轉換為0開始的索引
        labels = labels - 1

        logger.info(f"樹已切割為 {n_clusters} 個聚類")

        # 更新當前標籤
        self.n_clusters = n_clusters
        self.labels_ = labels

        return labels

    def __repr__(self) -> str:
        """字符串表示"""
        status = "已訓練" if self.model is not None else "未訓練"
        return (
            f"HierarchicalClusterer(n_clusters={self.n_clusters}, "
            f"linkage='{self.linkage}', metric='{self.metric}', "
            f"normalize={self.normalize}, status={status})"
        )
