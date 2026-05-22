from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable, Union
import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score, davies_bouldin_score
from loguru import logger


class BaseClusterer(ABC):
    """所有聚類算法的統一基類

    此基類提供聚類算法的通用功能，包括：
    - 特徵預處理和標準化
    - 聚類摘要統計生成
    - 聚類評估指標計算
    - 聚類分布分析

    子類只需實現 fit() 和 predict() 方法即可獲得完整功能。

    Attributes:
        normalize: 是否標準化特徵
        random_state: 隨機種子
        scaler: StandardScaler 實例
        labels_: 聚類標籤
        feature_columns: 用於聚類的特徵列
        _X_fitted: 訓練時使用的特徵數據
    """

    def __init__(self, normalize: bool = True, random_state: int = 42):
        """初始化基類

        Args:
            normalize: 是否標準化特徵數據
            random_state: 隨機種子，用於結果可重複性
        """
        self.normalize = normalize
        self.random_state = random_state
        self.scaler: Optional[StandardScaler] = None
        self.labels_: Optional[np.ndarray] = None
        self.feature_columns: Optional[List[str]] = None
        self._X_fitted: Optional[np.ndarray] = None

    def _prepare_features(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        fit_scaler: bool = True
    ) -> np.ndarray:
        """提取並標準化特徵(共用邏輯)

        Args:
            df: 輸入 DataFrame
            feature_columns: 特徵列名列表
            fit_scaler: 是否訓練 scaler (False 用於 transform)

        Returns:
            處理後的特徵數組

        Raises:
            ValidationError: 當數據無效時
        """
        from ..exceptions import ValidationError

        if df.empty:
            raise ValidationError("DataFrame is empty")

        missing_cols = set(feature_columns) - set(df.columns)
        if missing_cols:
            raise ValidationError(f"Missing columns: {missing_cols}")

        X = df[feature_columns].values

        if np.isnan(X).any():
            raise ValidationError("Feature data contains NaN values")

        if self.normalize:
            if fit_scaler:
                self.scaler = StandardScaler()
                X = self.scaler.fit_transform(X)
            else:
                if self.scaler is None:
                    raise ValueError("Scaler not fitted")
                X = self.scaler.transform(X)

        return X

    @abstractmethod
    def fit(self, df: pd.DataFrame, feature_columns: List[str]) -> 'BaseClusterer':
        """訓練聚類模型

        Args:
            df: 輸入數據 DataFrame
            feature_columns: 用於聚類的特徵列名

        Returns:
            self: 訓練後的聚類器實例
        """
        pass

    @abstractmethod
    def predict(self, df: pd.DataFrame, feature_columns: List[str]) -> np.ndarray:
        """預測新數據的聚類標籤

        Args:
            df: 新數據 DataFrame
            feature_columns: 特徵列名

        Returns:
            聚類標籤數組
        """
        pass

    def fit_predict(self, df: pd.DataFrame, feature_columns: List[str]) -> np.ndarray:
        """訓練並預測

        Args:
            df: 輸入數據 DataFrame
            feature_columns: 特徵列名

        Returns:
            聚類標籤數組
        """
        self.fit(df, feature_columns)
        return self.labels_

    def get_cluster_summary(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        labels: Optional[np.ndarray] = None,
        extra_stats: Optional[Dict[str, Callable]] = None
    ) -> pd.DataFrame:
        """獲取每個聚類的統計摘要（通用實現）

        此方法提供聚類摘要的通用計算邏輯，包括：
        - 聚類大小和百分比
        - 每個特徵的均值和標準差
        - 可選的額外統計量

        Args:
            df: 原始數據 DataFrame
            feature_columns: 特徵列名列表
            labels: 聚類標籤（默認使用 self.labels_）
            extra_stats: 額外統計量字典，格式為 {列名: 計算函數}

        Returns:
            聚類摘要 DataFrame，包含每個聚類的統計信息

        Raises:
            ClusteringError: 當模型未訓練時

        Example:
            >>> summary = clusterer.get_cluster_summary(
            ...     df,
            ...     ['Age', 'Income'],
            ...     extra_stats={'Age_median': lambda x: x['Age'].median()}
            ... )
        """
        from ..exceptions import ClusteringError

        # 使用提供的標籤或默認標籤
        cluster_labels = labels if labels is not None else self.labels_

        if cluster_labels is None:
            raise ClusteringError(
                "模型尚未訓練，無法生成摘要",
                algorithm=self.__class__.__name__
            )

        # 創建帶有聚類標籤的 DataFrame（避免修改原始數據）
        df_with_clusters = df.assign(Cluster=cluster_labels)

        # 獲取唯一的聚類標籤（排序以保持一致性）
        unique_clusters = sorted(df_with_clusters['Cluster'].unique())

        summary_list = []
        for cluster_id in unique_clusters:
            cluster_data = df_with_clusters[df_with_clusters['Cluster'] == cluster_id]

            # 處理特殊標籤（如 DBSCAN 的噪聲點 -1）
            cluster_name = 'Noise' if cluster_id == -1 else cluster_id

            summary = {
                'Cluster': cluster_name,
                'Size': len(cluster_data),
                'Percentage': round(len(cluster_data) / len(df_with_clusters) * 100, 2)
            }

            # 計算每個特徵的統計量
            for col in feature_columns:
                if col in cluster_data.columns:
                    summary[f'{col}_mean'] = round(cluster_data[col].mean(), 4)
                    summary[f'{col}_std'] = round(cluster_data[col].std(), 4)

            # 計算額外統計量
            if extra_stats:
                for stat_name, stat_func in extra_stats.items():
                    try:
                        summary[stat_name] = stat_func(cluster_data)
                    except Exception as e:
                        logger.warning(f"計算 {stat_name} 時出錯: {e}")
                        summary[stat_name] = None

            summary_list.append(summary)

        summary_df = pd.DataFrame(summary_list)
        logger.debug(f"生成聚類摘要: {len(summary_list)} 個聚類")

        return summary_df

    def get_cluster_distribution(self, labels: Optional[np.ndarray] = None) -> pd.DataFrame:
        """獲取聚類分布統計

        Args:
            labels: 聚類標籤（默認使用 self.labels_）

        Returns:
            包含聚類分布的 DataFrame
        """
        cluster_labels = labels if labels is not None else self.labels_

        if cluster_labels is None:
            from ..exceptions import ClusteringError
            raise ClusteringError(
                "模型尚未訓練",
                algorithm=self.__class__.__name__
            )

        distribution = pd.Series(cluster_labels).value_counts().sort_index()

        return pd.DataFrame({
            'Cluster': distribution.index,
            'Count': distribution.values,
            'Percentage': (distribution.values / len(cluster_labels) * 100).round(2)
        })

    def evaluate_clustering(
        self,
        X: Optional[Union[np.ndarray, pd.DataFrame]] = None,
        feature_cols: Optional[List[str]] = None,
        labels: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """評估聚類質量（通用實現）

        計算常用的聚類評估指標：
        - silhouette_score: 輪廓係數（-1 到 1，越高越好）
        - davies_bouldin_score: DB 指數（越低越好）
        - noise_percentage: 噪聲點佔總樣本的百分比

        兩種呼叫方式：
            1. evaluate_clustering(df, ['feature1', 'feature2'])
               → 傳 DataFrame + 特徵欄位名稱（會自動 to_numpy）
            2. evaluate_clustering()                         （使用 fit 時的資料）
            3. evaluate_clustering(X=arr, labels=lbl)        （直接傳 numpy）

        Args:
            X: 特徵數據（DataFrame 或 ndarray，None 用 self._X_fitted）
            feature_cols: 當 X 是 DataFrame 時要使用的欄位名稱
            labels: 聚類標籤（默認使用 self.labels_）

        Returns:
            包含評估指標的字典
        """
        from ..exceptions import ClusteringError

        # Resolve X. If caller passed (DataFrame, [col_names]) extract the columns;
        # otherwise fall back to fit-time data.
        if X is not None and isinstance(X, pd.DataFrame) and feature_cols is not None:
            X_data = X[feature_cols].to_numpy()
        elif X is not None:
            X_data = X
        else:
            X_data = self._X_fitted

        cluster_labels = labels if labels is not None else self.labels_

        if X_data is None or cluster_labels is None:
            raise ClusteringError(
                "模型尚未訓練，無法評估",
                algorithm=self.__class__.__name__
            )

        # 獲取有效聚類數（排除噪聲點）
        valid_mask = cluster_labels != -1
        n_clusters = len(set(cluster_labels[valid_mask]))
        n_samples = len(cluster_labels)
        n_noise = int((cluster_labels == -1).sum())

        # Per-cluster sample count keyed by cluster label (-1 = noise).
        # Useful for spotting heavily-skewed clusterings without eyeballing
        # silhouette numbers alone.
        cluster_distribution: Dict[int, int] = (
            pd.Series(cluster_labels).value_counts().sort_index().to_dict()
        )

        metrics: Dict[str, Any] = {
            'n_clusters':           n_clusters,
            'n_samples':            n_samples,
            'n_noise':              n_noise,
            'noise_percentage':     round(n_noise / n_samples * 100, 2) if n_samples else 0.0,
            'cluster_distribution': {int(k): int(v) for k, v in cluster_distribution.items()},
        }

        # 只有當有足夠的聚類時才計算評估指標
        if n_clusters >= 2 and valid_mask.sum() > n_clusters:
            X_valid = X_data[valid_mask]
            labels_valid = cluster_labels[valid_mask]

            try:
                metrics['silhouette_score'] = float(
                    silhouette_score(X_valid, labels_valid)
                )
            except Exception as e:
                logger.warning(f"無法計算輪廓係數: {e}")
                metrics['silhouette_score'] = None

            try:
                metrics['davies_bouldin_score'] = float(
                    davies_bouldin_score(X_valid, labels_valid)
                )
            except Exception as e:
                logger.warning(f"無法計算 Davies-Bouldin 指數: {e}")
                metrics['davies_bouldin_score'] = None
        else:
            metrics['silhouette_score'] = None
            metrics['davies_bouldin_score'] = None
            logger.warning("聚類數量不足，跳過評估指標計算")

        return metrics

    def to_dict(self) -> Dict[str, Any]:
        """導出為字典(用於序列化)

        Returns:
            包含聚類器配置的字典
        """
        return {
            'algorithm': self.__class__.__name__,
            'normalize': self.normalize,
            'random_state': self.random_state,
            'n_clusters': getattr(self, 'n_clusters', None),
            'feature_columns': self.feature_columns,
        }
