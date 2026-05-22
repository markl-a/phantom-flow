"""測試可視化模塊"""

import pytest
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import tempfile
from pathlib import Path

# 使用非交互式後端進行測試
matplotlib.use('Agg')

from data_analysis_chatbots.visualization.plotter import Plotter


class TestPlotterInitialization:
    """測試繪圖器初始化"""

    def test_default_initialization(self):
        """測試默認初始化"""
        plotter = Plotter()

        assert plotter.palette == 'husl'
        assert plotter.figure_size == (12, 8)
        assert plotter.dpi == 100

    def test_custom_initialization(self):
        """測試自定義初始化"""
        plotter = Plotter(
            style='default',
            palette='Set2',
            figure_size=(10, 6),
            dpi=150
        )

        assert plotter.palette == 'Set2'
        assert plotter.figure_size == (10, 6)
        assert plotter.dpi == 150

    def test_invalid_style_fallback(self):
        """測試無效樣式降級到默認"""
        # 不應該拋出錯誤，而是使用默認樣式
        plotter = Plotter(style='nonexistent_style')
        assert plotter is not None


class TestPlotDistribution:
    """測試分布圖"""

    @pytest.fixture
    def plotter(self):
        """創建繪圖器實例"""
        return Plotter()

    @pytest.fixture
    def sample_data(self):
        """創建範例數據"""
        np.random.seed(42)
        return pd.Series(np.random.randn(1000), name='test_data')

    def test_basic_distribution_plot(self, plotter, sample_data):
        """測試基本分布圖"""
        fig = plotter.plot_distribution(sample_data)

        assert fig is not None
        assert isinstance(fig, plt.Figure)

        plt.close(fig)

    def test_distribution_with_title(self, plotter, sample_data):
        """測試帶標題的分布圖"""
        fig = plotter.plot_distribution(
            sample_data,
            title="Test Distribution"
        )

        assert fig is not None
        plt.close(fig)

    def test_distribution_with_custom_bins(self, plotter, sample_data):
        """測試自定義bins數量"""
        fig = plotter.plot_distribution(
            sample_data,
            bins=50
        )

        assert fig is not None
        plt.close(fig)

    def test_distribution_without_kde(self, plotter, sample_data):
        """測試不顯示KDE"""
        fig = plotter.plot_distribution(
            sample_data,
            kde=False
        )

        assert fig is not None
        plt.close(fig)

    def test_distribution_save_to_file(self, plotter, sample_data):
        """測試保存分布圖到文件"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            save_path = tmp.name

        try:
            fig = plotter.plot_distribution(
                sample_data,
                save_path=save_path
            )

            assert Path(save_path).exists()
            assert Path(save_path).stat().st_size > 0

            plt.close(fig)
        finally:
            if Path(save_path).exists():
                Path(save_path).unlink()

    def test_distribution_with_xlabel(self, plotter, sample_data):
        """測試自定義X軸標籤"""
        fig = plotter.plot_distribution(
            sample_data,
            xlabel="Custom X Label"
        )

        assert fig is not None
        plt.close(fig)


class TestPlotScatter:
    """測試散點圖"""

    @pytest.fixture
    def plotter(self):
        """創建繪圖器實例"""
        return Plotter()

    @pytest.fixture
    def sample_data(self):
        """創建範例數據"""
        np.random.seed(42)
        return pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'category': np.random.choice(['A', 'B', 'C'], 100)
        })

    def test_basic_scatter_plot(self, plotter, sample_data):
        """測試基本散點圖"""
        fig = plotter.plot_scatter(
            x=sample_data['x'],
            y=sample_data['y']
        )

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_scatter_with_hue(self, plotter, sample_data):
        """測試帶顏色編碼的散點圖"""
        fig = plotter.plot_scatter(
            x=sample_data['x'],
            y=sample_data['y'],
            hue=sample_data['category']
        )

        assert fig is not None
        plt.close(fig)

    def test_scatter_with_labels(self, plotter, sample_data):
        """測試帶軸標籤的散點圖"""
        fig = plotter.plot_scatter(
            x=sample_data['x'],
            y=sample_data['y'],
            xlabel="X Axis",
            ylabel="Y Axis",
            title="Scatter Plot Test"
        )

        assert fig is not None
        plt.close(fig)

    def test_scatter_save_to_file(self, plotter, sample_data):
        """測試保存散點圖"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            save_path = tmp.name

        try:
            fig = plotter.plot_scatter(
                x=sample_data['x'],
                y=sample_data['y'],
                save_path=save_path
            )

            assert Path(save_path).exists()
            plt.close(fig)
        finally:
            if Path(save_path).exists():
                Path(save_path).unlink()


class TestPlotClusters:
    """測試聚類圖"""

    @pytest.fixture
    def plotter(self):
        """創建繪圖器實例"""
        return Plotter()

    @pytest.fixture
    def cluster_data(self):
        """創建聚類數據"""
        np.random.seed(42)
        return pd.DataFrame({
            'Feature1': np.random.randn(100),
            'Feature2': np.random.randn(100),
            'Cluster': np.random.choice([0, 1, 2], 100)
        })

    @pytest.fixture
    def cluster_centers(self):
        """創建聚類中心"""
        return pd.DataFrame({
            'Feature1': [0.5, -0.5, 0.0],
            'Feature2': [0.5, 0.5, -0.5]
        })

    def test_basic_cluster_plot(self, plotter, cluster_data):
        """測試基本聚類圖"""
        fig = plotter.plot_clusters(
            df=cluster_data,
            x_col='Feature1',
            y_col='Feature2',
            cluster_col='Cluster'
        )

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_cluster_plot_with_centers(self, plotter, cluster_data, cluster_centers):
        """測試帶聚類中心的聚類圖"""
        fig = plotter.plot_clusters(
            df=cluster_data,
            x_col='Feature1',
            y_col='Feature2',
            cluster_col='Cluster',
            centers=cluster_centers
        )

        assert fig is not None
        plt.close(fig)

    def test_cluster_plot_with_title(self, plotter, cluster_data):
        """測試帶標題的聚類圖"""
        fig = plotter.plot_clusters(
            df=cluster_data,
            x_col='Feature1',
            y_col='Feature2',
            cluster_col='Cluster',
            title="Customer Segments"
        )

        assert fig is not None
        plt.close(fig)

    def test_cluster_plot_save(self, plotter, cluster_data):
        """測試保存聚類圖"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            save_path = tmp.name

        try:
            fig = plotter.plot_clusters(
                df=cluster_data,
                x_col='Feature1',
                y_col='Feature2',
                cluster_col='Cluster',
                save_path=save_path
            )

            assert Path(save_path).exists()
            plt.close(fig)
        finally:
            if Path(save_path).exists():
                Path(save_path).unlink()


class TestPlotElbow:
    """測試肘部圖"""

    @pytest.fixture
    def plotter(self):
        """創建繪圖器實例"""
        return Plotter()

    def test_basic_elbow_plot(self, plotter):
        """測試基本肘部圖"""
        k_values = [2, 3, 4, 5, 6, 7, 8]
        inertias = [1000, 800, 600, 500, 450, 420, 400]

        fig = plotter.plot_elbow(k_values, inertias)

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_elbow_with_title(self, plotter):
        """測試帶標題的肘部圖"""
        k_values = [2, 3, 4, 5]
        inertias = [1000, 600, 400, 350]

        fig = plotter.plot_elbow(
            k_values,
            inertias,
            title="Custom Elbow Plot"
        )

        assert fig is not None
        plt.close(fig)

    def test_elbow_save(self, plotter):
        """測試保存肘部圖"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            save_path = tmp.name

        try:
            k_values = [2, 3, 4, 5]
            inertias = [1000, 600, 400, 350]

            fig = plotter.plot_elbow(
                k_values,
                inertias,
                save_path=save_path
            )

            assert Path(save_path).exists()
            plt.close(fig)
        finally:
            if Path(save_path).exists():
                Path(save_path).unlink()


class TestPlotRFMHeatmap:
    """測試RFM熱力圖"""

    @pytest.fixture
    def plotter(self):
        """創建繪圖器實例"""
        return Plotter()

    @pytest.fixture
    def rfm_data(self):
        """創建RFM數據"""
        np.random.seed(42)
        return pd.DataFrame({
            'Recency': np.random.randint(1, 365, 100),
            'Frequency': np.random.randint(1, 50, 100),
            'Monetary': np.random.uniform(100, 10000, 100)
        })

    def test_basic_rfm_heatmap(self, plotter, rfm_data):
        """測試基本RFM熱力圖"""
        fig = plotter.plot_rfm_heatmap(rfm_data)

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_rfm_heatmap_with_title(self, plotter, rfm_data):
        """測試帶標題的RFM熱力圖"""
        fig = plotter.plot_rfm_heatmap(
            rfm_data,
            title="Custom RFM Heatmap"
        )

        assert fig is not None
        plt.close(fig)

    def test_rfm_heatmap_save(self, plotter, rfm_data):
        """測試保存RFM熱力圖"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            save_path = tmp.name

        try:
            fig = plotter.plot_rfm_heatmap(
                rfm_data,
                save_path=save_path
            )

            assert Path(save_path).exists()
            plt.close(fig)
        finally:
            if Path(save_path).exists():
                Path(save_path).unlink()

    def test_rfm_heatmap_missing_columns(self, plotter):
        """測試缺少RFM列的情況"""
        # 創建不包含RFM列的數據
        df = pd.DataFrame({
            'Column1': [1, 2, 3],
            'Column2': [4, 5, 6]
        })

        fig = plotter.plot_rfm_heatmap(df)

        # 應該返回空圖，但不應該拋出錯誤
        assert fig is not None
        plt.close(fig)


class TestPlotSegmentDistribution:
    """測試客戶分群分布圖"""

    @pytest.fixture
    def plotter(self):
        """創建繪圖器實例"""
        return Plotter()

    @pytest.fixture
    def segment_data(self):
        """創建分群數據"""
        np.random.seed(42)
        segments = np.random.choice(
            ['Champions', 'Loyal', 'At Risk', 'Lost'],
            size=200,
            p=[0.2, 0.3, 0.3, 0.2]
        )
        return pd.Series(segments, name='Segment')

    def test_basic_segment_distribution(self, plotter, segment_data):
        """測試基本分群分布圖"""
        fig = plotter.plot_segment_distribution(segment_data)

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_segment_distribution_with_title(self, plotter, segment_data):
        """測試帶標題的分群分布圖"""
        fig = plotter.plot_segment_distribution(
            segment_data,
            title="Custom Segment Distribution"
        )

        assert fig is not None
        plt.close(fig)

    def test_segment_distribution_save(self, plotter, segment_data):
        """測試保存分群分布圖"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            save_path = tmp.name

        try:
            fig = plotter.plot_segment_distribution(
                segment_data,
                save_path=save_path
            )

            assert Path(save_path).exists()
            plt.close(fig)
        finally:
            if Path(save_path).exists():
                Path(save_path).unlink()

    def test_segment_distribution_few_segments(self, plotter):
        """測試少量分群的情況"""
        segments = pd.Series(['A', 'B', 'A', 'B', 'A'])

        fig = plotter.plot_segment_distribution(segments)

        assert fig is not None
        plt.close(fig)


class TestPlotComparison:
    """測試比較圖"""

    @pytest.fixture
    def plotter(self):
        """創建繪圖器實例"""
        return Plotter()

    @pytest.fixture
    def comparison_data(self):
        """創建比較數據"""
        np.random.seed(42)
        return pd.DataFrame({
            'Category': ['A', 'A', 'A', 'B', 'B', 'B', 'C', 'C', 'C'] * 10,
            'Value': np.random.randn(90) * 10 + 50,
            'Group': ['X', 'Y', 'Z'] * 30
        })

    def test_box_plot(self, plotter, comparison_data):
        """測試箱線圖"""
        fig = plotter.plot_comparison(
            df=comparison_data,
            x_col='Category',
            y_col='Value',
            group_col='Group',
            plot_type='box'
        )

        assert fig is not None
        assert isinstance(fig, plt.Figure)
        plt.close(fig)

    def test_violin_plot(self, plotter, comparison_data):
        """測試小提琴圖"""
        fig = plotter.plot_comparison(
            df=comparison_data,
            x_col='Category',
            y_col='Value',
            group_col='Group',
            plot_type='violin'
        )

        assert fig is not None
        plt.close(fig)

    def test_bar_plot(self, plotter, comparison_data):
        """測試柱狀圖"""
        fig = plotter.plot_comparison(
            df=comparison_data,
            x_col='Category',
            y_col='Value',
            group_col='Group',
            plot_type='bar'
        )

        assert fig is not None
        plt.close(fig)

    def test_invalid_plot_type(self, plotter, comparison_data):
        """測試無效的圖表類型"""
        fig = plotter.plot_comparison(
            df=comparison_data,
            x_col='Category',
            y_col='Value',
            group_col='Group',
            plot_type='invalid_type'
        )

        # 應該返回圖但不繪製內容
        assert fig is not None
        plt.close(fig)

    def test_comparison_with_title(self, plotter, comparison_data):
        """測試帶標題的比較圖"""
        fig = plotter.plot_comparison(
            df=comparison_data,
            x_col='Category',
            y_col='Value',
            group_col='Group',
            plot_type='box',
            title="Custom Comparison"
        )

        assert fig is not None
        plt.close(fig)

    def test_comparison_save(self, plotter, comparison_data):
        """測試保存比較圖"""
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            save_path = tmp.name

        try:
            fig = plotter.plot_comparison(
                df=comparison_data,
                x_col='Category',
                y_col='Value',
                group_col='Group',
                plot_type='box',
                save_path=save_path
            )

            assert Path(save_path).exists()
            plt.close(fig)
        finally:
            if Path(save_path).exists():
                Path(save_path).unlink()


class TestPlotterIntegration:
    """繪圖器集成測試"""

    @pytest.fixture
    def plotter(self):
        """創建繪圖器實例"""
        return Plotter()

    def test_multiple_plots_workflow(self, plotter):
        """測試創建多個圖表的工作流"""
        np.random.seed(42)

        # 準備數據
        data = pd.DataFrame({
            'x': np.random.randn(100),
            'y': np.random.randn(100),
            'cluster': np.random.choice([0, 1, 2], 100)
        })

        # 創建多個圖表
        fig1 = plotter.plot_distribution(data['x'])
        assert fig1 is not None
        plt.close(fig1)

        fig2 = plotter.plot_scatter(data['x'], data['y'])
        assert fig2 is not None
        plt.close(fig2)

        fig3 = plotter.plot_clusters(
            data,
            'x',
            'y',
            'cluster'
        )
        assert fig3 is not None
        plt.close(fig3)

    def test_save_multiple_plots(self, plotter):
        """測試保存多個圖表"""
        np.random.seed(42)
        data = pd.Series(np.random.randn(100))

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)

            # 保存多個圖表
            fig1 = plotter.plot_distribution(
                data,
                save_path=str(tmpdir / 'plot1.png')
            )
            fig2 = plotter.plot_distribution(
                data,
                save_path=str(tmpdir / 'plot2.png')
            )

            assert (tmpdir / 'plot1.png').exists()
            assert (tmpdir / 'plot2.png').exists()

            plt.close(fig1)
            plt.close(fig2)

    def test_different_styles(self):
        """測試不同樣式的繪圖器"""
        np.random.seed(42)
        data = pd.Series(np.random.randn(100))

        # 測試不同樣式
        for palette in ['husl', 'Set2', 'tab10']:
            plotter = Plotter(palette=palette)
            fig = plotter.plot_distribution(data)
            assert fig is not None
            plt.close(fig)

    def test_different_figure_sizes(self):
        """測試不同圖表大小"""
        np.random.seed(42)
        data = pd.Series(np.random.randn(100))

        # 測試不同大小
        for size in [(8, 6), (10, 8), (12, 10)]:
            plotter = Plotter(figure_size=size)
            fig = plotter.plot_distribution(data)
            assert fig is not None
            assert fig.get_size_inches()[0] == size[0]
            assert fig.get_size_inches()[1] == size[1]
            plt.close(fig)
