"""K-Means clustering for customer segmentation.

This module provides an optimized K-Means clustering implementation with:
- Parallel processing for optimal cluster search
- Caching for performance optimization
- Comprehensive validation and error handling
"""

from typing import Optional, List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import functools

import numpy as np
import pandas as pd
from loguru import logger
from sklearn.cluster import KMeans
from sklearn.metrics import davies_bouldin_score, silhouette_score, calinski_harabasz_score
from sklearn.preprocessing import StandardScaler

from .base import BaseClusterer
from ..exceptions import require_fitted, ValidationError, ClusteringError


def cached_property(func):
    """Simple cached property decorator for memoization."""
    attr_name = f'_cached_{func.__name__}'

    @functools.wraps(func)
    def wrapper(self):
        if not hasattr(self, attr_name):
            setattr(self, attr_name, func(self))
        return getattr(self, attr_name)

    return property(wrapper)


class KMeansClusterer(BaseClusterer):
    """Perform K-Means clustering for customer segmentation.

    This class provides a comprehensive K-Means clustering solution with
    optimization features including parallel cluster search and result caching.

    Attributes:
        n_clusters: Number of clusters to form
        random_state: Random seed for reproducibility
        max_iter: Maximum iterations for K-Means algorithm
        n_init: Number of initializations to try
        model: Fitted sklearn KMeans model
        inertia_: Sum of squared distances to cluster centers

    Example:
        >>> clusterer = KMeansClusterer(n_clusters=5)
        >>> labels = clusterer.fit_predict(df, ['Age', 'Income', 'Score'])
        >>> summary = clusterer.get_cluster_summary(df, ['Age', 'Income'])
    """

    def __init__(
        self,
        n_clusters: int = 5,
        random_state: int = 42,
        max_iter: int = 300,
        n_init: int = 10,
        normalize: bool = True
    ):
        """Initialize the K-Means Clusterer.

        Args:
            n_clusters: Number of clusters (must be >= 2)
            random_state: Random state for reproducibility
            max_iter: Maximum number of iterations
            n_init: Number of times K-means will be run with different centroid seeds
            normalize: Whether to normalize features before clustering

        Raises:
            ValidationError: If n_clusters < 2 or other invalid parameters
        """
        super().__init__(normalize=normalize, random_state=random_state)

        # Validate parameters
        if n_clusters < 2:
            raise ValidationError("n_clusters must be at least 2")
        if max_iter < 1:
            raise ValidationError("max_iter must be at least 1")
        if n_init < 1:
            raise ValidationError("n_init must be at least 1")

        self.n_clusters = n_clusters
        self.max_iter = max_iter
        self.n_init = n_init

        self.model: Optional[KMeans] = None
        self.inertia_: Optional[float] = None
        self._evaluation_cache: Dict[str, Any] = {}

    def _clear_cache(self) -> None:
        """Clear all cached results."""
        self._evaluation_cache = {}
        for attr in list(self.__dict__.keys()):
            if attr.startswith('_cached_'):
                delattr(self, attr)

    def fit(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        scale_features: bool = True
    ) -> 'KMeansClusterer':
        """Fit the K-Means model.

        Args:
            df: DataFrame containing features
            feature_columns: List of columns to use for clustering
            scale_features: Whether to scale features before clustering

        Returns:
            self

        Raises:
            ValidationError: If data is invalid or columns are missing
        """
        logger.info(f"Fitting K-Means with {self.n_clusters} clusters...")

        # Clear cached results from previous fit
        self._clear_cache()

        # Validate input
        if df.empty:
            raise ValidationError("DataFrame is empty")

        if len(df) < self.n_clusters:
            raise ValidationError(
                f"Number of samples ({len(df)}) must be >= n_clusters ({self.n_clusters})"
            )

        # Validate feature columns
        missing_cols = set(feature_columns) - set(df.columns)
        if missing_cols:
            raise ValidationError(f"Columns not found in DataFrame: {missing_cols}")

        self.feature_columns = feature_columns
        self.normalize = scale_features

        # Prepare data
        X = df[feature_columns].copy()

        # Handle missing values
        if X.isnull().any().any():
            logger.warning("Missing values detected. Filling with median values.")
            X = X.fillna(X.median())

        # Scale features
        if scale_features:
            self.scaler = StandardScaler()
            self._X_fitted = self.scaler.fit_transform(X)
        else:
            self._X_fitted = X.values

        # Fit K-Means
        self.model = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            max_iter=self.max_iter,
            n_init=self.n_init
        )

        self.model.fit(self._X_fitted)
        self.labels_ = self.model.labels_
        self.inertia_ = self.model.inertia_

        logger.success(f"K-Means clustering completed. Inertia: {self.inertia_:.2f}")

        return self

    @require_fitted
    def predict(self, df: pd.DataFrame, feature_columns: Optional[List[str]] = None) -> np.ndarray:
        """Predict cluster labels for new data.

        Args:
            df: DataFrame containing features
            feature_columns: Feature columns (uses fitted columns if None)

        Returns:
            Cluster labels array

        Raises:
            ClusteringError: If model is not fitted
            ValidationError: If data is invalid
        """
        if feature_columns is None:
            feature_columns = self.feature_columns

        X = df[feature_columns].copy()

        # Handle missing values
        if X.isnull().any().any():
            X = X.fillna(X.median())

        # Scale features
        if self.normalize and self.scaler is not None:
            X_scaled = self.scaler.transform(X)
        else:
            X_scaled = X.values

        return self.model.predict(X_scaled)

    def fit_predict(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        scale_features: bool = True
    ) -> np.ndarray:
        """Fit the model and predict cluster labels.

        Args:
            df: DataFrame containing features
            feature_columns: List of columns to use for clustering
            scale_features: Whether to scale features

        Returns:
            Cluster labels array
        """
        self.fit(df, feature_columns, scale_features)
        return self.labels_

    @require_fitted
    def get_cluster_centers(self, inverse_transform: bool = True) -> pd.DataFrame:
        """Get cluster centers.

        Args:
            inverse_transform: Whether to inverse transform scaled centers

        Returns:
            DataFrame with cluster centers
        """
        centers = self.model.cluster_centers_

        if inverse_transform and self.scaler is not None:
            centers = self.scaler.inverse_transform(centers)

        return pd.DataFrame(centers, columns=self.feature_columns)

    @require_fitted
    def evaluate_clustering(self) -> Dict[str, float]:
        """Evaluate clustering quality with comprehensive metrics.

        Returns:
            Dictionary with evaluation metrics including:
            - inertia: Sum of squared distances
            - silhouette_score: Cluster separation quality (-1 to 1)
            - davies_bouldin_score: Cluster similarity measure (lower is better)
            - calinski_harabasz_score: Variance ratio criterion (higher is better)
        """
        # Check cache first
        cache_key = f"eval_{id(self._X_fitted)}_{self.n_clusters}"
        if cache_key in self._evaluation_cache:
            return self._evaluation_cache[cache_key]

        logger.info("Evaluating clustering quality...")

        metrics = {
            'inertia': float(self.inertia_),
            'n_clusters': self.n_clusters,
            'n_samples': len(self._X_fitted)
        }

        # Calculate silhouette score
        if 1 < self.n_clusters < len(self._X_fitted):
            try:
                silhouette = silhouette_score(self._X_fitted, self.labels_)
                metrics['silhouette_score'] = float(silhouette)
            except Exception as e:
                logger.warning(f"Could not calculate silhouette score: {e}")
                metrics['silhouette_score'] = None

            try:
                db_score = davies_bouldin_score(self._X_fitted, self.labels_)
                metrics['davies_bouldin_score'] = float(db_score)
            except Exception as e:
                logger.warning(f"Could not calculate Davies-Bouldin score: {e}")
                metrics['davies_bouldin_score'] = None

            try:
                ch_score = calinski_harabasz_score(self._X_fitted, self.labels_)
                metrics['calinski_harabasz_score'] = float(ch_score)
            except Exception as e:
                logger.warning(f"Could not calculate Calinski-Harabasz score: {e}")
                metrics['calinski_harabasz_score'] = None

        # Cache results
        self._evaluation_cache[cache_key] = metrics
        logger.success("Clustering evaluation completed")

        return metrics

    def _evaluate_single_k(
        self,
        X_scaled: np.ndarray,
        k: int
    ) -> Tuple[int, Dict[str, float]]:
        """Evaluate a single K value (for parallel processing).

        Args:
            X_scaled: Scaled feature data
            k: Number of clusters to test

        Returns:
            Tuple of (k, metrics dict)
        """
        kmeans = KMeans(
            n_clusters=k,
            random_state=self.random_state,
            max_iter=self.max_iter,
            n_init=self.n_init
        )

        labels = kmeans.fit_predict(X_scaled)

        metrics = {
            'inertia': float(kmeans.inertia_),
            'n_clusters': k
        }

        # Silhouette score
        if k > 1:
            try:
                metrics['silhouette_score'] = float(silhouette_score(X_scaled, labels))
            except Exception:
                metrics['silhouette_score'] = None

            try:
                metrics['davies_bouldin_score'] = float(davies_bouldin_score(X_scaled, labels))
            except Exception:
                metrics['davies_bouldin_score'] = None

            try:
                metrics['calinski_harabasz_score'] = float(calinski_harabasz_score(X_scaled, labels))
            except Exception:
                metrics['calinski_harabasz_score'] = None

        return k, metrics

    def find_optimal_clusters(
        self,
        df: pd.DataFrame,
        feature_columns: List[str],
        k_range: Optional[List[int]] = None,
        scale_features: bool = True,
        parallel: bool = True,
        n_workers: int = 4
    ) -> Dict[int, Dict[str, float]]:
        """Find optimal number of clusters using elbow method and silhouette analysis.

        This method supports parallel processing for faster evaluation of multiple K values.

        Args:
            df: DataFrame containing features
            feature_columns: List of columns to use for clustering
            k_range: Range of K values to try (default: 2 to 10)
            scale_features: Whether to scale features
            parallel: Whether to use parallel processing
            n_workers: Number of parallel workers

        Returns:
            Dictionary with metrics for each K value, including recommended K
        """
        if k_range is None:
            k_range = list(range(2, 11))

        # Validate k_range
        if not k_range:
            raise ValidationError("k_range cannot be empty")
        if min(k_range) < 2:
            raise ValidationError("Minimum K must be at least 2")
        if max(k_range) >= len(df):
            raise ValidationError(f"Maximum K ({max(k_range)}) must be less than number of samples ({len(df)})")

        logger.info(f"Finding optimal number of clusters for K in {k_range}...")

        # Prepare data
        X = df[feature_columns].copy()
        if X.isnull().any().any():
            X = X.fillna(X.median())

        if scale_features:
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
        else:
            X_scaled = X.values

        results = {}

        if parallel and len(k_range) > 2:
            # Parallel processing
            logger.info(f"Using parallel processing with {n_workers} workers")
            with ThreadPoolExecutor(max_workers=n_workers) as executor:
                futures = {
                    executor.submit(self._evaluate_single_k, X_scaled, k): k
                    for k in k_range
                }

                for future in as_completed(futures):
                    k, metrics = future.result()
                    results[k] = metrics
                    logger.debug(f"Completed K={k}")
        else:
            # Sequential processing
            for k in k_range:
                logger.info(f"Testing K = {k}...")
                _, metrics = self._evaluate_single_k(X_scaled, k)
                results[k] = metrics

        # Recommend optimal K based on silhouette score
        silhouette_scores = {
            k: v.get('silhouette_score', 0) or 0
            for k, v in results.items()
        }
        if silhouette_scores:
            optimal_k = max(silhouette_scores, key=silhouette_scores.get)
            for k in results:
                results[k]['is_recommended'] = (k == optimal_k)

        logger.success(f"Optimal cluster search completed. Recommended K={optimal_k}")

        return results

    def get_cluster_distribution(self, cluster_labels: Optional[np.ndarray] = None) -> pd.DataFrame:
        """Get distribution of samples across clusters.

        Args:
            cluster_labels: Cluster labels (uses fitted labels if None)

        Returns:
            DataFrame with cluster distribution
        """
        if cluster_labels is None:
            if self.labels_ is None:
                raise ClusteringError("Model not fitted", algorithm="KMeans")
            cluster_labels = self.labels_

        distribution = pd.Series(cluster_labels).value_counts().sort_index()

        df = pd.DataFrame({
            'Cluster': distribution.index,
            'Count': distribution.values,
            'Percentage': (distribution.values / len(cluster_labels) * 100).round(2)
        })

        return df

    def assign_cluster_names(
        self,
        cluster_names: Dict[int, str]
    ) -> Dict[int, str]:
        """Assign custom names to clusters.

        Args:
            cluster_names: Dictionary mapping cluster IDs to names

        Returns:
            Cluster name mapping
        """
        self.cluster_names = cluster_names
        logger.info(f"Assigned names to {len(cluster_names)} clusters")
        return cluster_names

    def get_feature_importance(self) -> pd.DataFrame:
        """Calculate feature importance based on cluster centers variance.

        Returns:
            DataFrame with feature importance scores
        """
        if self.model is None:
            raise ClusteringError("Model not fitted", algorithm="KMeans")

        centers = self.model.cluster_centers_

        # Calculate variance of each feature across cluster centers
        feature_variance = np.var(centers, axis=0)

        # Normalize to get importance scores
        importance = feature_variance / feature_variance.sum()

        return pd.DataFrame({
            'feature': self.feature_columns,
            'importance': importance,
            'variance': feature_variance
        }).sort_values('importance', ascending=False)

    def to_dict(self) -> Dict[str, Any]:
        """Export clusterer configuration as dictionary.

        Returns:
            Dictionary with clusterer configuration
        """
        base_dict = super().to_dict()
        base_dict.update({
            'n_clusters': self.n_clusters,
            'max_iter': self.max_iter,
            'n_init': self.n_init,
            'inertia': self.inertia_
        })
        return base_dict
