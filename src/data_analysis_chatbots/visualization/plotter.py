"""Plotting and visualization utilities."""

from typing import Optional, List, Tuple, Dict, Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from loguru import logger


class Plotter:
    """Create visualizations for data analysis."""

    def __init__(
        self,
        style: str = 'seaborn-v0_8',
        palette: str = 'husl',
        figure_size: Tuple[int, int] = (12, 8),
        dpi: int = 100
    ):
        """
        Initialize the Plotter.

        Args:
            style: Matplotlib style
            palette: Seaborn color palette
            figure_size: Default figure size
            dpi: DPI for plots
        """
        self.style = style
        self.palette = palette
        self.figure_size = figure_size
        self.dpi = dpi

        # Set style
        try:
            plt.style.use(style)
        except OSError:
            logger.warning(f"Style '{style}' not found. Using default.")
            plt.style.use('default')

        sns.set_palette(palette)

    def plot_distribution(
        self,
        data: pd.Series,
        title: str = "Distribution Plot",
        xlabel: str = None,
        bins: int = 30,
        kde: bool = True,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot distribution of a variable.

        Args:
            data: Data to plot
            title: Plot title
            xlabel: X-axis label
            bins: Number of bins for histogram
            kde: Whether to show KDE
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)

        sns.histplot(data, bins=bins, kde=kde, ax=ax)

        ax.set_title(title, fontsize=16, fontweight='bold')
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        ax.set_ylabel('Frequency', fontsize=12)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def plot_scatter(
        self,
        x: pd.Series,
        y: pd.Series,
        hue: Optional[pd.Series] = None,
        title: str = "Scatter Plot",
        xlabel: str = None,
        ylabel: str = None,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create a scatter plot.

        Args:
            x: X-axis data
            y: Y-axis data
            hue: Variable for color encoding
            title: Plot title
            xlabel: X-axis label
            ylabel: Y-axis label
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)

        if hue is not None:
            sns.scatterplot(x=x, y=y, hue=hue, palette=self.palette, s=100, alpha=0.7, ax=ax)
        else:
            sns.scatterplot(x=x, y=y, s=100, alpha=0.7, ax=ax)

        ax.set_title(title, fontsize=16, fontweight='bold')
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=12)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=12)

        if hue is not None:
            ax.legend(title=hue.name, bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def plot_clusters(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        cluster_col: str,
        centers: Optional[pd.DataFrame] = None,
        title: str = "Customer Segments",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot clustering results.

        Args:
            df: DataFrame with data
            x_col: Column for x-axis
            y_col: Column for y-axis
            cluster_col: Column with cluster labels
            centers: DataFrame with cluster centers
            title: Plot title
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)

        # Plot clusters
        sns.scatterplot(
            data=df,
            x=x_col,
            y=y_col,
            hue=cluster_col,
            palette=self.palette,
            s=100,
            alpha=0.7,
            ax=ax
        )

        # Plot centers if provided
        if centers is not None and x_col in centers.columns and y_col in centers.columns:
            ax.scatter(
                centers[x_col],
                centers[y_col],
                s=300,
                c='red',
                marker='X',
                edgecolors='black',
                linewidths=2,
                label='Centers',
                zorder=10
            )

        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(x_col, fontsize=12)
        ax.set_ylabel(y_col, fontsize=12)
        ax.legend(title='Cluster', bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def plot_elbow(
        self,
        k_values: List[int],
        inertias: List[float],
        title: str = "Elbow Method for Optimal K",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot elbow curve for K-means.

        Args:
            k_values: List of K values
            inertias: List of inertia values
            title: Plot title
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)

        ax.plot(k_values, inertias, 'bo-', linewidth=2, markersize=8)

        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('Number of Clusters (K)', fontsize=12)
        ax.set_ylabel('Inertia', fontsize=12)
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def plot_rfm_heatmap(
        self,
        rfm_df: pd.DataFrame,
        title: str = "RFM Correlation Heatmap",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot RFM correlation heatmap.

        Args:
            rfm_df: DataFrame with RFM metrics
            title: Plot title
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=(10, 8), dpi=self.dpi)

        # Select only RFM columns
        rfm_cols = [col for col in ['Recency', 'Frequency', 'Monetary'] if col in rfm_df.columns]

        if not rfm_cols:
            logger.error("No RFM columns found in DataFrame")
            return fig

        # Calculate correlation
        corr = rfm_df[rfm_cols].corr()

        # Plot heatmap
        sns.heatmap(
            corr,
            annot=True,
            fmt='.2f',
            cmap='coolwarm',
            center=0,
            square=True,
            linewidths=1,
            cbar_kws={"shrink": 0.8},
            ax=ax
        )

        ax.set_title(title, fontsize=16, fontweight='bold')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def plot_segment_distribution(
        self,
        segments: pd.Series,
        title: str = "Customer Segment Distribution",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot distribution of customer segments.

        Args:
            segments: Series with segment labels
            title: Plot title
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), dpi=self.dpi)

        # Count plot
        segment_counts = segments.value_counts()
        colors = sns.color_palette(self.palette, len(segment_counts))

        ax1.bar(range(len(segment_counts)), segment_counts.values, color=colors)
        ax1.set_xticks(range(len(segment_counts)))
        ax1.set_xticklabels(segment_counts.index, rotation=45, ha='right')
        ax1.set_title('Segment Counts', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Number of Customers', fontsize=12)

        # Pie chart
        ax2.pie(
            segment_counts.values,
            labels=segment_counts.index,
            autopct='%1.1f%%',
            colors=colors,
            startangle=90
        )
        ax2.set_title('Segment Percentage', fontsize=14, fontweight='bold')

        fig.suptitle(title, fontsize=16, fontweight='bold')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def plot_comparison(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        group_col: str,
        plot_type: str = 'box',
        title: str = "Comparison Plot",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot comparison across groups.

        Args:
            df: DataFrame with data
            x_col: Column for x-axis (groups)
            y_col: Column for y-axis (values)
            group_col: Column for grouping
            plot_type: Type of plot ('box', 'violin', 'bar')
            title: Plot title
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)

        if plot_type == 'box':
            sns.boxplot(data=df, x=x_col, y=y_col, hue=group_col, palette=self.palette, ax=ax)
        elif plot_type == 'violin':
            sns.violinplot(data=df, x=x_col, y=y_col, hue=group_col, palette=self.palette, ax=ax)
        elif plot_type == 'bar':
            sns.barplot(data=df, x=x_col, y=y_col, hue=group_col, palette=self.palette, ax=ax)
        else:
            logger.error(f"Unknown plot type: {plot_type}")
            return fig

        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel(x_col, fontsize=12)
        ax.set_ylabel(y_col, fontsize=12)

        if group_col:
            ax.legend(title=group_col, bbox_to_anchor=(1.05, 1), loc='upper left')

        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def plot_silhouette(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        title: str = "Silhouette Analysis",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot silhouette analysis for clustering evaluation.

        Shows the silhouette score for each sample, grouped by cluster.
        Helps identify cluster quality and potential mis-clustered samples.

        Args:
            X: Feature data (n_samples, n_features)
            labels: Cluster labels
            title: Plot title
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        from sklearn.metrics import silhouette_samples, silhouette_score

        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)

        # Calculate silhouette scores
        n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
        silhouette_avg = silhouette_score(X, labels)
        sample_silhouette_values = silhouette_samples(X, labels)

        y_lower = 10
        colors = sns.color_palette(self.palette, n_clusters)

        for i, cluster_id in enumerate(sorted(set(labels))):
            if cluster_id == -1:
                continue  # Skip noise points

            # Get silhouette values for this cluster
            cluster_silhouette_values = sample_silhouette_values[labels == cluster_id]
            cluster_silhouette_values.sort()

            size_cluster_i = len(cluster_silhouette_values)
            y_upper = y_lower + size_cluster_i

            ax.fill_betweenx(
                np.arange(y_lower, y_upper),
                0,
                cluster_silhouette_values,
                facecolor=colors[i],
                edgecolor=colors[i],
                alpha=0.7
            )

            # Label the clusters
            ax.text(-0.05, y_lower + 0.5 * size_cluster_i, str(cluster_id))
            y_lower = y_upper + 10

        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel("Silhouette Coefficient", fontsize=12)
        ax.set_ylabel("Cluster", fontsize=12)

        # Draw vertical line for average silhouette score
        ax.axvline(x=silhouette_avg, color="red", linestyle="--", label=f"Average: {silhouette_avg:.3f}")
        ax.legend(loc="best")

        ax.set_yticks([])
        ax.set_xlim([-0.2, 1])

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def plot_3d_clusters(
        self,
        df: pd.DataFrame,
        x_col: str,
        y_col: str,
        z_col: str,
        cluster_col: str,
        title: str = "3D Cluster Visualization",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create 3D scatter plot for clustering visualization.

        Args:
            df: DataFrame with data
            x_col: Column for x-axis
            y_col: Column for y-axis
            z_col: Column for z-axis
            cluster_col: Column with cluster labels
            title: Plot title
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        from mpl_toolkits.mplot3d import Axes3D

        fig = plt.figure(figsize=self.figure_size, dpi=self.dpi)
        ax = fig.add_subplot(111, projection='3d')

        clusters = df[cluster_col].unique()
        colors = sns.color_palette(self.palette, len(clusters))

        for i, cluster in enumerate(sorted(clusters)):
            mask = df[cluster_col] == cluster
            label = f"Noise" if cluster == -1 else f"Cluster {cluster}"

            ax.scatter(
                df.loc[mask, x_col],
                df.loc[mask, y_col],
                df.loc[mask, z_col],
                c=[colors[i]],
                label=label,
                s=50,
                alpha=0.7
            )

        ax.set_xlabel(x_col, fontsize=10)
        ax.set_ylabel(y_col, fontsize=10)
        ax.set_zlabel(z_col, fontsize=10)
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.legend(loc='upper left', bbox_to_anchor=(1.05, 1))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def plot_cluster_radar(
        self,
        cluster_summary: pd.DataFrame,
        feature_columns: List[str],
        cluster_col: str = 'Cluster',
        title: str = "Cluster Profiles",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create radar chart comparing cluster profiles.

        Args:
            cluster_summary: DataFrame with cluster statistics
            feature_columns: Feature columns to include
            cluster_col: Column with cluster labels
            title: Plot title
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        from math import pi

        categories = feature_columns
        N = len(categories)

        # Create angles for radar chart
        angles = [n / float(N) * 2 * pi for n in range(N)]
        angles += angles[:1]  # Complete the loop

        fig, ax = plt.subplots(figsize=self.figure_size, subplot_kw=dict(polar=True), dpi=self.dpi)

        clusters = cluster_summary[cluster_col].unique()
        colors = sns.color_palette(self.palette, len(clusters))

        # Normalize values for radar chart
        normalized_df = cluster_summary.copy()
        for col in feature_columns:
            col_min = normalized_df[col].min()
            col_max = normalized_df[col].max()
            if col_max != col_min:
                normalized_df[col] = (normalized_df[col] - col_min) / (col_max - col_min)
            else:
                normalized_df[col] = 0.5

        for i, cluster in enumerate(sorted(clusters)):
            values = normalized_df[normalized_df[cluster_col] == cluster][feature_columns].values.flatten().tolist()
            values += values[:1]  # Complete the loop

            label = f"Noise" if cluster == -1 else f"Cluster {cluster}"

            ax.plot(angles, values, 'o-', linewidth=2, label=label, color=colors[i])
            ax.fill(angles, values, alpha=0.25, color=colors[i])

        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, fontsize=10)
        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def plot_dendrogram(
        self,
        X: np.ndarray,
        labels: Optional[List[str]] = None,
        method: str = 'ward',
        title: str = "Hierarchical Clustering Dendrogram",
        color_threshold: Optional[float] = None,
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot dendrogram for hierarchical clustering.

        Args:
            X: Feature data (n_samples, n_features)
            labels: Sample labels for leaves
            method: Linkage method ('ward', 'complete', 'average', 'single')
            title: Plot title
            color_threshold: Threshold for coloring branches
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        from scipy.cluster.hierarchy import dendrogram, linkage

        fig, ax = plt.subplots(figsize=(16, 10), dpi=self.dpi)

        # Perform hierarchical clustering
        Z = linkage(X, method=method)

        # Plot dendrogram
        dendrogram(
            Z,
            labels=labels,
            leaf_rotation=90,
            leaf_font_size=8,
            color_threshold=color_threshold,
            ax=ax
        )

        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('Sample Index', fontsize=12)
        ax.set_ylabel('Distance', fontsize=12)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def plot_cluster_heatmap(
        self,
        cluster_summary: pd.DataFrame,
        feature_columns: List[str],
        cluster_col: str = 'Cluster',
        title: str = "Cluster Feature Heatmap",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Create heatmap showing cluster centroids for each feature.

        Args:
            cluster_summary: DataFrame with cluster statistics
            feature_columns: Feature columns to include
            cluster_col: Column with cluster labels
            title: Plot title
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)

        # Prepare data for heatmap
        heatmap_data = cluster_summary.set_index(cluster_col)[feature_columns]

        # Normalize data for visualization
        normalized_data = (heatmap_data - heatmap_data.min()) / (heatmap_data.max() - heatmap_data.min())

        sns.heatmap(
            normalized_data,
            annot=True,
            fmt='.2f',
            cmap='RdYlGn',
            center=0.5,
            linewidths=1,
            cbar_kws={"shrink": 0.8, "label": "Normalized Value"},
            ax=ax
        )

        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.set_xlabel('Features', fontsize=12)
        ax.set_ylabel('Cluster', fontsize=12)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def plot_pca_clusters(
        self,
        X: np.ndarray,
        labels: np.ndarray,
        n_components: int = 2,
        title: str = "PCA Cluster Visualization",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot clusters after PCA dimensionality reduction.

        Args:
            X: Feature data
            labels: Cluster labels
            n_components: Number of PCA components (2 or 3)
            title: Plot title
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        from sklearn.decomposition import PCA

        pca = PCA(n_components=n_components)
        X_pca = pca.fit_transform(X)

        if n_components == 3:
            from mpl_toolkits.mplot3d import Axes3D
            fig = plt.figure(figsize=self.figure_size, dpi=self.dpi)
            ax = fig.add_subplot(111, projection='3d')

            clusters = sorted(set(labels))
            colors = sns.color_palette(self.palette, len(clusters))

            for i, cluster in enumerate(clusters):
                mask = labels == cluster
                label = "Noise" if cluster == -1 else f"Cluster {cluster}"
                ax.scatter(
                    X_pca[mask, 0],
                    X_pca[mask, 1],
                    X_pca[mask, 2],
                    c=[colors[i]],
                    label=label,
                    s=50,
                    alpha=0.7
                )

            ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})', fontsize=10)
            ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})', fontsize=10)
            ax.set_zlabel(f'PC3 ({pca.explained_variance_ratio_[2]:.1%})', fontsize=10)
        else:
            fig, ax = plt.subplots(figsize=self.figure_size, dpi=self.dpi)

            clusters = sorted(set(labels))
            colors = sns.color_palette(self.palette, len(clusters))

            for i, cluster in enumerate(clusters):
                mask = labels == cluster
                label = "Noise" if cluster == -1 else f"Cluster {cluster}"
                ax.scatter(
                    X_pca[mask, 0],
                    X_pca[mask, 1],
                    c=[colors[i]],
                    label=label,
                    s=50,
                    alpha=0.7
                )

            ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%})', fontsize=12)
            ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%})', fontsize=12)

        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.legend(loc='best')

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig

    def plot_optimal_k(
        self,
        k_results: Dict[int, Dict[str, float]],
        title: str = "Optimal K Analysis",
        save_path: Optional[str] = None
    ) -> plt.Figure:
        """
        Plot comprehensive optimal K analysis with multiple metrics.

        Args:
            k_results: Dictionary from find_optimal_clusters with metrics for each K
            title: Plot title
            save_path: Path to save the plot

        Returns:
            Matplotlib figure
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10), dpi=self.dpi)

        k_values = sorted(k_results.keys())
        inertias = [k_results[k].get('inertia', 0) for k in k_values]
        silhouettes = [k_results[k].get('silhouette_score', 0) or 0 for k in k_values]
        db_scores = [k_results[k].get('davies_bouldin_score', 0) or 0 for k in k_values]
        ch_scores = [k_results[k].get('calinski_harabasz_score', 0) or 0 for k in k_values]

        # Find recommended K
        recommended_k = None
        for k, v in k_results.items():
            if v.get('is_recommended', False):
                recommended_k = k
                break

        # Plot 1: Elbow curve (Inertia)
        axes[0, 0].plot(k_values, inertias, 'bo-', linewidth=2, markersize=8)
        if recommended_k:
            axes[0, 0].axvline(x=recommended_k, color='red', linestyle='--', alpha=0.7)
        axes[0, 0].set_title('Elbow Method (Inertia)', fontsize=12, fontweight='bold')
        axes[0, 0].set_xlabel('Number of Clusters (K)')
        axes[0, 0].set_ylabel('Inertia')
        axes[0, 0].grid(True, alpha=0.3)

        # Plot 2: Silhouette Score
        axes[0, 1].plot(k_values, silhouettes, 'go-', linewidth=2, markersize=8)
        if recommended_k:
            axes[0, 1].axvline(x=recommended_k, color='red', linestyle='--', alpha=0.7)
        axes[0, 1].set_title('Silhouette Score', fontsize=12, fontweight='bold')
        axes[0, 1].set_xlabel('Number of Clusters (K)')
        axes[0, 1].set_ylabel('Silhouette Score')
        axes[0, 1].grid(True, alpha=0.3)

        # Plot 3: Davies-Bouldin Index
        axes[1, 0].plot(k_values, db_scores, 'ro-', linewidth=2, markersize=8)
        if recommended_k:
            axes[1, 0].axvline(x=recommended_k, color='blue', linestyle='--', alpha=0.7)
        axes[1, 0].set_title('Davies-Bouldin Index (lower is better)', fontsize=12, fontweight='bold')
        axes[1, 0].set_xlabel('Number of Clusters (K)')
        axes[1, 0].set_ylabel('Davies-Bouldin Index')
        axes[1, 0].grid(True, alpha=0.3)

        # Plot 4: Calinski-Harabasz Index
        axes[1, 1].plot(k_values, ch_scores, 'mo-', linewidth=2, markersize=8)
        if recommended_k:
            axes[1, 1].axvline(x=recommended_k, color='blue', linestyle='--', alpha=0.7)
        axes[1, 1].set_title('Calinski-Harabasz Index (higher is better)', fontsize=12, fontweight='bold')
        axes[1, 1].set_xlabel('Number of Clusters (K)')
        axes[1, 1].set_ylabel('Calinski-Harabasz Index')
        axes[1, 1].grid(True, alpha=0.3)

        fig.suptitle(f"{title}\n(Recommended K = {recommended_k})", fontsize=16, fontweight='bold')
        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=self.dpi, bbox_inches='tight')
            logger.info(f"Plot saved to {save_path}")

        return fig
