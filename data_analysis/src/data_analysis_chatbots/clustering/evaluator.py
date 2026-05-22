"""Clustering evaluation utilities.

This module provides comprehensive clustering evaluation tools including
multiple validation metrics, visualization helpers, and comparison utilities.
"""

from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.metrics import (
    silhouette_score,
    silhouette_samples,
    davies_bouldin_score,
    calinski_harabasz_score,
    adjusted_rand_score,
    normalized_mutual_info_score,
    homogeneity_score,
    completeness_score,
    v_measure_score
)

from ..exceptions import ValidationError, ClusteringError


class ClusteringEvaluator:
    """Comprehensive clustering evaluation utility.

    This class provides methods to evaluate clustering quality using
    multiple metrics, compare different clustering solutions, and
    generate detailed evaluation reports.

    Attributes:
        X: Feature data used for evaluation
        labels: Cluster labels
        true_labels: Ground truth labels (if available)

    Example:
        >>> evaluator = ClusteringEvaluator(X_scaled, cluster_labels)
        >>> metrics = evaluator.evaluate_all()
        >>> print(f"Silhouette Score: {metrics['silhouette_score']:.3f}")
        >>> report = evaluator.generate_report()
    """

    def __init__(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        true_labels: Optional[np.ndarray] = None
    ):
        """Initialize the clustering evaluator.

        Args:
            X: Feature data (n_samples, n_features)
            labels: Predicted cluster labels
            true_labels: Ground truth labels (optional, for external validation)

        Raises:
            ValidationError: If input data is invalid
        """
        if X.shape[0] != len(labels):
            raise ValidationError(
                f"X and labels must have same number of samples. "
                f"Got X: {X.shape[0]}, labels: {len(labels)}"
            )

        if true_labels is not None and len(true_labels) != len(labels):
            raise ValidationError(
                f"true_labels must have same length as labels. "
                f"Got true_labels: {len(true_labels)}, labels: {len(labels)}"
            )

        self.X = X
        self.labels = labels
        self.true_labels = true_labels
        self._cache: Dict[str, Any] = {}

    @property
    def n_clusters(self) -> int:
        """Number of unique clusters (excluding noise points)."""
        unique_labels = set(self.labels)
        return len(unique_labels) - (1 if -1 in unique_labels else 0)

    @property
    def n_samples(self) -> int:
        """Number of samples."""
        return len(self.labels)

    @property
    def has_noise(self) -> bool:
        """Check if there are noise points (label -1)."""
        return -1 in self.labels

    def _check_valid_for_metrics(self) -> bool:
        """Check if clustering is valid for computing metrics."""
        return 1 < self.n_clusters < self.n_samples

    def silhouette(self, sample_scores: bool = False) -> float | np.ndarray:
        """Calculate silhouette score.

        The silhouette score measures how similar samples are to their own
        cluster compared to other clusters. Range: [-1, 1], higher is better.

        Args:
            sample_scores: If True, return per-sample scores

        Returns:
            Silhouette score (float) or per-sample scores (array)
        """
        if not self._check_valid_for_metrics():
            logger.warning("Cannot compute silhouette score: invalid clustering")
            return np.nan

        try:
            if sample_scores:
                return silhouette_samples(self.X, self.labels)
            return float(silhouette_score(self.X, self.labels))
        except Exception as e:
            logger.warning(f"Failed to compute silhouette score: {e}")
            return np.nan

    def davies_bouldin(self) -> float:
        """Calculate Davies-Bouldin index.

        Measures the average similarity between clusters. Lower is better.
        Range: [0, inf)

        Returns:
            Davies-Bouldin index
        """
        if not self._check_valid_for_metrics():
            logger.warning("Cannot compute Davies-Bouldin index: invalid clustering")
            return np.nan

        try:
            return float(davies_bouldin_score(self.X, self.labels))
        except Exception as e:
            logger.warning(f"Failed to compute Davies-Bouldin index: {e}")
            return np.nan

    def calinski_harabasz(self) -> float:
        """Calculate Calinski-Harabasz index (Variance Ratio Criterion).

        Ratio of between-cluster dispersion to within-cluster dispersion.
        Higher is better.

        Returns:
            Calinski-Harabasz index
        """
        if not self._check_valid_for_metrics():
            logger.warning("Cannot compute Calinski-Harabasz index: invalid clustering")
            return np.nan

        try:
            return float(calinski_harabasz_score(self.X, self.labels))
        except Exception as e:
            logger.warning(f"Failed to compute Calinski-Harabasz index: {e}")
            return np.nan

    def inertia(self, cluster_centers: Optional[np.ndarray] = None) -> float:
        """Calculate inertia (sum of squared distances to cluster centers).

        Args:
            cluster_centers: Pre-computed cluster centers (optional)

        Returns:
            Inertia value
        """
        if cluster_centers is None:
            # Compute centers from data
            cluster_centers = np.array([
                self.X[self.labels == k].mean(axis=0)
                for k in range(self.n_clusters)
            ])

        inertia = 0.0
        for k in range(self.n_clusters):
            cluster_points = self.X[self.labels == k]
            if len(cluster_points) > 0:
                distances = np.sum((cluster_points - cluster_centers[k]) ** 2)
                inertia += distances

        return float(inertia)

    def external_metrics(self) -> Dict[str, float]:
        """Calculate external validation metrics (requires true labels).

        Returns metrics that compare clustering with ground truth labels.

        Returns:
            Dictionary with external validation metrics

        Raises:
            ValidationError: If true_labels not provided
        """
        if self.true_labels is None:
            raise ValidationError("true_labels required for external validation")

        return {
            'adjusted_rand_index': float(adjusted_rand_score(
                self.true_labels, self.labels
            )),
            'normalized_mutual_info': float(normalized_mutual_info_score(
                self.true_labels, self.labels
            )),
            'homogeneity': float(homogeneity_score(
                self.true_labels, self.labels
            )),
            'completeness': float(completeness_score(
                self.true_labels, self.labels
            )),
            'v_measure': float(v_measure_score(
                self.true_labels, self.labels
            ))
        }

    def cluster_sizes(self) -> Dict[int, int]:
        """Get the size of each cluster.

        Returns:
            Dictionary mapping cluster ID to size
        """
        unique, counts = np.unique(self.labels, return_counts=True)
        return {int(k): int(v) for k, v in zip(unique, counts)}

    def cluster_statistics(self) -> pd.DataFrame:
        """Calculate statistics for each cluster.

        Returns:
            DataFrame with cluster statistics (size, percentage, avg silhouette)
        """
        sizes = self.cluster_sizes()
        total = self.n_samples

        stats = []
        sample_silhouettes = self.silhouette(sample_scores=True)

        for cluster_id in sorted(sizes.keys()):
            size = sizes[cluster_id]
            mask = self.labels == cluster_id

            cluster_stats = {
                'cluster': cluster_id,
                'size': size,
                'percentage': size / total * 100,
            }

            if isinstance(sample_silhouettes, np.ndarray):
                cluster_stats['avg_silhouette'] = float(sample_silhouettes[mask].mean())

            stats.append(cluster_stats)

        return pd.DataFrame(stats)

    def evaluate_all(self, include_external: bool = True) -> Dict[str, Any]:
        """Evaluate clustering using all available metrics.

        Args:
            include_external: Include external metrics if true_labels available

        Returns:
            Dictionary with all computed metrics
        """
        metrics = {
            'n_clusters': self.n_clusters,
            'n_samples': self.n_samples,
            'has_noise': self.has_noise,
            'silhouette_score': self.silhouette(),
            'davies_bouldin_score': self.davies_bouldin(),
            'calinski_harabasz_score': self.calinski_harabasz(),
            'cluster_sizes': self.cluster_sizes()
        }

        if include_external and self.true_labels is not None:
            metrics['external'] = self.external_metrics()

        return metrics

    def compare_with(
        self,
        other_labels: np.ndarray,
        name: str = "alternative"
    ) -> Dict[str, Dict[str, float]]:
        """Compare current clustering with another solution.

        Args:
            other_labels: Alternative cluster labels to compare with
            name: Name for the alternative clustering

        Returns:
            Dictionary comparing metrics between the two clusterings
        """
        current_metrics = {
            'silhouette': self.silhouette(),
            'davies_bouldin': self.davies_bouldin(),
            'calinski_harabasz': self.calinski_harabasz(),
            'n_clusters': self.n_clusters
        }

        other_evaluator = ClusteringEvaluator(self.X, other_labels)
        other_metrics = {
            'silhouette': other_evaluator.silhouette(),
            'davies_bouldin': other_evaluator.davies_bouldin(),
            'calinski_harabasz': other_evaluator.calinski_harabasz(),
            'n_clusters': other_evaluator.n_clusters
        }

        return {
            'current': current_metrics,
            name: other_metrics,
            'comparison': {
                'silhouette_diff': current_metrics['silhouette'] - other_metrics['silhouette'],
                'davies_bouldin_diff': other_metrics['davies_bouldin'] - current_metrics['davies_bouldin'],
                'calinski_harabasz_diff': current_metrics['calinski_harabasz'] - other_metrics['calinski_harabasz']
            }
        }

    def generate_report(self) -> str:
        """Generate a human-readable evaluation report.

        Returns:
            Formatted string report
        """
        metrics = self.evaluate_all()
        cluster_stats = self.cluster_statistics()

        lines = [
            "=" * 60,
            "CLUSTERING EVALUATION REPORT",
            "=" * 60,
            "",
            "Summary:",
            f"  Number of clusters: {metrics['n_clusters']}",
            f"  Number of samples: {metrics['n_samples']}",
            f"  Contains noise points: {metrics['has_noise']}",
            "",
            "Internal Validation Metrics:",
            f"  Silhouette Score: {metrics['silhouette_score']:.4f} (range: -1 to 1, higher is better)",
            f"  Davies-Bouldin Index: {metrics['davies_bouldin_score']:.4f} (lower is better)",
            f"  Calinski-Harabasz Index: {metrics['calinski_harabasz_score']:.4f} (higher is better)",
            "",
            "Cluster Distribution:",
        ]

        for _, row in cluster_stats.iterrows():
            cluster_name = "Noise" if row['cluster'] == -1 else f"Cluster {int(row['cluster'])}"
            line = f"  {cluster_name}: {int(row['size'])} samples ({row['percentage']:.1f}%)"
            if 'avg_silhouette' in row:
                line += f" | Avg Silhouette: {row['avg_silhouette']:.4f}"
            lines.append(line)

        if 'external' in metrics:
            lines.extend([
                "",
                "External Validation Metrics:",
                f"  Adjusted Rand Index: {metrics['external']['adjusted_rand_index']:.4f}",
                f"  Normalized Mutual Info: {metrics['external']['normalized_mutual_info']:.4f}",
                f"  V-Measure: {metrics['external']['v_measure']:.4f}",
            ])

        lines.extend(["", "=" * 60])

        return "\n".join(lines)


def find_optimal_k(
    X: np.ndarray,
    k_range: List[int],
    method: str = 'silhouette',
    n_init: int = 10,
    random_state: int = 42,
    parallel: bool = True,
    n_workers: int = 4
) -> Tuple[int, Dict[int, Dict[str, float]]]:
    """Find optimal number of clusters using elbow method or silhouette analysis.

    Args:
        X: Feature data
        k_range: Range of K values to evaluate
        method: Optimization method ('silhouette', 'elbow', 'calinski')
        n_init: Number of K-means initializations
        random_state: Random seed
        parallel: Use parallel processing
        n_workers: Number of parallel workers

    Returns:
        Tuple of (optimal_k, results_dict)
    """
    from sklearn.cluster import KMeans

    def evaluate_k(k: int) -> Tuple[int, Dict[str, float]]:
        kmeans = KMeans(
            n_clusters=k,
            n_init=n_init,
            random_state=random_state
        )
        labels = kmeans.fit_predict(X)

        metrics = {
            'inertia': float(kmeans.inertia_),
            'n_clusters': k
        }

        if k > 1:
            try:
                metrics['silhouette_score'] = float(silhouette_score(X, labels))
            except Exception:
                metrics['silhouette_score'] = np.nan

            try:
                metrics['davies_bouldin_score'] = float(davies_bouldin_score(X, labels))
            except Exception:
                metrics['davies_bouldin_score'] = np.nan

            try:
                metrics['calinski_harabasz_score'] = float(calinski_harabasz_score(X, labels))
            except Exception:
                metrics['calinski_harabasz_score'] = np.nan

        return k, metrics

    results = {}

    if parallel and len(k_range) > 2:
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            futures = {executor.submit(evaluate_k, k): k for k in k_range}
            for future in as_completed(futures):
                k, metrics = future.result()
                results[k] = metrics
    else:
        for k in k_range:
            _, metrics = evaluate_k(k)
            results[k] = metrics

    # Find optimal K based on method
    if method == 'silhouette':
        scores = {k: v.get('silhouette_score', 0) or 0 for k, v in results.items()}
        optimal_k = max(scores, key=scores.get)
    elif method == 'calinski':
        scores = {k: v.get('calinski_harabasz_score', 0) or 0 for k, v in results.items()}
        optimal_k = max(scores, key=scores.get)
    else:  # elbow method
        inertias = {k: v['inertia'] for k, v in results.items()}
        # Simple elbow detection using second derivative
        k_values = sorted(inertias.keys())
        if len(k_values) >= 3:
            inertia_values = [inertias[k] for k in k_values]
            second_derivatives = []
            for i in range(1, len(inertia_values) - 1):
                d2 = inertia_values[i-1] - 2*inertia_values[i] + inertia_values[i+1]
                second_derivatives.append((k_values[i], d2))
            optimal_k = max(second_derivatives, key=lambda x: x[1])[0]
        else:
            optimal_k = k_values[len(k_values) // 2]

    # Mark recommended K
    for k in results:
        results[k]['is_recommended'] = (k == optimal_k)

    logger.info(f"Optimal K found: {optimal_k} (method: {method})")

    return optimal_k, results
