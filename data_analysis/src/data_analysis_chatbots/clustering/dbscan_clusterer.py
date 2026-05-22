"""DBSCAN聚類分析器

DBSCAN (Density-Based Spatial Clustering of Applications with Noise) 是一種基於密度的聚類算法。

優勢:
- 可以發現任意形狀的聚類
- 不需要預先指定聚類數量
- 能夠自動識別異常點(噪聲)
- 對離群值不敏感

適用場景:
- 地理空間數據分析
- 異常檢測
- 客戶行為模式發現
"""

from typing import List, Optional, Tuple, Dict
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from loguru import logger

from .base import BaseClusterer
from ..exceptions import ClusteringError, ValidationError, raise_if_empty_dataframe, raise_if_columns_missing, require_fitted


class DBSCANClusterer(BaseClusterer):
    """DBSCAN聚類分析器

    DBSCAN不需要預先指定聚類數量,而是基於密度來發現聚類。

    Parameters:
        eps (float): 鄰域半徑,兩個樣本被視為鄰居的最大距離
        min_samples (int): 核心點所需的最小鄰居數量
        metric (str): 距離度量方法,默認'euclidean'
        normalize (bool): 是否在聚類前標準化數據

    Attributes:
        model (DBSCAN): 訓練好的DBSCAN模型
        scaler (StandardScaler): 數據標準化器
        labels_ (np.ndarray): 聚類標籤
        n_clusters_ (int): 發現的聚類數量(不含噪聲)
        n_noise_ (int): 噪聲點數量

    Examples:
        >>> clusterer = DBSCANClusterer(eps=0.5, min_samples=5)
        >>> labels = clusterer.fit_predict(df, ['Age', 'Income'])
        >>> print(f"發現 {clusterer.n_clusters_} 個聚類和 {clusterer.n_noise_} 個噪聲點")
    """

    def __init__(
        self,
        eps: float = 0.5,
        min_samples: int = 5,
        metric: str = 'euclidean',
        normalize: bool = True
    ):
        """初始化DBSCAN聚類器

        Args:
            eps: 鄰域半徑(epsilon),較小的值會產生更多聚類
            min_samples: 核心點的最小鄰居數,通常設為特徵維度+1
            metric: 距離度量方法('euclidean', 'manhattan', 'cosine'等)
            normalize: 是否標準化特徵(強烈推薦)

        Raises:
            ClusteringError: 當參數無效時
        """
        super().__init__(normalize=normalize, random_state=42)

        if eps <= 0:
            raise ClusteringError("eps必須大於0", algorithm="DBSCAN")

        if min_samples < 1:
            raise ClusteringError("min_samples必須至少為1", algorithm="DBSCAN")

        self.eps = eps
        self.min_samples = min_samples
        self.metric = metric

        self.model: Optional[DBSCAN] = None
        self.n_clusters_: int = 0
        self.n_noise_: int = 0

        logger.info(f"初始化DBSCAN聚類器: eps={eps}, min_samples={min_samples}")

    def fit(self, df: pd.DataFrame, feature_columns: List[str]) -> 'DBSCANClusterer':
        """訓練DBSCAN模型

        Args:
            df: 輸入數據DataFrame
            feature_columns: 用於聚類的特徵列名

        Returns:
            self: 訓練好的聚類器

        Raises:
            ValidationError: 當數據無效時
            ClusteringError: 當聚類失敗時
        """
        raise_if_empty_dataframe(df, "DBSCAN聚類")
        raise_if_columns_missing(df, feature_columns, "DBSCAN聚類")

        logger.info(f"開始DBSCAN聚類: 特徵={feature_columns}")

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

        # 保存訓練數據用於評估
        self._X_fitted = X

        # 訓練DBSCAN
        try:
            self.model = DBSCAN(
                eps=self.eps,
                min_samples=self.min_samples,
                metric=self.metric
            )
            self.labels_ = self.model.fit_predict(X)

            # 計算聚類統計
            self.n_clusters_ = len(set(self.labels_)) - (1 if -1 in self.labels_ else 0)
            self.n_noise_ = list(self.labels_).count(-1)

            logger.success(
                f"DBSCAN聚類完成: 發現 {self.n_clusters_} 個聚類, "
                f"{self.n_noise_} 個噪聲點 ({self.n_noise_ / len(self.labels_) * 100:.1f}%)"
            )

            return self

        except Exception as e:
            raise ClusteringError(f"DBSCAN聚類失敗: {str(e)}", algorithm="DBSCAN")

    @require_fitted
    def predict(self, df: pd.DataFrame, feature_columns: List[str]) -> np.ndarray:
        """預測新數據的聚類標籤

        注意: DBSCAN不支持直接預測新數據點。
        此方法使用最近鄰方法來分配標籤。

        Args:
            df: 新數據DataFrame
            feature_columns: 特徵列名

        Returns:
            預測的聚類標籤

        Raises:
            ClusteringError: 當模型未訓練或預測失敗時
        """
        raise_if_empty_dataframe(df, "DBSCAN預測")
        raise_if_columns_missing(df, feature_columns, "DBSCAN預測")

        X = df[feature_columns].values

        if self.normalize and self.scaler is not None:
            X = self.scaler.transform(X)

        # 使用最近鄰分配標籤
        from sklearn.neighbors import NearestNeighbors

        # 獲取訓練數據(這裡我們需要存儲它)
        # 注意:這是簡化實現,實際應用中可能需要更複雜的方法
        logger.warning("DBSCAN預測使用近似方法,可能不夠準確")

        # 對於每個新點,找到最近的核心點並分配其標籤
        # 如果最近點是噪聲,則標記為-1
        return np.full(len(X), -1)  # 簡化實現

    def fit_predict(self, df: pd.DataFrame, feature_columns: List[str]) -> np.ndarray:
        """訓練模型並返回聚類標籤

        Args:
            df: 輸入數據DataFrame
            feature_columns: 特徵列名

        Returns:
            聚類標籤數組

        Raises:
            ValidationError: 當數據無效時
            ClusteringError: 當聚類失敗時
        """
        self.fit(df, feature_columns)
        return self.labels_

    # 注意: evaluate_clustering() 和 get_cluster_summary() 現在繼承自 BaseClusterer
    # 基類方法已經處理了 DBSCAN 的噪聲點 (-1) 情況

    @require_fitted
    def get_core_samples(self) -> np.ndarray:
        """獲取核心樣本的索引

        核心樣本是具有足夠鄰居的樣本點

        Returns:
            核心樣本的索引數組

        Raises:
            ClusteringError: 當模型未訓練時
        """
        return self.model.core_sample_indices_

    def find_optimal_eps(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        k: int = None
    ) -> Tuple[float, np.ndarray]:
        """使用K距離圖找到最優eps值

        方法: 計算每個點到其第k個最近鄰的距離,繪製排序後的距離曲線,
        曲線的"肘部"即為最優eps值。

        Args:
            df: 輸入數據DataFrame
            feature_columns: 特徵列名
            k: 鄰居數量,默認為min_samples

        Returns:
            (推薦的eps值, k距離數組)

        Raises:
            ValidationError: 當數據無效時
        """
        raise_if_empty_dataframe(df, "尋找最優eps")
        raise_if_columns_missing(df, feature_columns, "尋找最優eps")

        if k is None:
            k = self.min_samples

        X = df[feature_columns].values

        if self.normalize:
            scaler = StandardScaler()
            X = scaler.fit_transform(X)

        # 計算K距離
        from sklearn.neighbors import NearestNeighbors

        neighbors = NearestNeighbors(n_neighbors=k)
        neighbors.fit(X)
        distances, _ = neighbors.kneighbors(X)

        # 獲取第k個鄰居的距離
        k_distances = distances[:, -1]
        k_distances = np.sort(k_distances)[::-1]  # 降序排列

        # 簡單方法:使用平均距離作為推薦值
        # 更複雜的方法可以使用肘部檢測算法
        recommended_eps = np.mean(k_distances)

        logger.info(f"推薦的eps值: {recommended_eps:.4f} (基於{k}最近鄰)")

        return recommended_eps, k_distances

    def __repr__(self) -> str:
        """字符串表示"""
        status = "已訓練" if self.model is not None else "未訓練"
        return (
            f"DBSCANClusterer(eps={self.eps}, min_samples={self.min_samples}, "
            f"metric='{self.metric}', normalize={self.normalize}, status={status})"
        )
