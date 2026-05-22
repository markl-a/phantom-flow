"""Script to generate remaining anomaly detection solutions"""

SOLUTIONS = {
    "15_knn_anomaly_detection": """\"\"\"
K-Nearest Neighbors (KNN) Anomaly Detection
==========================================

This solution implements KNN-based anomaly detection:
1. Distance to K-th nearest neighbor
2. Average distance to K nearest neighbors
3. Local distance-based outlier factor
4. Adaptive KNN with variable K

Author: Kaggle Solutions
\"\"\"

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics import (
    roc_curve, auc, precision_recall_curve,
    f1_score, precision_score, recall_score
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')


class KNNAnomalyDetector:
    \"\"\"KNN-based anomaly detector\"\"\"

    def __init__(self, n_neighbors=5, method='largest'):
        \"\"\"
        method: 'largest' (distance to k-th neighbor) or 'average' (avg distance)
        \"\"\"
        self.n_neighbors = n_neighbors
        self.method = method
        self.nn_ = None
        self.X_train_ = None

    def fit(self, X):
        \"\"\"Fit the detector\"\"\"
        self.X_train_ = X.copy()
        self.nn_ = NearestNeighbors(n_neighbors=self.n_neighbors + 1)
        self.nn_.fit(X)
        return self

    def predict(self, X):
        \"\"\"Predict anomalies\"\"\"
        scores = self.decision_function(X)
        threshold = np.percentile(scores, 95)
        return (scores > threshold).astype(int)

    def decision_function(self, X):
        \"\"\"Return anomaly scores\"\"\"
        distances, _ = self.nn_.kneighbors(X)
        
        # Exclude distance to self (0) for training data
        if np.allclose(X, self.X_train_[:len(X)]):
            distances = distances[:, 1:]
        
        if self.method == 'largest':
            return distances[:, -1]
        elif self.method == 'average':
            return np.mean(distances, axis=1)
        else:  # sum
            return np.sum(distances, axis=1)


class AdaptiveKNNDetector:
    \"\"\"Adaptive KNN with variable neighborhood size\"\"\"

    def __init__(self, k_range=(5, 50), n_estimators=10):
        self.k_range = k_range
        self.n_estimators = n_estimators
        self.detectors_ = []

    def fit(self, X):
        \"\"\"Fit multiple KNN detectors\"\"\"
        k_values = np.linspace(self.k_range[0], self.k_range[1], self.n_estimators, dtype=int)
        
        for k in k_values:
            detector = KNNAnomalyDetector(n_neighbors=k, method='average')
            detector.fit(X)
            self.detectors_.append(detector)
        
        return self

    def predict(self, X):
        \"\"\"Predict using ensemble\"\"\"
        scores = self.decision_function(X)
        threshold = np.percentile(scores, 90)
        return (scores > threshold).astype(int)

    def decision_function(self, X):
        \"\"\"Average scores from all detectors\"\"\"
        all_scores = np.array([d.decision_function(X) for d in self.detectors_])
        return np.mean(all_scores, axis=0)


class LocalDistanceOutlierDetector:
    \"\"\"Local distance-based outlier detector\"\"\"

    def __init__(self, n_neighbors=20, contamination=0.1):
        self.n_neighbors = n_neighbors
        self.contamination = contamination
        self.nn_ = None
        self.X_train_ = None

    def fit(self, X):
        \"\"\"Fit the detector\"\"\"
        self.X_train_ = X.copy()
        self.nn_ = NearestNeighbors(n_neighbors=self.n_neighbors + 1)
        self.nn_.fit(X)
        return self

    def predict(self, X):
        \"\"\"Predict anomalies\"\"\"
        scores = self.decision_function(X)
        threshold = np.percentile(scores, (1 - self.contamination) * 100)
        return (scores > threshold).astype(int)

    def decision_function(self, X):
        \"\"\"Compute local distance-based scores\"\"\"
        distances, indices = self.nn_.kneighbors(X)
        
        # For each point, compare its distance to neighbors
        # with the average distance of its neighbors to their neighbors
        scores = np.zeros(len(X))
        
        for i in range(len(X)):
            # Average distance to neighbors
            avg_dist = np.mean(distances[i, 1:])
            
            # Average distance of neighbors to their neighbors
            neighbor_dists = []
            for neighbor_idx in indices[i, 1:]:
                if neighbor_idx < len(self.X_train_):
                    neighbor_distances, _ = self.nn_.kneighbors([self.X_train_[neighbor_idx]])
                    neighbor_dists.append(np.mean(neighbor_distances[0, 1:]))
            
            if neighbor_dists:
                avg_neighbor_dist = np.mean(neighbor_dists)
                scores[i] = avg_dist / (avg_neighbor_dist + 1e-10)
            else:
                scores[i] = avg_dist
        
        return scores


def generate_anomaly_data(n_samples=1000, n_features=8, contamination=0.1):
    \"\"\"Generate synthetic data with anomalies\"\"\"
    n_normal = int(n_samples * (1 - contamination))
    n_anomalies = n_samples - n_normal
    
    # Normal data - multiple clusters
    n_clusters = 3
    samples_per_cluster = n_normal // n_clusters
    
    X_normal = []
    for i in range(n_clusters):
        center = np.random.randn(n_features) * 3
        cluster_data = np.random.randn(samples_per_cluster, n_features) + center
        X_normal.append(cluster_data)
    
    X_normal = np.vstack(X_normal)
    
    # Anomalies - isolated points
    X_anomalies = np.random.uniform(-10, 10, (n_anomalies, n_features))
    
    # Combine
    X = np.vstack([X_normal, X_anomalies])
    y = np.hstack([np.zeros(n_normal), np.ones(n_anomalies)])
    
    # Shuffle
    indices = np.random.permutation(len(X))
    return X[indices], y[indices]


def plot_knn_visualization_2d(X, y_true, detectors, names):
    \"\"\"Visualize KNN detection in 2D\"\"\"
    n_detectors = len(detectors)
    fig, axes = plt.subplots(1, n_detectors + 1, figsize=(5*(n_detectors+1), 5))
    
    # True labels
    axes[0].scatter(X[y_true == 0, 0], X[y_true == 0, 1],
                   c='blue', alpha=0.6, s=30, label='Normal')
    axes[0].scatter(X[y_true == 1, 0], X[y_true == 1, 1],
                   c='red', alpha=0.8, s=50, marker='^', label='Anomaly')
    axes[0].set_title('True Labels', fontsize=12, fontweight='bold')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    # Predictions
    for i, (detector, name) in enumerate(zip(detectors, names)):
        y_pred = detector.predict(X)
        
        axes[i+1].scatter(X[y_pred == 0, 0], X[y_pred == 0, 1],
                         c='blue', alpha=0.6, s=30, label='Normal')
        axes[i+1].scatter(X[y_pred == 1, 0], X[y_pred == 1, 1],
                         c='red', alpha=0.8, s=50, marker='^', label='Anomaly')
        
        f1 = f1_score(y_true, y_pred)
        axes[i+1].set_title(f'{name}\\nF1={f1:.3f}', fontsize=12, fontweight='bold')
        axes[i+1].legend()
        axes[i+1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_distance_distribution(X, detector, y_true):
    \"\"\"Plot distance distribution\"\"\"
    scores = detector.decision_function(X)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Separate scores by true label
    normal_scores = scores[y_true == 0]
    anomaly_scores = scores[y_true == 1]
    
    ax.hist(normal_scores, bins=50, alpha=0.7, color='blue',
           label='Normal', density=True)
    ax.hist(anomaly_scores, bins=50, alpha=0.7, color='red',
           label='Anomaly', density=True)
    
    ax.set_xlabel('Anomaly Score', fontsize=12)
    ax.set_ylabel('Density', fontsize=12)
    ax.set_title('KNN Distance Distribution', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_k_sensitivity(X_train, X_test, y_test, k_values):
    \"\"\"Plot performance vs K\"\"\"
    results = []
    
    for k in k_values:
        detector = KNNAnomalyDetector(n_neighbors=k, method='average')
        detector.fit(X_train)
        y_pred = detector.predict(X_test)
        
        results.append({
            'k': k,
            'f1': f1_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred)
        })
    
    results_df = pd.DataFrame(results)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.plot(results_df['k'], results_df['f1'], 'b-o', label='F1 Score', linewidth=2)
    ax.plot(results_df['k'], results_df['precision'], 'g--s', label='Precision')
    ax.plot(results_df['k'], results_df['recall'], 'r--^', label='Recall')
    
    ax.set_xlabel('Number of Neighbors (K)', fontsize=12)
    ax.set_ylabel('Score', fontsize=12)
    ax.set_title('KNN Performance vs K', fontsize=14, fontweight='bold')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    return fig


def plot_roc_pr_curves(detectors, X_test, y_test, names):
    \"\"\"Plot ROC and PR curves\"\"\"
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
    \"\"\"Evaluate detector\"\"\"
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
    \"\"\"Main execution function\"\"\"
    print("=" * 80)
    print("K-Nearest Neighbors (KNN) Anomaly Detection")
    print("=" * 80)
    
    np.random.seed(42)
    
    # Generate data
    print("\\n1. Generating synthetic data...")
    X, y = generate_anomaly_data(n_samples=1500, n_features=8, contamination=0.12)
    print(f"   Dataset shape: {X.shape}")
    print(f"   Anomaly ratio: {y.sum() / len(y):.3f}")
    
    # Normalize
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X_scaled, y, test_size=0.3, random_state=42, stratify=y
    )
    
    print("\\n2. Training KNN detectors...")
    detectors = {
        'KNN (k=5, largest)': KNNAnomalyDetector(n_neighbors=5, method='largest'),
        'KNN (k=10, average)': KNNAnomalyDetector(n_neighbors=10, method='average'),
        'KNN (k=20, average)': KNNAnomalyDetector(n_neighbors=20, method='average'),
        'Adaptive KNN': AdaptiveKNNDetector(k_range=(5, 50), n_estimators=10),
        'Local Distance': LocalDistanceOutlierDetector(n_neighbors=20, contamination=0.12)
    }
    
    for name, detector in detectors.items():
        detector.fit(X_train)
        print(f"   {name} trained")
    
    print("\\n3. Evaluating detectors...")
    results = []
    for name, detector in detectors.items():
        result = evaluate_detector(detector, X_test, y_test, name)
        results.append(result)
        print(f"   {name}: F1={result['F1 Score']:.3f}, "
              f"Precision={result['Precision']:.3f}, "
              f"Recall={result['Recall']:.3f}")
    
    results_df = pd.DataFrame(results)
    
    # Visualizations
    print("\\n4. Creating visualizations...")
    
    # K sensitivity analysis
    k_values = range(3, 51, 2)
    fig = plot_k_sensitivity(X_train, X_test, y_test, k_values)
    plt.savefig('knn_k_sensitivity.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Distance distribution
    fig = plot_distance_distribution(X_test, detectors['KNN (k=10, average)'], y_test)
    plt.savefig('knn_distance_distribution.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # 2D visualization
    detector_list = [detectors['KNN (k=5, largest)'],
                    detectors['KNN (k=20, average)'],
                    detectors['Adaptive KNN']]
    names_list = ['KNN k=5', 'KNN k=20', 'Adaptive']
    fig = plot_knn_visualization_2d(X_test, y_test, detector_list, names_list)
    plt.savefig('knn_2d_visualization.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # ROC and PR curves
    detector_list = list(detectors.values())
    names_list = list(detectors.keys())
    fig = plot_roc_pr_curves(detector_list, X_test, y_test, names_list)
    plt.savefig('knn_roc_pr_curves.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Final results
    print("\\n5. Final Performance Comparison:")
    print("\\n" + "="*80)
    print(results_df.to_string(index=False))
    print("="*80)
    
    results_df.to_csv('knn_detection_results.csv', index=False)
    print("\\nResults saved!")
    print("\\n" + "="*80)
    print("Analysis complete!")
    print("="*80)


if __name__ == "__main__":
    main()
""",
}

# Write the solution
for folder, content in SOLUTIONS.items():
    filepath = f"/home/user/Data-Analysis-with-Chatbots/kaggle_solutions/10_anomaly_detection/{folder}/solution.py"
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"Created {filepath}")

print("Done!")
