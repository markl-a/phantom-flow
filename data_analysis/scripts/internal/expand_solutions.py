"""Expand anomaly detection solutions to meet line requirements"""

# Read and count existing lines
base_path = "/home/user/Data-Analysis-with-Chatbots/kaggle_solutions/10_anomaly_detection"

# For solutions 17-30, add comprehensive implementations
expansions = {}

# Let's expand a few key solutions as examples
# The rest will follow similar patterns

expansions["19_dbscan_anomaly_detection"] = '''"""
DBSCAN for Anomaly Detection
============================

This solution uses DBSCAN clustering for anomaly detection:
1. DBSCAN noise points as anomalies
2. Parameter tuning (eps, min_samples)
3. HDBSCAN for hierarchical density-based detection
4. Cluster-based scoring

Author: Kaggle Solutions
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import DBSCAN
from sklearn.metrics import (
    roc_curve, auc, precision_recall_curve,
    f1_score, precision_score, recall_score,
    silhouette_score
)
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors
import warnings
warnings.filterwarnings('ignore')

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False
    print("Warning: hdbscan not available")


class DBSCANAnomalyDetector:
    """DBSCAN-based anomaly detector"""

    def __init__(self, eps=0.5, min_samples=5):
        self.eps = eps
        self.min_samples = min_samples
        self.dbscan_ = None
        self.labels_ = None

    def fit(self, X):
        """Fit DBSCAN"""
        self.dbscan_ = DBSCAN(eps=self.eps, min_samples=self.min_samples)
        self.labels_ = self.dbscan_.fit_predict(X)
        return self

    def predict(self, X):
        """Predict anomalies (noise points = -1 in DBSCAN)"""
        # For new data, use nearest neighbor to assign
        if hasattr(self.dbscan_, 'components_'):
            # Use core samples to predict
            nn = NearestNeighbors(n_neighbors=self.min_samples, radius=self.eps)
            nn.fit(self.dbscan_.components_)
            
            distances, indices = nn.kneighbors(X)
            
            # If average distance > eps, likely anomaly
            predictions = (distances.mean(axis=1) > self.eps).astype(int)
        else:
            # Simple approach: refit on combined data
            combined = np.vstack([self.dbscan_.components_ if hasattr(self.dbscan_, 'components_') else X, X])
            labels = self.dbscan_.fit_predict(combined)
            predictions = (labels[-len(X):] == -1).astype(int)
        
        return predictions

    def decision_function(self, X):
        """Return anomaly scores based on distance to nearest cluster"""
        if hasattr(self.dbscan_, 'components_'):
            nn = NearestNeighbors(n_neighbors=min(self.min_samples, len(self.dbscan_.components_)))
            nn.fit(self.dbscan_.components_)
            distances, _ = nn.kneighbors(X)
            return distances.mean(axis=1)
        else:
            return np.ones(len(X))

    def fit_predict(self, X):
        """Fit and predict"""
        self.fit(X)
        return (self.labels_ == -1).astype(int)


class AdaptiveDBSCANDetector:
    """DBSCAN with adaptive epsilon selection"""

    def __init__(self, min_samples=5, k=4):
        self.min_samples = min_samples
        self.k = k
        self.eps_ = None
        self.dbscan_ = None

    def _estimate_eps(self, X):
        """Estimate eps using k-distance plot"""
        nn = NearestNeighbors(n_neighbors=self.k)
        nn.fit(X)
        distances, _ = nn.kneighbors(X)
        
        # Use k-th nearest neighbor distance
        k_distances = distances[:, -1]
        k_distances = np.sort(k_distances)
        
        # Find elbow point (simplified)
        # Use knee of k-distance graph
        diffs = np.diff(k_distances)
        knee_idx = np.argmax(diffs)
        
        return k_distances[knee_idx]

    def fit(self, X):
        """Fit with adaptive eps"""
        self.eps_ = self._estimate_eps(X)
        self.dbscan_ = DBSCANAnomalyDetector(eps=self.eps_, min_samples=self.min_samples)
        self.dbscan_.fit(X)
        return self

    def predict(self, X):
        """Predict anomalies"""
        return self.dbscan_.predict(X)

    def decision_function(self, X):
        """Return anomaly scores"""
        return self.dbscan_.decision_function(X)


class HDBSCANDetector:
    """HDBSCAN-based detector (if available)"""

    def __init__(self, min_cluster_size=5, min_samples=None):
        self.min_cluster_size = min_cluster_size
        self.min_samples = min_samples
        self.clusterer_ = None

    def fit(self, X):
        """Fit HDBSCAN"""
        if not HDBSCAN_AVAILABLE:
            raise ImportError("hdbscan not available")
        
        self.clusterer_ = hdbscan.HDBSCAN(
            min_cluster_size=self.min_cluster_size,
            min_samples=self.min_samples
        )
        self.clusterer_.fit(X)
        return self

    def predict(self, X):
        """Predict using outlier scores"""
        if hasattr(self.clusterer_, 'outlier_scores_'):
            # For training data
            if len(X) == len(self.clusterer_.outlier_scores_):
                threshold = np.percentile(self.clusterer_.outlier_scores_, 90)
                return (self.clusterer_.outlier_scores_ > threshold).astype(int)
        
        # For new data, use labels
        labels = self.clusterer_.labels_
        return (labels == -1).astype(int)

    def decision_function(self, X):
        """Return outlier scores"""
        if hasattr(self.clusterer_, 'outlier_scores_'):
            return self.clusterer_.outlier_scores_
        else:
            return np.ones(len(X))


def generate_clustered_anomaly_data(n_samples=1000, n_features=8, contamination=0.1):
    """Generate data with clear clusters and anomalies"""
    n_normal = int(n_samples * (1 - contamination))
    n_anomalies = n_samples - n_normal
    
    # Create well-separated clusters
    n_clusters = 3
    samples_per_cluster = n_normal // n_clusters
    
    X_normal = []
    cluster_centers = []
    
    for i in range(n_clusters):
        # Random center, well separated
        center = np.random.randn(n_features) * 5
        cluster_centers.append(center)
        
        # Compact cluster
        cluster = np.random.randn(samples_per_cluster, n_features) * 0.5 + center
        X_normal.append(cluster)
    
    X_normal = np.vstack(X_normal)
    
    # Anomalies - scattered points
    X_anomalies = np.random.uniform(-15, 15, (n_anomalies, n_features))
    
    # Combine
    X = np.vstack([X_normal, X_anomalies])
    y = np.hstack([np.zeros(n_normal), np.ones(n_anomalies)])
    
    # Shuffle
    indices = np.random.permutation(len(X))
    return X[indices], y[indices]


def tune_dbscan_parameters(X, eps_range, min_samples_range):
    """Tune DBSCAN parameters"""
    results = []
    
    for eps in eps_range:
        for min_samples in min_samples_range:
            dbscan = DBSCAN(eps=eps, min_samples=min_samples)
            labels = dbscan.fit_predict(X)
            
            n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
            n_noise = list(labels).count(-1)
            
            # Calculate silhouette score if there are clusters
            if n_clusters > 1 and n_noise < len(X):
                try:
                    silhouette = silhouette_score(X, labels)
                except ValueError:
                    silhouette = -1
            else:
                silhouette = -1
            
            results.append({
                'eps': eps,
                'min_samples': min_samples,
                'n_clusters': n_clusters,
                'n_noise': n_noise,
                'noise_ratio': n_noise / len(X),
                'silhouette': silhouette
            })
    
    return pd.DataFrame(results)


def plot_k_distance(X, k=4):
    """Plot k-distance graph for eps selection"""
    nn = NearestNeighbors(n_neighbors=k)
    nn.fit(X)
    distances, _ = nn.kneighbors(X)
    
    k_distances = np.sort(distances[:, -1])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.plot(range(len(k_distances)), k_distances, 'b-', linewidth=2)
    
    # Estimate knee
    diffs = np.diff(k_distances)
    knee_idx = np.argmax(diffs)
    knee_value = k_distances[knee_idx]
    
    ax.axhline(knee_value, color='red', linestyle='--',
              label=f'Estimated eps: {knee_value:.3f}')
    ax.scatter([knee_idx], [knee_value], color='red', s=100, zorder=5)
    
    ax.set_xlabel('Points sorted by distance', fontsize=12)
    ax.set_ylabel(f'{k}-th Nearest Neighbor Distance', fontsize=12)
    ax.set_title('K-Distance Plot for Eps Selection', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_dbscan_clusters_2d(X, labels, title="DBSCAN Clustering"):
    """Visualize DBSCAN clustering in 2D"""
    fig, ax = plt.subplots(figsize=(10, 8))
    
    # Unique cluster labels
    unique_labels = set(labels)
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
    
    for k, col in zip(unique_labels, colors):
        if k == -1:
            # Noise points (anomalies)
            col = 'red'
            marker = 'x'
            size = 100
            label = 'Anomalies'
        else:
            marker = 'o'
            size = 50
            label = f'Cluster {k}'
        
        class_member_mask = (labels == k)
        xy = X[class_member_mask]
        
        ax.scatter(xy[:, 0], xy[:, 1], c=[col], marker=marker,
                  s=size, alpha=0.6, label=label)
    
    ax.set_xlabel('Feature 1', fontsize=12)
    ax.set_ylabel('Feature 2', fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_parameter_heatmap(results_df):
    """Plot heatmap of parameter tuning results"""
    # Pivot for heatmap
    pivot_silhouette = results_df.pivot(index='min_samples', columns='eps',
                                       values='silhouette')
    pivot_noise = results_df.pivot(index='min_samples', columns='eps',
                                   values='noise_ratio')
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Silhouette score heatmap
    sns.heatmap(pivot_silhouette, annot=True, fmt='.3f', cmap='RdYlGn',
               ax=ax1, cbar_kws={'label': 'Silhouette Score'})
    ax1.set_title('Silhouette Score by Parameters', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Eps', fontsize=12)
    ax1.set_ylabel('Min Samples', fontsize=12)
    
    # Noise ratio heatmap
    sns.heatmap(pivot_noise, annot=True, fmt='.3f', cmap='YlOrRd',
               ax=ax2, cbar_kws={'label': 'Noise Ratio'})
    ax2.set_title('Noise Ratio by Parameters', fontsize=14, fontweight='bold')
    ax2.set_xlabel('Eps', fontsize=12)
    ax2.set_ylabel('Min Samples', fontsize=12)
    
    plt.tight_layout()
    return fig


def plot_roc_pr_curves(detectors, X_test, y_test, names):
    """Plot ROC and PR curves"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    colors = ['blue', 'green', 'red', 'purple', 'orange']
    
    for i, (detector, name) in enumerate(zip(detectors, names)):
        scores = detector.decision_function(X_test)
        
        fpr, tpr, _ = roc_curve(y_test, scores)
        roc_auc = auc(fpr, tpr)
        ax1.plot(fpr, tpr, color=colors[i % len(colors)], lw=2,
                label=f'{name} (AUC={roc_auc:.3f})')
        
        precision, recall, _ = precision_recall_curve(y_test, scores)
        pr_auc = auc(recall, precision)
        ax2.plot(recall, precision, color=colors[i % len(colors)], lw=2,
                label=f'{name} (AUC={pr_auc:.3f})')
    
    ax1.plot([0, 1], [0, 1], 'k--', lw=1)
    ax1.set_xlabel('False Positive Rate', fontsize=12)
    ax1.set_ylabel('True Positive Rate', fontsize=12)
    ax1.set_title('ROC Curves', fontsize=14, fontweight='bold')
    ax1.legend(loc='lower right')
    ax1.grid(True, alpha=0.3)
    
    ax2.set_xlabel('Recall', fontsize=12)
    ax2.set_ylabel('Precision', fontsize=12)
    ax2.set_title('Precision-Recall Curves', fontsize=14, fontweight='bold')
    ax2.legend(loc='best')
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def evaluate_detector(detector, X_test, y_test, name):
    """Evaluate detector"""
    y_pred = detector.predict(X_test)
    scores = detector.decision_function(X_test)
    
    f1 = f1_score(y_test, y_pred)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    
    fpr, tpr, _ = roc_curve(y_test, scores)
    roc_auc = auc(fpr, tpr)
    
    prec_curve, rec_curve, _ = precision_recall_curve(y_test, scores)
    pr_auc = auc(rec_curve, prec_curve)
    
    return {
        'Detector': name,
        'F1 Score': f1,
        'Precision': precision,
        'Recall': recall,
        'ROC AUC': roc_auc,
        'PR AUC': pr_auc
    }


def main():
    """Main execution function"""
    print("=" * 80)
    print("DBSCAN for Anomaly Detection")
    print("=" * 80)
    
    np.random.seed(42)
    
    # Generate data
    print("\\n1. Generating synthetic data...")
    X, y = generate_clustered_anomaly_data(n_samples=1500, n_features=8, contamination=0.12)
    print(f"   Dataset shape: {X.shape}")
    print(f"   Anomaly ratio: {y.sum() / len(y):.3f}")
    
    # Normalize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.3, random_state=42, stratify=y
    )
    
    # Parameter tuning
    print("\\n2. Tuning DBSCAN parameters...")
    eps_range = np.linspace(0.3, 1.5, 10)
    min_samples_range = [3, 5, 7, 10]
    
    tuning_results = tune_dbscan_parameters(X_train, eps_range, min_samples_range)
    
    # Find best parameters (maximize silhouette, target noise ratio around 0.1)
    valid_results = tuning_results[tuning_results['silhouette'] > 0]
    if len(valid_results) > 0:
        valid_results['score'] = valid_results['silhouette'] - abs(valid_results['noise_ratio'] - 0.12) * 2
        best_params = valid_results.loc[valid_results['score'].idxmax()]
        best_eps = best_params['eps']
        best_min_samples = int(best_params['min_samples'])
    else:
        best_eps = 0.5
        best_min_samples = 5
    
    print(f"   Best parameters: eps={best_eps:.3f}, min_samples={best_min_samples}")
    
    # K-distance plot
    print("\\n3. Analyzing K-distance for eps selection...")
    fig = plot_k_distance(X_train, k=4)
    plt.savefig('dbscan_k_distance.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Parameter heatmap
    fig = plot_parameter_heatmap(tuning_results)
    plt.savefig('dbscan_parameter_tuning.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Train detectors
    print("\\n4. Training DBSCAN detectors...")
    detectors = {
        f'DBSCAN (tuned)': DBSCANAnomalyDetector(eps=best_eps, min_samples=best_min_samples),
        'DBSCAN (eps=0.5)': DBSCANAnomalyDetector(eps=0.5, min_samples=5),
        'Adaptive DBSCAN': AdaptiveDBSCANDetector(min_samples=5, k=4),
    }
    
    if HDBSCAN_AVAILABLE:
        detectors['HDBSCAN'] = HDBSCANDetector(min_cluster_size=5)
    
    for name, detector in detectors.items():
        detector.fit(X_train)
        print(f"   {name} trained")
    
    # Visualize clusters
    labels = detectors[f'DBSCAN (tuned)'].labels_
    fig = plot_dbscan_clusters_2d(X_train, labels, "DBSCAN Clustering (Training Data)")
    plt.savefig('dbscan_clusters_2d.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Evaluate
    print("\\n5. Evaluating detectors...")
    results = []
    for name, detector in detectors.items():
        result = evaluate_detector(detector, X_test, y_test, name)
        results.append(result)
        print(f"   {name}: F1={result['F1 Score']:.3f}, "
              f"Precision={result['Precision']:.3f}, "
              f"Recall={result['Recall']:.3f}")
    
    results_df = pd.DataFrame(results)
    
    # ROC and PR curves
    print("\\n6. Creating visualizations...")
    detector_list = list(detectors.values())
    names_list = list(detectors.keys())
    fig = plot_roc_pr_curves(detector_list, X_test, y_test, names_list)
    plt.savefig('dbscan_roc_pr_curves.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Final results
    print("\\n7. Final Performance Comparison:")
    print("\\n" + "="*80)
    print(results_df.to_string(index=False))
    print("="*80)
    
    results_df.to_csv('dbscan_detection_results.csv', index=False)
    print("\\nResults saved!")
    print("\\n" + "="*80)
    print("Analysis complete!")
    print("="*80)


if __name__ == "__main__":
    main()
'''

# Write the expansion
with open(f"{base_path}/19_dbscan_anomaly_detection/solution.py", 'w') as f:
    f.write(expansions["19_dbscan_anomaly_detection"])

print("Solution 19 expanded successfully!")
print(f"New line count: {len(expansions['19_dbscan_anomaly_detection'].splitlines())}")

