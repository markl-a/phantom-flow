"""聚類算法比較範例

此腳本展示如何使用和比較4種不同的聚類算法:
1. K-Means - 快速、適合球形聚類
2. DBSCAN - 發現任意形狀、自動檢測異常
3. GMM - 概率性軟聚類
4. Hierarchical - 層次結構可視化

使用方法:
    python examples/clustering_comparison.py

輸出:
    - 比較表格
    - 可視化圖表
    - 性能指標
"""

import sys
from pathlib import Path
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 添加專案根目錄到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from data_analysis_chatbots import DataLoader, setup_logging
from data_analysis_chatbots.clustering import (
    KMeansClusterer,
    DBSCANClusterer,
    GMMClusterer,
    HierarchicalClusterer
)

# 設置日誌
setup_logging(level="INFO")

# 設置繪圖樣式
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (15, 10)
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'DejaVu Sans']


def load_sample_data():
    """加載示例數據"""
    print("📦 加載數據集...")
    loader = DataLoader()

    try:
        df = loader.load_mall_customers()
        print(f"✓ 成功加載 {len(df)} 條記錄")
        return df
    except FileNotFoundError:
        print("⚠️  數據集未找到，使用生成的示例數據")
        # 生成示例數據
        from sklearn.datasets import make_blobs
        X, _ = make_blobs(n_samples=200, centers=4, random_state=42)
        df = pd.DataFrame(X, columns=['Feature1', 'Feature2'])
        df['Feature3'] = np.random.randn(200) * 20 + 50
        return df


def get_features(df):
    """獲取特徵列"""
    # 嘗試使用mall customers的特徵
    if all(col in df.columns for col in ['Age', 'Annual Income (k$)', 'Spending Score (1-100)']):
        return ['Age', 'Annual Income (k$)', 'Spending Score (1-100)']
    else:
        # 使用數值列
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        return numeric_cols[:3] if len(numeric_cols) >= 3 else numeric_cols


def run_kmeans(df, features, n_clusters=4):
    """運行K-Means聚類"""
    print("\n🔵 運行 K-Means 聚類...")
    start_time = time.time()

    clusterer = KMeansClusterer(n_clusters=n_clusters, random_state=42)
    labels = clusterer.fit_predict(df, features)
    summary = clusterer.get_cluster_summary(df, features)
    metrics = clusterer.evaluate_clustering(df, features)

    elapsed_time = time.time() - start_time
    metrics['execution_time'] = elapsed_time
    metrics['algorithm'] = 'K-Means'

    print(f"✓ 完成 (耗時: {elapsed_time:.2f}秒)")
    print(f"   聚類數: {n_clusters}")
    print(f"   Silhouette分數: {metrics.get('silhouette_score', 'N/A')}")

    return labels, summary, metrics, clusterer


def run_dbscan(df, features, eps=0.5, min_samples=5):
    """運行DBSCAN聚類"""
    print("\n🟢 運行 DBSCAN 聚類...")
    start_time = time.time()

    clusterer = DBSCANClusterer(eps=eps, min_samples=min_samples)
    labels = clusterer.fit_predict(df, features)
    summary = clusterer.get_cluster_summary(df, features)
    metrics = clusterer.evaluate_clustering(df, features)

    elapsed_time = time.time() - start_time
    metrics['execution_time'] = elapsed_time
    metrics['algorithm'] = 'DBSCAN'

    print(f"✓ 完成 (耗時: {elapsed_time:.2f}秒)")
    print(f"   聚類數: {clusterer.n_clusters_}")
    print(f"   噪聲點: {clusterer.n_noise_} ({clusterer.n_noise_/len(df)*100:.1f}%)")

    return labels, summary, metrics, clusterer


def run_gmm(df, features, n_components=4):
    """運行GMM聚類"""
    print("\n🟡 運行 GMM 聚類...")
    start_time = time.time()

    clusterer = GMMClusterer(n_components=n_components, random_state=42)
    labels = clusterer.fit_predict(df, features)
    summary = clusterer.get_cluster_summary(df, features)
    metrics = clusterer.evaluate_clustering(df, features)

    elapsed_time = time.time() - start_time
    metrics['execution_time'] = elapsed_time
    metrics['algorithm'] = 'GMM'

    print(f"✓ 完成 (耗時: {elapsed_time:.2f}秒)")
    print(f"   組件數: {n_components}")
    print(f"   BIC: {metrics.get('bic', 'N/A'):.2f}")
    print(f"   收斂: {metrics.get('converged', 'N/A')}")

    return labels, summary, metrics, clusterer


def run_hierarchical(df, features, n_clusters=4, linkage='ward'):
    """運行層次聚類"""
    print("\n🟣 運行 Hierarchical 聚類...")
    start_time = time.time()

    clusterer = HierarchicalClusterer(n_clusters=n_clusters, linkage=linkage)
    labels = clusterer.fit_predict(df, features)
    summary = clusterer.get_cluster_summary(df, features)
    metrics = clusterer.evaluate_clustering(df, features)

    elapsed_time = time.time() - start_time
    metrics['execution_time'] = elapsed_time
    metrics['algorithm'] = 'Hierarchical'

    print(f"✓ 完成 (耗時: {elapsed_time:.2f}秒)")
    print(f"   聚類數: {n_clusters}")
    print(f"   連接方法: {linkage}")

    return labels, summary, metrics, clusterer


def compare_algorithms(all_metrics):
    """比較所有算法的性能"""
    print("\n" + "="*80)
    print("📊 算法性能比較")
    print("="*80)

    comparison_df = pd.DataFrame([
        {
            '算法': m['algorithm'],
            '執行時間(秒)': f"{m['execution_time']:.3f}",
            '聚類數': m.get('n_clusters') or m.get('n_components', 'N/A'),
            'Silhouette分數': f"{m.get('silhouette_score', 0):.4f}" if m.get('silhouette_score') else 'N/A',
            'Davies-Bouldin分數': f"{m.get('davies_bouldin_score', 0):.4f}" if m.get('davies_bouldin_score') else 'N/A',
            '樣本數': m['n_samples']
        }
        for m in all_metrics
    ])

    print("\n" + comparison_df.to_string(index=False))
    print("\n" + "="*80)

    # 評分說明
    print("\n📝 評分說明:")
    print("   • Silhouette分數: -1到1，越高越好 (>0.5為優秀)")
    print("   • Davies-Bouldin分數: ≥0，越低越好 (<1為優秀)")

    return comparison_df


def plot_results(df, features, all_labels, all_clusterers):
    """可視化所有算法的結果"""
    print("\n📈 生成可視化圖表...")

    # 使用前兩個特徵進行2D可視化
    feat_x, feat_y = features[0], features[1]

    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('聚類算法比較 - 可視化結果', fontsize=16, fontweight='bold')

    algorithms = ['K-Means', 'DBSCAN', 'GMM', 'Hierarchical']
    colors = ['Blues', 'Greens', 'YlOrRd', 'Purples']

    for idx, (labels, clusterer, algo, cmap) in enumerate(zip(
        all_labels, all_clusterers, algorithms, colors
    )):
        ax = axes[idx // 2, idx % 2]

        # 創建散點圖
        scatter = ax.scatter(
            df[feat_x],
            df[feat_y],
            c=labels,
            cmap=cmap,
            alpha=0.6,
            s=50,
            edgecolors='black',
            linewidth=0.5
        )

        ax.set_xlabel(feat_x, fontsize=11)
        ax.set_ylabel(feat_y, fontsize=11)
        ax.set_title(f'{algo}聚類結果', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)

        # 添加顏色條
        cbar = plt.colorbar(scatter, ax=ax)
        cbar.set_label('Cluster', fontsize=10)

        # 添加聚類中心(僅K-Means)
        if algo == 'K-Means' and hasattr(clusterer, 'cluster_centers_'):
            centers = clusterer.cluster_centers_
            if centers is not None and len(features) >= 2:
                # 如果數據被標準化了，需要反標準化
                if clusterer.scaler is not None:
                    # 創建完整的中心點(包含所有特徵)
                    full_centers = centers
                    centers_original = clusterer.scaler.inverse_transform(full_centers)
                    feat_idx_x = features.index(feat_x)
                    feat_idx_y = features.index(feat_y)
                    ax.scatter(
                        centers_original[:, feat_idx_x],
                        centers_original[:, feat_idx_y],
                        c='red',
                        marker='X',
                        s=200,
                        edgecolors='black',
                        linewidth=2,
                        label='聚類中心'
                    )
                    ax.legend()

    plt.tight_layout()

    # 保存圖表
    output_path = project_root / 'outputs' / 'plots' / 'clustering_comparison.png'
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 圖表已保存到: {output_path}")

    plt.show()


def plot_metrics_comparison(comparison_df):
    """繪製指標比較柱狀圖"""
    print("\n📊 生成性能指標比較圖...")

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.suptitle('聚類算法性能指標比較', fontsize=14, fontweight='bold')

    # 執行時間比較
    ax1 = axes[0]
    execution_times = comparison_df['執行時間(秒)'].astype(float)
    algorithms = comparison_df['算法']

    bars1 = ax1.bar(algorithms, execution_times, color=['#3498db', '#2ecc71', '#f39c12', '#9b59b6'])
    ax1.set_ylabel('執行時間 (秒)', fontsize=11)
    ax1.set_title('執行時間比較', fontsize=12, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)

    # 在柱子上添加數值標籤
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.3f}s',
                ha='center', va='bottom', fontsize=9)

    # Silhouette分數比較(過濾N/A值)
    ax2 = axes[1]
    valid_scores = comparison_df[comparison_df['Silhouette分數'] != 'N/A'].copy()

    if len(valid_scores) > 0:
        silhouette_scores = valid_scores['Silhouette分數'].astype(float)
        algos = valid_scores['算法']

        bars2 = ax2.bar(algos, silhouette_scores, color=['#3498db', '#2ecc71', '#f39c12', '#9b59b6'])
        ax2.set_ylabel('Silhouette分數', fontsize=11)
        ax2.set_title('聚類質量比較 (Silhouette)', fontsize=12, fontweight='bold')
        ax2.set_ylim(0, 1)
        ax2.axhline(y=0.5, color='red', linestyle='--', linewidth=1, label='優秀閾值 (0.5)')
        ax2.grid(axis='y', alpha=0.3)
        ax2.legend()

        # 添加數值標籤
        for bar in bars2:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}',
                    ha='center', va='bottom', fontsize=9)

    plt.tight_layout()

    # 保存圖表
    output_path = project_root / 'outputs' / 'plots' / 'metrics_comparison.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✓ 指標比較圖已保存到: {output_path}")

    plt.show()


def save_results(comparison_df, all_summaries):
    """保存結果到CSV"""
    print("\n💾 保存結果...")

    # 保存比較表
    comparison_path = project_root / 'outputs' / 'reports' / 'clustering_comparison.csv'
    comparison_path.parent.mkdir(parents=True, exist_ok=True)
    comparison_df.to_csv(comparison_path, index=False, encoding='utf-8-sig')
    print(f"✓ 比較表已保存到: {comparison_path}")

    # 保存各算法的詳細摘要
    for summary, algo in zip(all_summaries, ['kmeans', 'dbscan', 'gmm', 'hierarchical']):
        summary_path = project_root / 'outputs' / 'reports' / f'{algo}_summary.csv'
        summary.to_csv(summary_path, index=False, encoding='utf-8-sig')

    print(f"✓ 詳細摘要已保存到: outputs/reports/")


def main():
    """主函數"""
    print("="*80)
    print("🚀 聚類算法全面比較")
    print("="*80)
    print("\n本腳本將比較4種聚類算法:")
    print("  1️⃣  K-Means - 快速、適合球形聚類")
    print("  2️⃣  DBSCAN - 發現任意形狀、自動檢測異常")
    print("  3️⃣  GMM - 概率性軟聚類")
    print("  4️⃣  Hierarchical - 層次結構可視化")
    print()

    # 加載數據
    df = load_sample_data()
    features = get_features(df)
    print(f"\n✓ 使用特徵: {features}")

    # 運行所有算法
    n_clusters = 4

    kmeans_labels, kmeans_summary, kmeans_metrics, kmeans_clusterer = run_kmeans(
        df, features, n_clusters
    )

    dbscan_labels, dbscan_summary, dbscan_metrics, dbscan_clusterer = run_dbscan(
        df, features, eps=0.5, min_samples=5
    )

    gmm_labels, gmm_summary, gmm_metrics, gmm_clusterer = run_gmm(
        df, features, n_clusters
    )

    hierarchical_labels, hierarchical_summary, hierarchical_metrics, hierarchical_clusterer = run_hierarchical(
        df, features, n_clusters
    )

    # 收集結果
    all_metrics = [kmeans_metrics, dbscan_metrics, gmm_metrics, hierarchical_metrics]
    all_labels = [kmeans_labels, dbscan_labels, gmm_labels, hierarchical_labels]
    all_summaries = [kmeans_summary, dbscan_summary, gmm_summary, hierarchical_summary]
    all_clusterers = [kmeans_clusterer, dbscan_clusterer, gmm_clusterer, hierarchical_clusterer]

    # 比較算法
    comparison_df = compare_algorithms(all_metrics)

    # 可視化結果
    plot_results(df, features, all_labels, all_clusterers)
    plot_metrics_comparison(comparison_df)

    # 保存結果
    save_results(comparison_df, all_summaries)

    print("\n" + "="*80)
    print("✅ 分析完成！")
    print("="*80)
    print("\n📂 輸出文件:")
    print("   • outputs/plots/clustering_comparison.png - 聚類結果可視化")
    print("   • outputs/plots/metrics_comparison.png - 性能指標比較")
    print("   • outputs/reports/clustering_comparison.csv - 比較表")
    print("   • outputs/reports/*_summary.csv - 各算法詳細摘要")
    print("\n💡 建議:")
    print("   • Silhouette分數最高的算法通常質量最好")
    print("   • 考慮執行時間和質量的平衡")
    print("   • 對於異常檢測，DBSCAN表現最佳")
    print("   • 對於概率性分群，選擇GMM")
    print()


if __name__ == '__main__':
    main()
