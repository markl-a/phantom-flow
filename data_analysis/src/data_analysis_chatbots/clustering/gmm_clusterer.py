"""高斯混合模型(GMM)聚類分析器

GMM (Gaussian Mixture Model) 是一種基於概率的軟聚類算法。

優勢:
- 提供概率性聚類(每個樣本屬於各聚類的概率)
- 可以發現橢圓形聚類
- 支持多種協方差類型
- 提供樣本的不確定性度量

適用場景:
- 需要概率性聚類結果
- 數據呈橢圓形分佈
- 需要識別不確定樣本
- 客戶分群(軟分群)
"""

from typing import List, Optional, Dict, Tuple
import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from loguru import logger

from .base import BaseClusterer
from ..exceptions import ClusteringError, ValidationError, raise_if_empty_dataframe, raise_if_columns_missing, require_fitted


class GMMClusterer(BaseClusterer):
    """高斯混合模型聚類分析器

    GMM假設數據由多個高斯分佈混合而成,提供軟聚類(每個點屬於各聚類的概率)。

    Parameters:
        n_components (int): 高斯分佈(聚類)的數量
        covariance_type (str): 協方差類型
            - 'full': 每個分量有各自的協方差矩陣
            - 'tied': 所有分量共享協方差矩陣
            - 'diag': 對角協方差矩陣
            - 'spherical': 球形協方差矩陣
        max_iter (int): EM算法的最大迭代次數
        random_state (int): 隨機種子
        normalize (bool): 是否標準化數據

    Attributes:
        model (GaussianMixture): 訓練好的GMM模型
        scaler (StandardScaler): 數據標準化器
        labels_ (np.ndarray): 硬聚類標籤(最大概率)
        probabilities_ (np.ndarray): 每個樣本屬於各聚類的概率

    Examples:
        >>> clusterer = GMMClusterer(n_components=3)
        >>> labels = clusterer.fit_predict(df, ['Age', 'Income'])
        >>> probs = clusterer.predict_proba(df, ['Age', 'Income'])
        >>> print(f"客戶1屬於聚類0的概率: {probs[0, 0]:.2%}")
    """

    def __init__(
        self,
        n_components: int = 3,
        covariance_type: str = 'full',
        max_iter: int = 100,
        random_state: int = 42,
        normalize: bool = True
    ):
        """初始化GMM聚類器

        Args:
            n_components: 聚類數量
            covariance_type: 協方差類型(full/tied/diag/spherical)
            max_iter: 最大迭代次數
            random_state: 隨機種子(保證可重複性)
            normalize: 是否標準化特徵

        Raises:
            ClusteringError: 當參數無效時
        """
        super().__init__(normalize=normalize, random_state=random_state)

        if n_components < 1:
            raise ClusteringError("n_components必須至少為1", algorithm="GMM", n_clusters=n_components)

        if covariance_type not in ['full', 'tied', 'diag', 'spherical']:
            raise ClusteringError(
                f"無效的covariance_type: {covariance_type}",
                algorithm="GMM"
            )

        self.n_components = n_components
        self.n_clusters = n_components  # 別名，保持一致性
        self.covariance_type = covariance_type
        self.max_iter = max_iter

        self.model: Optional[GaussianMixture] = None
        self.probabilities_: Optional[np.ndarray] = None

        logger.info(
            f"初始化GMM聚類器: n_components={n_components}, "
            f"covariance_type={covariance_type}"
        )

    def fit(self, df: pd.DataFrame, feature_columns: List[str]) -> 'GMMClusterer':
        """訓練GMM模型

        Args:
            df: 輸入數據DataFrame
            feature_columns: 用於聚類的特徵列名

        Returns:
            self: 訓練好的聚類器

        Raises:
            ValidationError: 當數據無效時
            ClusteringError: 當聚類失敗時
        """
        raise_if_empty_dataframe(df, "GMM聚類")
        raise_if_columns_missing(df, feature_columns, "GMM聚類")

        logger.info(f"開始GMM聚類: 特徵={feature_columns}, n_components={self.n_components}")

        # 保存特徵列名
        self.feature_columns = feature_columns

        # 提取特徵
        X = df[feature_columns].values

        # 檢查NaN值
        if np.isnan(X).any():
            raise ValidationError("特徵數據包含NaN值,請先處理缺失值")

        # 檢查樣本數是否足夠
        if len(X) < self.n_components:
            raise ClusteringError(
                f"樣本數({len(X)})少於聚類數({self.n_components})",
                algorithm="GMM",
                n_clusters=self.n_components
            )

        # 標準化
        if self.normalize:
            self.scaler = StandardScaler()
            X = self.scaler.fit_transform(X)
            logger.debug("特徵已標準化")

        # 保存訓練數據用於評估
        self._X_fitted = X

        # 訓練GMM
        try:
            self.model = GaussianMixture(
                n_components=self.n_components,
                covariance_type=self.covariance_type,
                max_iter=self.max_iter,
                random_state=self.random_state
            )

            self.model.fit(X)
            self.labels_ = self.model.predict(X)
            self.probabilities_ = self.model.predict_proba(X)

            # 檢查收斂性
            if not self.model.converged_:
                logger.warning(
                    f"GMM未收斂(迭代{self.model.n_iter_}次)。"
                    f"考慮增加max_iter或調整n_components"
                )

            logger.success(
                f"GMM聚類完成: {self.n_components} 個聚類, "
                f"BIC={self.model.bic(X):.2f}, AIC={self.model.aic(X):.2f}"
            )

            return self

        except Exception as e:
            raise ClusteringError(
                f"GMM聚類失敗: {str(e)}",
                algorithm="GMM",
                n_clusters=self.n_components
            )

    @require_fitted
    def predict(self, df: pd.DataFrame, feature_columns: List[str]) -> np.ndarray:
        """預測新數據的聚類標籤(硬聚類)

        Args:
            df: 新數據DataFrame
            feature_columns: 特徵列名

        Returns:
            預測的聚類標籤

        Raises:
            ClusteringError: 當模型未訓練時
        """
        raise_if_empty_dataframe(df, "GMM預測")
        raise_if_columns_missing(df, feature_columns, "GMM預測")

        X = df[feature_columns].values

        if self.normalize and self.scaler is not None:
            X = self.scaler.transform(X)

        return self.model.predict(X)

    @require_fitted
    def predict_proba(self, df: pd.DataFrame, feature_columns: List[str]) -> np.ndarray:
        """預測新數據屬於各聚類的概率(軟聚類)

        Args:
            df: 新數據DataFrame
            feature_columns: 特徵列名

        Returns:
            概率矩陣,形狀為(n_samples, n_components)

        Raises:
            ClusteringError: 當模型未訓練時
        """
        raise_if_empty_dataframe(df, "GMM概率預測")
        raise_if_columns_missing(df, feature_columns, "GMM概率預測")

        X = df[feature_columns].values

        if self.normalize and self.scaler is not None:
            X = self.scaler.transform(X)

        return self.model.predict_proba(X)

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

    def evaluate_clustering(
        self,
        X: Optional[np.ndarray] = None,
        labels: Optional[np.ndarray] = None
    ) -> Dict[str, float]:
        """評估聚類質量（擴展基類方法，添加 GMM 特有指標）

        包含 BIC、AIC、輪廓係數等多個指標

        Args:
            X: 特徵數據（默認使用 self._X_fitted）
            labels: 聚類標籤（默認使用 self.labels_）

        Returns:
            包含評估指標的字典

        Raises:
            ClusteringError: 當模型未訓練時
        """
        # 獲取基類的評估指標
        metrics = super().evaluate_clustering(X, labels)

        # 添加 GMM 特有的指標
        if self.model is not None and self._X_fitted is not None:
            X_data = X if X is not None else self._X_fitted
            metrics.update({
                'bic': float(self.model.bic(X_data)),
                'aic': float(self.model.aic(X_data)),
                'log_likelihood': float(self.model.score(X_data) * len(X_data)),
                'converged': self.model.converged_,
                'n_iterations': self.model.n_iter_
            })

        logger.info(f"聚類評估完成: BIC={metrics.get('bic', 'N/A')}, AIC={metrics.get('aic', 'N/A')}")
        return metrics

    def get_cluster_summary(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        labels: Optional[np.ndarray] = None,
        extra_stats: Optional[Dict] = None
    ) -> pd.DataFrame:
        """獲取每個聚類的統計摘要（擴展基類方法，添加確定性度量）

        Args:
            df: 原始數據 DataFrame
            feature_columns: 特徵列名
            labels: 聚類標籤（默認使用 self.labels_）
            extra_stats: 額外統計量

        Returns:
            聚類摘要 DataFrame，包含 GMM 特有的 Avg_Certainty 列

        Raises:
            ClusteringError: 當模型未訓練時
        """
        # 構建包含確定性度量的額外統計
        gmm_stats = extra_stats.copy() if extra_stats else {}

        if self.probabilities_ is not None:
            # 添加確定性統計
            def calc_avg_certainty(cluster_data: pd.DataFrame) -> float:
                indices = cluster_data.index
                # 從原始 DataFrame 索引獲取對應的概率
                mask = df.index.isin(indices)
                if mask.any():
                    return float(self.probabilities_[mask].max(axis=1).mean())
                return 0.0

            gmm_stats['Avg_Certainty'] = calc_avg_certainty

        # 調用基類方法
        return super().get_cluster_summary(df, feature_columns, labels, gmm_stats)

    def get_uncertain_samples(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        threshold: float = 0.6
    ) -> pd.DataFrame:
        """獲取不確定的樣本(最大概率低於閾值)

        這些樣本可能需要人工審核或屬於多個聚類

        Args:
            df: 原始數據DataFrame
            feature_columns: 特徵列名
            threshold: 確定性閾值(0-1之間)

        Returns:
            不確定樣本的DataFrame

        Raises:
            ClusteringError: 當模型未訓練時
        """
        if self.probabilities_ is None:
            raise ClusteringError("模型尚未訓練,無法識別不確定樣本", algorithm="GMM")

        max_probs = self.probabilities_.max(axis=1)
        uncertain_mask = max_probs < threshold

        uncertain_df = df[uncertain_mask].copy()
        uncertain_df['Max_Probability'] = max_probs[uncertain_mask]
        uncertain_df['Cluster'] = self.labels_[uncertain_mask]

        # 添加所有聚類的概率
        for i in range(self.n_components):
            uncertain_df[f'Prob_Cluster_{i}'] = self.probabilities_[uncertain_mask, i]

        logger.info(
            f"發現 {len(uncertain_df)} 個不確定樣本 "
            f"({len(uncertain_df) / len(df) * 100:.1f}%)"
        )

        return uncertain_df

    def find_optimal_components(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        max_components: int = 10,
        criterion: str = 'bic'
    ) -> Tuple[int, List[float]]:
        """使用BIC或AIC找到最優聚類數

        Args:
            df: 輸入數據DataFrame
            feature_columns: 特徵列名
            max_components: 最大嘗試的聚類數
            criterion: 評估標準('bic'或'aic')

        Returns:
            (最優聚類數, 評估分數列表)

        Raises:
            ValidationError: 當數據無效時
        """
        raise_if_empty_dataframe(df, "尋找最優聚類數")
        raise_if_columns_missing(df, feature_columns, "尋找最優聚類數")

        X = df[feature_columns].values

        if self.normalize:
            scaler = StandardScaler()
            X = scaler.fit_transform(X)

        scores = []
        n_components_range = range(1, min(max_components + 1, len(X)))

        logger.info(f"開始搜索最優聚類數(1-{max_components}),使用{criterion.upper()}標準")

        for n in n_components_range:
            gmm = GaussianMixture(
                n_components=n,
                covariance_type=self.covariance_type,
                max_iter=self.max_iter,
                random_state=self.random_state
            )
            gmm.fit(X)

            if criterion == 'bic':
                score = gmm.bic(X)
            elif criterion == 'aic':
                score = gmm.aic(X)
            else:
                raise ValidationError(f"未知的criterion: {criterion}")

            scores.append(score)
            logger.debug(f"n_components={n}, {criterion.upper()}={score:.2f}")

        # 找到最小值(BIC和AIC都是越小越好)
        optimal_n = int(np.argmin(scores) + 1)

        logger.success(
            f"最優聚類數: {optimal_n} "
            f"({criterion.upper()}={scores[optimal_n - 1]:.2f})"
        )

        return optimal_n, scores

    def __repr__(self) -> str:
        """字符串表示"""
        status = "已訓練" if self.model is not None else "未訓練"
        return (
            f"GMMClusterer(n_components={self.n_components}, "
            f"covariance_type='{self.covariance_type}', "
            f"normalize={self.normalize}, status={status})"
        )
