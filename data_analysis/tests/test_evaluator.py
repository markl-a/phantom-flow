"""Tests for clustering evaluator module."""

import pytest
import numpy as np
import pandas as pd
from sklearn.datasets import make_blobs

from data_analysis_chatbots.clustering import ClusteringEvaluator, find_optimal_k
from data_analysis_chatbots.exceptions import ValidationError


class TestClusteringEvaluator:
    """Tests for ClusteringEvaluator class."""

    @pytest.fixture
    def sample_clustering_data(self):
        """Create sample clustering data with known structure."""
        X, labels = make_blobs(
            n_samples=150,
            n_features=4,
            centers=3,
            cluster_std=1.0,
            random_state=42
        )
        return X, labels

    @pytest.fixture
    def evaluator(self, sample_clustering_data):
        """Create evaluator instance."""
        X, labels = sample_clustering_data
        return ClusteringEvaluator(X, labels)

    def test_initialization(self, sample_clustering_data):
        """Test evaluator initialization."""
        X, labels = sample_clustering_data
        evaluator = ClusteringEvaluator(X, labels)

        assert evaluator.n_clusters == 3
        assert evaluator.n_samples == 150
        assert not evaluator.has_noise

    def test_initialization_with_true_labels(self, sample_clustering_data):
        """Test initialization with ground truth labels."""
        X, labels = sample_clustering_data
        evaluator = ClusteringEvaluator(X, labels, true_labels=labels)

        assert evaluator.true_labels is not None

    def test_initialization_validation(self, sample_clustering_data):
        """Test validation on initialization."""
        X, labels = sample_clustering_data

        # Mismatched lengths
        with pytest.raises(ValidationError):
            ClusteringEvaluator(X, labels[:-10])

        # Mismatched true_labels
        with pytest.raises(ValidationError):
            ClusteringEvaluator(X, labels, true_labels=labels[:-10])

    def test_silhouette_score(self, evaluator):
        """Test silhouette score calculation."""
        score = evaluator.silhouette()

        assert isinstance(score, float)
        assert -1 <= score <= 1

    def test_silhouette_sample_scores(self, evaluator):
        """Test per-sample silhouette scores."""
        sample_scores = evaluator.silhouette(sample_scores=True)

        assert isinstance(sample_scores, np.ndarray)
        assert len(sample_scores) == evaluator.n_samples
        assert all(-1 <= s <= 1 for s in sample_scores)

    def test_davies_bouldin(self, evaluator):
        """Test Davies-Bouldin index calculation."""
        score = evaluator.davies_bouldin()

        assert isinstance(score, float)
        assert score >= 0

    def test_calinski_harabasz(self, evaluator):
        """Test Calinski-Harabasz index calculation."""
        score = evaluator.calinski_harabasz()

        assert isinstance(score, float)
        assert score >= 0

    def test_cluster_sizes(self, evaluator):
        """Test cluster size calculation."""
        sizes = evaluator.cluster_sizes()

        assert isinstance(sizes, dict)
        assert len(sizes) == 3
        assert sum(sizes.values()) == evaluator.n_samples

    def test_cluster_statistics(self, evaluator):
        """Test cluster statistics calculation."""
        stats = evaluator.cluster_statistics()

        assert isinstance(stats, pd.DataFrame)
        assert 'cluster' in stats.columns
        assert 'size' in stats.columns
        assert 'percentage' in stats.columns
        assert len(stats) == 3
        assert abs(stats['percentage'].sum() - 100) < 0.1

    def test_evaluate_all(self, evaluator):
        """Test comprehensive evaluation."""
        metrics = evaluator.evaluate_all()

        assert 'n_clusters' in metrics
        assert 'n_samples' in metrics
        assert 'silhouette_score' in metrics
        assert 'davies_bouldin_score' in metrics
        assert 'calinski_harabasz_score' in metrics
        assert 'cluster_sizes' in metrics

    def test_external_metrics(self, sample_clustering_data):
        """Test external validation metrics."""
        X, labels = sample_clustering_data
        evaluator = ClusteringEvaluator(X, labels, true_labels=labels)

        external = evaluator.external_metrics()

        assert 'adjusted_rand_index' in external
        assert 'normalized_mutual_info' in external
        assert 'homogeneity' in external
        assert 'completeness' in external
        assert 'v_measure' in external

        # With perfect clustering, scores should be 1.0
        assert external['adjusted_rand_index'] == pytest.approx(1.0)
        assert external['normalized_mutual_info'] == pytest.approx(1.0)

    def test_external_metrics_requires_true_labels(self, evaluator):
        """Test that external metrics require true_labels."""
        with pytest.raises(ValidationError):
            evaluator.external_metrics()

    def test_compare_with(self, sample_clustering_data):
        """Test comparison between clusterings."""
        X, labels = sample_clustering_data
        evaluator = ClusteringEvaluator(X, labels)

        # Create alternative labels
        other_labels = (labels + 1) % 3

        comparison = evaluator.compare_with(other_labels, "shuffled")

        assert 'current' in comparison
        assert 'shuffled' in comparison
        assert 'comparison' in comparison
        assert 'silhouette_diff' in comparison['comparison']

    def test_generate_report(self, evaluator):
        """Test report generation."""
        report = evaluator.generate_report()

        assert isinstance(report, str)
        assert "CLUSTERING EVALUATION REPORT" in report
        assert "Silhouette Score" in report
        assert "Davies-Bouldin Index" in report
        assert "Cluster Distribution" in report

    def test_noise_handling(self):
        """Test handling of noise points (label -1)."""
        np.random.seed(42)
        X = np.random.randn(100, 2)
        labels = np.array([0]*30 + [1]*30 + [-1]*40)

        evaluator = ClusteringEvaluator(X, labels)

        assert evaluator.has_noise
        assert evaluator.n_clusters == 2

        sizes = evaluator.cluster_sizes()
        assert -1 in sizes
        assert sizes[-1] == 40


class TestFindOptimalK:
    """Tests for find_optimal_k function."""

    @pytest.fixture
    def sample_data(self):
        """Create sample data for optimal K search."""
        X, _ = make_blobs(
            n_samples=100,
            n_features=3,
            centers=3,
            cluster_std=1.0,
            random_state=42
        )
        return X

    def test_find_optimal_k_silhouette(self, sample_data):
        """Test finding optimal K using silhouette method."""
        optimal_k, results = find_optimal_k(
            sample_data,
            k_range=[2, 3, 4, 5],
            method='silhouette',
            parallel=False
        )

        assert optimal_k in [2, 3, 4, 5]
        assert len(results) == 4
        assert results[optimal_k]['is_recommended'] is True

    def test_find_optimal_k_elbow(self, sample_data):
        """Test finding optimal K using elbow method."""
        optimal_k, results = find_optimal_k(
            sample_data,
            k_range=[2, 3, 4, 5],
            method='elbow',
            parallel=False
        )

        assert optimal_k in [2, 3, 4, 5]
        assert all('inertia' in v for v in results.values())

    def test_find_optimal_k_parallel(self, sample_data):
        """Test parallel processing for optimal K search."""
        optimal_k, results = find_optimal_k(
            sample_data,
            k_range=[2, 3, 4, 5],
            parallel=True,
            n_workers=2
        )

        assert len(results) == 4
        assert all('silhouette_score' in v for v in results.values())

    def test_find_optimal_k_metrics(self, sample_data):
        """Test that all metrics are computed."""
        _, results = find_optimal_k(
            sample_data,
            k_range=[2, 3, 4],
            parallel=False
        )

        for k, metrics in results.items():
            assert 'inertia' in metrics
            assert 'n_clusters' in metrics
            if k > 1:
                assert 'silhouette_score' in metrics
                assert 'davies_bouldin_score' in metrics
                assert 'calinski_harabasz_score' in metrics
