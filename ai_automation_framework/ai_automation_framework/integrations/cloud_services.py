"""
雲服務集成
Cloud Services Integration

提供 Azure 和阿里雲的集成功能。
"""

import os
from typing import Optional, List, Dict, Any


# Custom exceptions for cloud services
class CloudServiceError(Exception):
    """Base exception for cloud service errors."""
    pass


class AzureStorageError(CloudServiceError):
    """Exception for Azure Blob Storage operations."""
    pass


class AliyunOSSError(CloudServiceError):
    """Exception for Aliyun OSS operations."""
    pass


# Azure 相關導入
try:
    from azure.storage.blob import BlobServiceClient, BlobClient
    from azure.cosmos import CosmosClient
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential
    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False

# 阿里雲相關導入
try:
    import oss2
    from aliyunsdkcore.client import AcsClient
    from aliyunsdkcore.request import CommonRequest
    HAS_ALIYUN = True
except ImportError:
    HAS_ALIYUN = False


class AzureStorage:
    """Azure Blob Storage 集成"""

    def __init__(
        self,
        connection_string: Optional[str] = None,
        account_name: Optional[str] = None,
        account_key: Optional[str] = None
    ):
        """
        初始化 Azure Storage 客戶端

        Args:
            connection_string: Azure Storage 連接字符串
            account_name: 存儲帳戶名稱
            account_key: 存儲帳戶密鑰
        """
        if not HAS_AZURE:
            raise ImportError("需要安裝 Azure SDK: pip install azure-storage-blob")

        self.connection_string = connection_string or os.getenv("AZURE_STORAGE_CONNECTION_STRING")

        if self.connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
        elif account_name and account_key:
            account_url = f"https://{account_name}.blob.core.windows.net"
            self.blob_service_client = BlobServiceClient(
                account_url=account_url,
                credential=account_key
            )
        else:
            raise ValueError("必須提供 connection_string 或 account_name + account_key")

    def upload_file(
        self,
        container_name: str,
        blob_name: str,
        file_path: str,
        overwrite: bool = True
    ) -> str:
        """
        上傳文件到 Azure Blob Storage

        Args:
            container_name: 容器名稱
            blob_name: Blob 名稱
            file_path: 本地文件路徑
            overwrite: 是否覆蓋已存在的文件

        Returns:
            Blob URL
        """
        # Validate inputs
        if not container_name or not container_name.strip():
            raise ValueError("container_name cannot be empty")
        if not blob_name or not blob_name.strip():
            raise ValueError("blob_name cannot be empty")
        if not file_path or not file_path.strip():
            raise ValueError("file_path cannot be empty")

        # Check file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")

        blob_client = self.blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )

        try:
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=overwrite)
        except IOError as e:
            raise IOError(f"Failed to read file {file_path}: {str(e)}")
        except Exception as e:
            raise AzureStorageError(f"Failed to upload file to Azure Blob Storage: {str(e)}")

        return blob_client.url

    def download_file(
        self,
        container_name: str,
        blob_name: str,
        file_path: str
    ) -> str:
        """
        從 Azure Blob Storage 下載文件

        Args:
            container_name: 容器名稱
            blob_name: Blob 名稱
            file_path: 本地保存路徑

        Returns:
            本地文件路徑
        """
        # Validate inputs
        if not container_name or not container_name.strip():
            raise ValueError("container_name cannot be empty")
        if not blob_name or not blob_name.strip():
            raise ValueError("blob_name cannot be empty")
        if not file_path or not file_path.strip():
            raise ValueError("file_path cannot be empty")

        blob_client = self.blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )

        try:
            with open(file_path, "wb") as download_file:
                download_file.write(blob_client.download_blob().readall())
        except IOError as e:
            raise IOError(f"Failed to write file {file_path}: {str(e)}")
        except Exception as e:
            raise AzureStorageError(f"Failed to download file from Azure Blob Storage: {str(e)}")

        return file_path

    def list_blobs(self, container_name: str) -> List[str]:
        """
        列出容器中的所有 Blob

        Args:
            container_name: 容器名稱

        Returns:
            Blob 名稱列表
        """
        container_client = self.blob_service_client.get_container_client(container_name)
        return [blob.name for blob in container_client.list_blobs()]

    def delete_blob(self, container_name: str, blob_name: str):
        """
        刪除 Blob

        Args:
            container_name: 容器名稱
            blob_name: Blob 名稱
        """
        blob_client = self.blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_name
        )
        blob_client.delete_blob()


class AzureCosmos:
    """Azure Cosmos DB 集成"""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        key: Optional[str] = None,
        database_name: str = "defaultdb"
    ):
        """
        初始化 Azure Cosmos DB 客戶端

        Args:
            endpoint: Cosmos DB 端點
            key: Cosmos DB 密鑰
            database_name: 數據庫名稱
        """
        if not HAS_AZURE:
            raise ImportError("需要安裝 Azure SDK: pip install azure-cosmos")

        self.endpoint = endpoint or os.getenv("AZURE_COSMOS_ENDPOINT")
        self.key = key or os.getenv("AZURE_COSMOS_KEY")
        self.database_name = database_name

        self.client = CosmosClient(self.endpoint, self.key)
        self.database = self.client.get_database_client(database_name)

    def create_item(self, container_name: str, item: Dict[str, Any]) -> Dict[str, Any]:
        """
        創建項目

        Args:
            container_name: 容器名稱
            item: 項目數據

        Returns:
            創建的項目
        """
        container = self.database.get_container_client(container_name)
        return container.create_item(body=item)

    def read_item(
        self,
        container_name: str,
        item_id: str,
        partition_key: str
    ) -> Dict[str, Any]:
        """
        讀取項目

        Args:
            container_name: 容器名稱
            item_id: 項目 ID
            partition_key: 分區鍵

        Returns:
            項目數據
        """
        # Validate inputs
        if not container_name or not container_name.strip():
            raise ValueError("container_name cannot be empty")
        if not item_id or not item_id.strip():
            raise ValueError("item_id cannot be empty")
        if not partition_key or not partition_key.strip():
            raise ValueError("partition_key cannot be empty")

        container = self.database.get_container_client(container_name)
        return container.read_item(item=item_id, partition_key=partition_key)

    def query_items(
        self,
        container_name: str,
        query: str,
        parameters: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        查詢項目

        Args:
            container_name: 容器名稱
            query: SQL 查詢
            parameters: 查詢參數

        Returns:
            查詢結果列表
        """
        container = self.database.get_container_client(container_name)
        return list(container.query_items(
            query=query,
            parameters=parameters or [],
            enable_cross_partition_query=True
        ))

    def delete_item(
        self,
        container_name: str,
        item_id: str,
        partition_key: str
    ):
        """
        刪除項目

        Args:
            container_name: 容器名稱
            item_id: 項目 ID
            partition_key: 分區鍵
        """
        # Validate inputs
        if not container_name or not container_name.strip():
            raise ValueError("container_name cannot be empty")
        if not item_id or not item_id.strip():
            raise ValueError("item_id cannot be empty")
        if not partition_key or not partition_key.strip():
            raise ValueError("partition_key cannot be empty")

        container = self.database.get_container_client(container_name)
        container.delete_item(item=item_id, partition_key=partition_key)


class AliyunOSS:
    """阿里雲 OSS 集成"""

    def __init__(
        self,
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        endpoint: str = "oss-cn-hangzhou.aliyuncs.com",
        bucket_name: Optional[str] = None
    ):
        """
        初始化阿里雲 OSS 客戶端

        Args:
            access_key_id: AccessKey ID
            access_key_secret: AccessKey Secret
            endpoint: OSS 端點
            bucket_name: Bucket 名稱
        """
        if not HAS_ALIYUN:
            raise ImportError("需要安裝阿里雲 SDK: pip install oss2")

        self.access_key_id = access_key_id or os.getenv("ALIYUN_ACCESS_KEY_ID")
        self.access_key_secret = access_key_secret or os.getenv("ALIYUN_ACCESS_KEY_SECRET")
        self.endpoint = endpoint
        self.bucket_name = bucket_name

        self.auth = oss2.Auth(self.access_key_id, self.access_key_secret)

        if bucket_name:
            self.bucket = oss2.Bucket(self.auth, endpoint, bucket_name)
        else:
            self.bucket = None

    def set_bucket(self, bucket_name: str):
        """
        設置當前 Bucket

        Args:
            bucket_name: Bucket 名稱
        """
        self.bucket_name = bucket_name
        self.bucket = oss2.Bucket(self.auth, self.endpoint, bucket_name)

    def upload_file(
        self,
        object_name: str,
        file_path: str
    ) -> str:
        """
        上傳文件到 OSS

        Args:
            object_name: 對象名稱
            file_path: 本地文件路徑

        Returns:
            對象 URL
        """
        if not self.bucket:
            raise ValueError("請先設置 Bucket")

        # Validate inputs
        if not object_name or not object_name.strip():
            raise ValueError("object_name cannot be empty")
        if not file_path or not file_path.strip():
            raise ValueError("file_path cannot be empty")

        # Check file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        if not os.path.isfile(file_path):
            raise ValueError(f"Path is not a file: {file_path}")

        try:
            self.bucket.put_object_from_file(object_name, file_path)
        except Exception as e:
            raise AliyunOSSError(f"Failed to upload file to Aliyun OSS: {str(e)}")

        return f"https://{self.bucket_name}.{self.endpoint}/{object_name}"

    def download_file(
        self,
        object_name: str,
        file_path: str
    ) -> str:
        """
        從 OSS 下載文件

        Args:
            object_name: 對象名稱
            file_path: 本地保存路徑

        Returns:
            本地文件路徑
        """
        if not self.bucket:
            raise ValueError("請先設置 Bucket")

        # Validate inputs
        if not object_name or not object_name.strip():
            raise ValueError("object_name cannot be empty")
        if not file_path or not file_path.strip():
            raise ValueError("file_path cannot be empty")

        try:
            self.bucket.get_object_to_file(object_name, file_path)
        except IOError as e:
            raise IOError(f"Failed to write file {file_path}: {str(e)}")
        except Exception as e:
            raise AliyunOSSError(f"Failed to download file from Aliyun OSS: {str(e)}")

        return file_path

    def list_objects(self, prefix: str = "") -> List[str]:
        """
        列出 Bucket 中的對象

        Args:
            prefix: 對象名稱前綴

        Returns:
            對象名稱列表
        """
        if not self.bucket:
            raise ValueError("請先設置 Bucket")

        objects = []
        for obj in oss2.ObjectIterator(self.bucket, prefix=prefix):
            objects.append(obj.key)
        return objects

    def delete_object(self, object_name: str):
        """
        刪除對象

        Args:
            object_name: 對象名稱
        """
        if not self.bucket:
            raise ValueError("請先設置 Bucket")

        # Validate inputs
        if not object_name or not object_name.strip():
            raise ValueError("object_name cannot be empty")

        try:
            self.bucket.delete_object(object_name)
        except Exception as e:
            raise AliyunOSSError(f"Failed to delete object from Aliyun OSS: {str(e)}")


class AliyunClient:
    """阿里雲通用客戶端"""

    def __init__(
        self,
        access_key_id: Optional[str] = None,
        access_key_secret: Optional[str] = None,
        region_id: str = "cn-hangzhou"
    ):
        """
        初始化阿里雲客戶端

        Args:
            access_key_id: AccessKey ID
            access_key_secret: AccessKey Secret
            region_id: 地域 ID
        """
        if not HAS_ALIYUN:
            raise ImportError("需要安裝阿里雲 SDK: pip install aliyun-python-sdk-core")

        self.access_key_id = access_key_id or os.getenv("ALIYUN_ACCESS_KEY_ID")
        self.access_key_secret = access_key_secret or os.getenv("ALIYUN_ACCESS_KEY_SECRET")
        self.region_id = region_id

        self.client = AcsClient(
            self.access_key_id,
            self.access_key_secret,
            self.region_id
        )

    def send_request(
        self,
        domain: str,
        version: str,
        action: str,
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        發送通用 API 請求

        Args:
            domain: API 域名
            version: API 版本
            action: API 操作
            params: 請求參數

        Returns:
            響應數據
        """
        request = CommonRequest()
        request.set_domain(domain)
        request.set_version(version)
        request.set_action_name(action)

        for key, value in params.items():
            request.add_query_param(key, value)

        response = self.client.do_action_with_exception(request)
        import json
        return json.loads(response)


__all__ = [
    'AzureStorage',
    'AzureCosmos',
    'AliyunOSS',
    'AliyunClient',
]
