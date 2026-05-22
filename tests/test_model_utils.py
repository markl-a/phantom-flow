"""測試模型工具模塊"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

from data_analysis_chatbots.model_utils import (
    ModelRegistry,
    save_model,
    load_model,
    export_model_metadata,
    compare_models,
    cleanup_old_models
)
from data_analysis_chatbots.clustering import KMeansClusterer, DBSCANClusterer
from data_analysis_chatbots.exceptions import ModelSaveError, ModelLoadError


class TestModelRegistry:
    """測試模型註冊表"""

    @pytest.fixture
    def temp_registry_dir(self):
        """創建臨時註冊表目錄"""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def registry(self, temp_registry_dir):
        """創建測試註冊表"""
        registry_path = temp_registry_dir / "test_registry.json"
        return ModelRegistry(registry_path)

    def test_initialization(self, temp_registry_dir):
        """測試初始化"""
        registry_path = temp_registry_dir / "registry.json"
        registry = ModelRegistry(registry_path)

        assert registry.registry_path == registry_path
        assert isinstance(registry.registry, dict)
        assert 'models' in registry.registry

    def test_register_model(self, registry):
        """測試註冊模型"""
        metadata = {
            'algorithm': 'KMeansClusterer',
            'n_clusters': 5,
            'dataset': 'test_data'
        }

        registry.register_model('test_model_1', metadata)

        # 驗證模型已註冊
        model_info = registry.get_model_info('test_model_1')
        assert model_info is not None
        assert model_info['algorithm'] == 'KMeansClusterer'
        assert model_info['n_clusters'] == 5
        assert 'registered_at' in model_info

    def test_get_model_info_exists(self, registry):
        """測試獲取存在的模型信息"""
        metadata = {'algorithm': 'KMeans', 'n_clusters': 3}
        registry.register_model('model_a', metadata)

        info = registry.get_model_info('model_a')
        assert info is not None
        assert info['algorithm'] == 'KMeans'

    def test_get_model_info_not_exists(self, registry):
        """測試獲取不存在的模型信息"""
        info = registry.get_model_info('nonexistent_model')
        assert info is None

    def test_list_models_empty(self, registry):
        """測試列出空註冊表"""
        models = registry.list_models()
        assert isinstance(models, list)
        assert len(models) == 0

    def test_list_models_with_data(self, registry):
        """測試列出已註冊的模型"""
        # 註冊多個模型
        registry.register_model('model_1', {'algorithm': 'KMeans', 'n_clusters': 3})
        registry.register_model('model_2', {'algorithm': 'DBSCAN', 'eps': 0.5})
        registry.register_model('model_3', {'algorithm': 'KMeans', 'n_clusters': 5})

        models = registry.list_models()
        assert len(models) == 3

    def test_list_models_filter_by_algorithm(self, registry):
        """測試按算法篩選模型"""
        registry.register_model('km1', {'algorithm': 'KMeans', 'n_clusters': 3})
        registry.register_model('km2', {'algorithm': 'KMeans', 'n_clusters': 5})
        registry.register_model('db1', {'algorithm': 'DBSCAN', 'eps': 0.5})

        kmeans_models = registry.list_models(algorithm='KMeans')
        assert len(kmeans_models) == 2
        assert all(m['algorithm'] == 'KMeans' for m in kmeans_models)

    def test_list_models_filter_by_dataset(self, registry):
        """測試按數據集篩選模型"""
        registry.register_model('m1', {'algorithm': 'KMeans', 'dataset': 'customers'})
        registry.register_model('m2', {'algorithm': 'DBSCAN', 'dataset': 'customers'})
        registry.register_model('m3', {'algorithm': 'KMeans', 'dataset': 'products'})

        customer_models = registry.list_models(dataset='customers')
        assert len(customer_models) == 2
        assert all(m['dataset'] == 'customers' for m in customer_models)

    def test_delete_model(self, registry):
        """測試刪除模型"""
        registry.register_model('model_to_delete', {'algorithm': 'KMeans'})

        # 確認模型存在
        assert registry.get_model_info('model_to_delete') is not None

        # 刪除模型
        success = registry.delete_model('model_to_delete')
        assert success is True

        # 確認已刪除
        assert registry.get_model_info('model_to_delete') is None

    def test_delete_nonexistent_model(self, registry):
        """測試刪除不存在的模型"""
        success = registry.delete_model('nonexistent')
        assert success is False

    def test_persistence(self, temp_registry_dir):
        """測試註冊表持久化"""
        registry_path = temp_registry_dir / "persistent_registry.json"

        # 創建註冊表並添加模型
        registry1 = ModelRegistry(registry_path)
        registry1.register_model('model_1', {'algorithm': 'KMeans'})

        # 創建新實例，應該能加載之前的數據
        registry2 = ModelRegistry(registry_path)
        model_info = registry2.get_model_info('model_1')

        assert model_info is not None
        assert model_info['algorithm'] == 'KMeans'


class TestSaveModel:
    """測試模型保存功能"""

    @pytest.fixture
    def temp_model_dir(self):
        """創建臨時模型目錄"""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def sample_data(self):
        """創建範例數據"""
        np.random.seed(42)
        return pd.DataFrame({
            'Feature1': np.random.randn(100),
            'Feature2': np.random.randn(100)
        })

    @pytest.fixture
    def trained_clusterer(self, sample_data):
        """創建訓練好的聚類器"""
        clusterer = KMeansClusterer(n_clusters=3, random_state=42)
        clusterer.fit(sample_data, ['Feature1', 'Feature2'])
        return clusterer

    def test_save_model_basic(self, trained_clusterer, temp_model_dir):
        """測試基本模型保存"""
        model_path = temp_model_dir / "test_model.pkl"

        path = save_model(
            trained_clusterer,
            model_path=model_path,
            register=False
        )

        assert path.exists()
        assert path == model_path

    def test_save_model_auto_path(self, trained_clusterer, temp_model_dir, monkeypatch):
        """測試自動生成路徑"""
        # 修改工作目錄
        monkeypatch.chdir(temp_model_dir)

        path = save_model(
            trained_clusterer,
            register=False
        )

        assert path.exists()
        assert 'kmeans' in path.name.lower()
        assert path.suffix == '.pkl'

    def test_save_model_with_metadata(self, trained_clusterer, temp_model_dir):
        """測試保存帶元數據的模型"""
        model_path = temp_model_dir / "model_with_metadata.pkl"
        metadata = {
            'dataset': 'test_dataset',
            'features': ['Feature1', 'Feature2'],
            'performance': 0.85
        }

        path = save_model(
            trained_clusterer,
            model_path=model_path,
            metadata=metadata,
            register=False
        )

        assert path.exists()

    def test_save_model_creates_directory(self, trained_clusterer, temp_model_dir):
        """測試自動創建目錄"""
        model_path = temp_model_dir / "nested" / "dir" / "model.pkl"

        path = save_model(
            trained_clusterer,
            model_path=model_path,
            register=False
        )

        assert path.exists()
        assert path.parent.exists()

    def test_save_different_clusterer_types(self, sample_data, temp_model_dir):
        """測試保存不同類型的聚類器"""
        # KMeans
        kmeans = KMeansClusterer(n_clusters=3)
        kmeans.fit(sample_data, ['Feature1', 'Feature2'])

        kmeans_path = save_model(
            kmeans,
            model_path=temp_model_dir / "kmeans.pkl",
            register=False
        )
        assert kmeans_path.exists()

        # DBSCAN
        dbscan = DBSCANClusterer(eps=0.5, min_samples=5)
        dbscan.fit(sample_data, ['Feature1', 'Feature2'])

        dbscan_path = save_model(
            dbscan,
            model_path=temp_model_dir / "dbscan.pkl",
            register=False
        )
        assert dbscan_path.exists()


class TestLoadModel:
    """測試模型加載功能"""

    @pytest.fixture
    def temp_model_dir(self):
        """創建臨時模型目錄"""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def sample_data(self):
        """創建範例數據"""
        np.random.seed(42)
        return pd.DataFrame({
            'Feature1': np.random.randn(100),
            'Feature2': np.random.randn(100)
        })

    @pytest.fixture
    def saved_model_path(self, sample_data, temp_model_dir):
        """創建並保存一個模型"""
        clusterer = KMeansClusterer(n_clusters=3, random_state=42)
        clusterer.fit(sample_data, ['Feature1', 'Feature2'])

        model_path = temp_model_dir / "saved_model.pkl"
        save_model(clusterer, model_path=model_path, register=False)

        return model_path

    def test_load_model_from_path(self, saved_model_path):
        """測試從路徑加載模型"""
        clusterer = load_model(model_path=saved_model_path)

        assert clusterer is not None
        assert isinstance(clusterer, KMeansClusterer)
        assert clusterer.n_clusters == 3

    def test_load_nonexistent_model(self, temp_model_dir):
        """測試加載不存在的模型"""
        with pytest.raises(ModelLoadError):
            load_model(model_path=temp_model_dir / "nonexistent.pkl")

    def test_load_model_preserves_state(self, saved_model_path, sample_data):
        """測試加載的模型保持訓練狀態"""
        clusterer = load_model(model_path=saved_model_path)

        # 應該能夠直接預測
        labels = clusterer.predict(sample_data, ['Feature1', 'Feature2'])
        assert len(labels) == len(sample_data)
        assert len(set(labels)) <= 3

    def test_load_without_arguments(self):
        """測試不提供參數時拋出錯誤"""
        with pytest.raises(ModelLoadError):
            load_model()


class TestExportModelMetadata:
    """測試元數據導出"""

    @pytest.fixture
    def temp_dir(self):
        """創建臨時目錄"""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def registry_with_model(self, temp_dir):
        """創建包含模型的註冊表"""
        registry_path = temp_dir / "registry.json"
        registry = ModelRegistry(registry_path)

        metadata = {
            'algorithm': 'KMeansClusterer',
            'n_clusters': 5,
            'dataset': 'test_data',
            'performance': 0.85
        }
        registry.register_model('test_model', metadata)

        return registry

    def test_export_metadata(self, temp_dir, registry_with_model):
        """測試導出元數據"""
        output_path = temp_dir / "exported_metadata.json"

        path = export_model_metadata('test_model', output_path, registry=registry_with_model)

        assert path.exists()
        assert path == output_path

        # 驗證內容
        import json
        with open(path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        assert metadata['algorithm'] == 'KMeansClusterer'
        assert metadata['n_clusters'] == 5

    def test_export_nonexistent_model(self, temp_dir, registry_with_model):
        """測試導出不存在的模型元數據"""
        with pytest.raises(ModelLoadError):
            export_model_metadata('nonexistent_model', temp_dir / "output.json", registry=registry_with_model)


class TestCompareModels:
    """測試模型比較"""

    @pytest.fixture
    def temp_dir(self):
        """創建臨時目錄"""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def registry_with_models(self, temp_dir):
        """創建包含多個模型的註冊表"""
        registry_path = temp_dir / "registry.json"
        registry = ModelRegistry(registry_path)

        registry.register_model('model_v1', {
            'algorithm': 'KMeans',
            'n_clusters': 3,
            'performance': 0.75
        })
        registry.register_model('model_v2', {
            'algorithm': 'KMeans',
            'n_clusters': 5,
            'performance': 0.82
        })
        registry.register_model('model_v3', {
            'algorithm': 'DBSCAN',
            'eps': 0.5,
            'performance': 0.88
        })

        return registry

    def test_compare_models(self, registry_with_models, capsys):
        """測試模型比較輸出"""
        # 這個函數會打印輸出，我們主要測試它不會拋出錯誤
        compare_models(['model_v1', 'model_v2', 'model_v3'], registry=registry_with_models)

        captured = capsys.readouterr()
        assert '模型比較' in captured.out
        assert 'model_v1' in captured.out

    def test_compare_nonexistent_models(self, registry_with_models, capsys):
        """測試比較不存在的模型"""
        compare_models(['nonexistent1', 'nonexistent2'], registry=registry_with_models)

        captured = capsys.readouterr()
        assert '沒有找到任何模型' in captured.out


class TestCleanupOldModels:
    """測試清理舊模型"""

    @pytest.fixture
    def temp_dir(self):
        """創建臨時目錄"""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def registry_with_old_models(self, temp_dir):
        """創建包含新舊模型的註冊表"""
        registry_path = temp_dir / "registry.json"
        registry = ModelRegistry(registry_path)

        # 註冊舊模型（60天前）
        old_date = (datetime.now() - timedelta(days=60)).isoformat()
        registry.registry['models']['old_model_1'] = {
            'algorithm': 'KMeans',
            'registered_at': old_date
        }

        # 註冊新模型（5天前）
        recent_date = (datetime.now() - timedelta(days=5)).isoformat()
        registry.registry['models']['recent_model'] = {
            'algorithm': 'DBSCAN',
            'registered_at': recent_date
        }

        registry._save_registry()
        return registry

    def test_cleanup_dry_run(self, registry_with_old_models):
        """測試模擬清理模式"""
        to_delete = cleanup_old_models(days=30, dry_run=True, registry=registry_with_old_models)

        assert len(to_delete) >= 1
        assert 'old_model_1' in to_delete

        # 驗證實際上沒有刪除
        assert registry_with_old_models.get_model_info('old_model_1') is not None

    def test_cleanup_actual(self, temp_dir):
        """測試實際清理"""
        registry_path = temp_dir / "registry.json"
        registry = ModelRegistry(registry_path)

        # 註冊舊模型
        old_date = (datetime.now() - timedelta(days=60)).isoformat()
        registry.registry['models']['old_model'] = {
            'algorithm': 'KMeans',
            'registered_at': old_date,
            'path': str(temp_dir / 'nonexistent.pkl')  # 不存在的文件
        }
        registry._save_registry()

        # 實際清理
        deleted = cleanup_old_models(days=30, dry_run=False, registry=registry)

        assert 'old_model' in deleted

        # 重新加載註冊表驗證
        registry2 = ModelRegistry(registry_path)
        assert registry2.get_model_info('old_model') is None


class TestModelUtilsIntegration:
    """模型工具集成測試"""

    @pytest.fixture
    def temp_dir(self):
        """創建臨時目錄"""
        tmpdir = tempfile.mkdtemp()
        yield Path(tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)

    @pytest.fixture
    def sample_data(self):
        """創建範例數據"""
        np.random.seed(42)
        return pd.DataFrame({
            'Feature1': np.random.randn(100),
            'Feature2': np.random.randn(100)
        })

    def test_full_workflow(self, sample_data, temp_dir, monkeypatch):
        """測試完整工作流：訓練 -> 保存 -> 註冊 -> 加載 -> 預測"""
        monkeypatch.chdir(temp_dir)

        # 1. 訓練模型
        clusterer = KMeansClusterer(n_clusters=3, random_state=42)
        clusterer.fit(sample_data, ['Feature1', 'Feature2'])

        # 2. 保存並註冊模型
        model_path = temp_dir / "models" / "workflow_test.pkl"
        registry_path = temp_dir / "models" / "registry.json"

        save_model(
            clusterer,
            model_path=model_path,
            model_name='workflow_test',
            metadata={'dataset': 'test', 'purpose': 'integration_test'},
            register=True
        )

        # 3. 驗證註冊表
        registry = ModelRegistry(registry_path)
        model_info = registry.get_model_info('workflow_test')
        assert model_info is not None
        assert model_info['algorithm'] == 'KMeansClusterer'

        # 4. 加載模型
        loaded_clusterer = load_model(model_path=model_path)
        assert isinstance(loaded_clusterer, KMeansClusterer)

        # 5. 使用加載的模型進行預測
        labels = loaded_clusterer.predict(sample_data, ['Feature1', 'Feature2'])
        assert len(labels) == len(sample_data)
        assert len(set(labels)) == 3
