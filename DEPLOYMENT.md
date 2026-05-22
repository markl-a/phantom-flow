# 部署指南

> **完整的 Data Analysis with Chatbots 專案部署指南**
> 涵蓋本地開發、Docker 容器化、生產環境部署的所有細節

## 目錄

1. [本地開發環境](#本地開發環境)
2. [Docker 部署](#docker-部署)
3. [生產環境部署](#生產環境部署)
4. [環境變量配置](#環境變量配置)
5. [監控和日誌](#監控和日誌)
6. [故障排除](#故障排除)
7. [性能優化](#性能優化)

---

## 本地開發環境

### 系統要求

#### 硬件要求
- **CPU**: 雙核及以上（推薦四核）
- **內存**: 最低 4GB（推薦 8GB 或更多）
- **硬盤空間**: 最低 5GB 可用空間（推薦 10GB）
- **網絡**: 穩定的互聯網連接（用於下載 Kaggle 數據集）

#### 軟件要求
- **Python**: 3.8, 3.9, 3.10, 3.11, 或 3.12
- **pip**: 最新版本（運行 `pip install --upgrade pip`）
- **Git**: 2.x 或更高版本
- **（可選）conda**: Miniconda 或 Anaconda

#### 操作系統支持
- **Linux**: Ubuntu 18.04+, Debian 10+, CentOS 7+, Fedora 30+
- **macOS**: 10.14 (Mojave) 或更高版本
- **Windows**: Windows 10/11（推薦使用 WSL2）

### 安裝步驟

#### 方法 1: 使用 pip (推薦)

```bash
# 1. 克隆專案
git clone https://github.com/markl-a/Data-Analysis-with-Chatbots.git
cd Data-Analysis-with-Chatbots

# 2. 創建虛擬環境（推薦）
python -m venv venv

# 3. 激活虛擬環境
# Linux/macOS:
source venv/bin/activate

# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Windows (CMD):
venv\Scripts\activate.bat

# 4. 升級 pip
python -m pip install --upgrade pip

# 5. 安裝依賴
pip install -r requirements.txt

# 6. 安裝專案包（可編輯模式）
pip install -e .

# 7. 安裝開發依賴（可選）
pip install -e ".[dev]"

# 8. 安裝 Jupyter Notebook 支持（可選）
pip install -e ".[notebooks]"

# 9. 安裝 Kaggle API 支持（可選）
pip install -e ".[kaggle]"
```

#### 方法 2: 使用 conda

```bash
# 1. 克隆專案
git clone https://github.com/markl-a/Data-Analysis-with-Chatbots.git
cd Data-Analysis-with-Chatbots

# 2. 創建 conda 環境
conda create -n dac python=3.11

# 3. 激活環境
conda activate dac

# 4. 安裝依賴
pip install -r requirements.txt

# 5. 安裝專案包
pip install -e .
```

### 初始化專案結構

運行以下命令創建必要的目錄結構：

```bash
# 創建完整的目錄結構和示例數據
python -m data_analysis_chatbots.init --with-examples

# 或僅驗證目錄結構是否完整
python -m data_analysis_chatbots.init --validate

# 查看幫助信息
python -m data_analysis_chatbots.init --help
```

這將創建以下目錄：
- `data/raw/` - 原始數據
- `data/processed/` - 處理後的數據
- `data/outputs/` - 分析結果
- `models/` - 訓練好的模型
- `logs/` - 日誌文件
- `outputs/plots/` - 生成的圖表

### 下載數據集

#### 配置 Kaggle API（首次使用）

```bash
# 1. 登錄 Kaggle 網站 (https://www.kaggle.com)
# 2. 進入 Account -> API -> Create New API Token
# 3. 下載 kaggle.json 文件
# 4. 將文件移動到正確位置：

# Linux/macOS:
mkdir -p ~/.kaggle
mv ~/Downloads/kaggle.json ~/.kaggle/
chmod 600 ~/.kaggle/kaggle.json

# Windows:
# 將 kaggle.json 放在 C:\Users\<你的用戶名>\.kaggle\
```

#### 下載數據集

```bash
# 下載所有數據集（約 500MB）
python -m data_analysis_chatbots.data_downloader --all

# 下載特定數據集
python -m data_analysis_chatbots.data_downloader --dataset mall_customers
python -m data_analysis_chatbots.data_downloader --dataset ecommerce
python -m data_analysis_chatbots.data_downloader --dataset personality

# 創建範例數據（用於測試，無需 Kaggle API）
python -m data_analysis_chatbots.data_downloader --sample

# 列出所有可用數據集
python -m data_analysis_chatbots.data_downloader --list
```

### 驗證安裝

```bash
# 運行測試套件
pytest

# 運行快速測試
pytest tests/unit/ -v

# 檢查代碼質量
black --check src/
flake8 src/
isort --check-only src/

# 啟動 Streamlit 應用（驗證 UI）
streamlit run app.py
```

訪問 http://localhost:8501 查看應用是否正常運行。

### 運行示例代碼

```bash
# 運行完整分析工作流
python examples/complete_analysis_workflow.py

# 運行 K-Means 聚類示例
python examples/kmeans_clustering.py

# 運行 RFM 分析示例
python examples/rfm_analysis.py

# 啟動 Jupyter Notebook
jupyter notebook notebooks/
```

---

## Docker 部署

Docker 提供了一致的運行環境，簡化了部署過程。

### 前置要求

- **Docker**: 20.10 或更高版本
- **Docker Compose**: 1.29 或更高版本

安裝 Docker:
- **Linux**: https://docs.docker.com/engine/install/
- **macOS**: https://docs.docker.com/desktop/install/mac-install/
- **Windows**: https://docs.docker.com/desktop/install/windows-install/

### 使用 Docker Compose（推薦）

#### 1. 快速啟動所有服務

```bash
# 構建並啟動所有服務
docker-compose up -d

# 查看運行中的容器
docker-compose ps

# 查看日誌
docker-compose logs -f

# 查看特定服務的日誌
docker-compose logs -f app
docker-compose logs -f jupyter
```

#### 2. 訪問服務

服務啟動後，可以通過以下地址訪問：

- **Streamlit 應用**: http://localhost:8501
- **Jupyter Notebook**: http://localhost:8888
- **Redis**: localhost:6379（僅內部使用）
- **PostgreSQL**: localhost:5432（僅內部使用）

#### 3. 管理服務

```bash
# 停止所有服務
docker-compose stop

# 啟動已停止的服務
docker-compose start

# 重啟服務
docker-compose restart

# 停止並刪除容器
docker-compose down

# 停止並刪除容器、網絡、卷
docker-compose down -v

# 重新構建並啟動
docker-compose up -d --build

# 僅啟動特定服務
docker-compose up -d app
docker-compose up -d jupyter
```

#### 4. 執行命令

```bash
# 在運行中的容器內執行命令
docker-compose exec app bash
docker-compose exec app python -c "import data_analysis_chatbots; print('OK')"

# 運行一次性命令
docker-compose run --rm app python -m data_analysis_chatbots.data_downloader --sample

# 運行測試
docker-compose run --rm app pytest
```

#### 5. 查看健康狀態

```bash
# 查看健康檢查狀態
docker-compose ps

# 查看詳細健康信息
docker inspect dac-app | grep -A 10 Health

# 測試 Streamlit 健康端點
curl http://localhost:8501/healthz
```

### 單獨運行容器

如果不使用 Docker Compose，可以手動運行容器：

#### 1. 構建鏡像

```bash
# 構建 Docker 鏡像
docker build -t data-analysis-chatbots:latest .

# 構建時指定 Python 版本
docker build --build-arg PYTHON_VERSION=3.11 -t data-analysis-chatbots:3.11 .
```

#### 2. 運行容器

```bash
# 運行 Streamlit 應用
docker run -d \
  --name dac-app \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  -v $(pwd)/outputs:/app/outputs \
  -e STREAMLIT_SERVER_PORT=8501 \
  data-analysis-chatbots:latest

# 運行 Jupyter Notebook
docker run -d \
  --name dac-jupyter \
  -p 8888:8888 \
  -v $(pwd)/notebooks:/app/notebooks \
  -v $(pwd)/data:/app/data \
  data-analysis-chatbots:latest \
  jupyter notebook --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token=''

# 查看容器日誌
docker logs -f dac-app

# 進入容器
docker exec -it dac-app bash

# 停止和刪除容器
docker stop dac-app
docker rm dac-app
```

### Docker 最佳實踐

#### 1. 數據持久化

確保重要數據掛載到宿主機：

```yaml
volumes:
  - ./data:/app/data           # 數據文件
  - ./config:/app/config       # 配置文件
  - ./outputs:/app/outputs     # 輸出結果
  - ./models:/app/models       # 訓練模型
  - ./logs:/app/logs           # 日誌文件
```

#### 2. 資源限制

在 docker-compose.yml 中添加資源限制：

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

#### 3. 環境變量

創建 `.env` 文件管理環境變量：

```bash
# .env 文件
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true
PYTHONUNBUFFERED=1
DAC_LOG_LEVEL=INFO
DAC_CONFIG_PATH=config/config.yaml
```

然後在 docker-compose.yml 中引用：

```yaml
services:
  app:
    env_file:
      - .env
```

---

## 生產環境部署

### Streamlit Cloud 部署（推薦新手）

Streamlit Cloud 提供免費的託管服務，非常適合快速部署和分享。

#### 步驟

1. **準備代碼**
   ```bash
   # 確保有 requirements.txt
   # 確保有 app.py（Streamlit 主文件）
   # 提交代碼到 GitHub
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **部署到 Streamlit Cloud**
   - 訪問 https://streamlit.io/cloud
   - 使用 GitHub 賬號登錄
   - 點擊 "New app"
   - 選擇你的 GitHub 倉庫
   - 指定主文件：`app.py`
   - 點擊 "Deploy"

3. **配置 Secrets**
   - 在 Streamlit Cloud 儀表板中
   - Settings -> Secrets
   - 添加敏感配置（如 Kaggle API 密鑰）：
     ```toml
     [kaggle]
     username = "your_username"
     key = "your_api_key"
     ```

4. **自定義域名（可選）**
   - Settings -> General
   - Custom subdomain: `your-app-name`
   - 訪問：`https://your-app-name.streamlit.app`

### 自建服務器部署

適用於需要完全控制和自定義的場景。

#### 選項 1: Ubuntu/Debian 服務器 + Nginx + Systemd

**1. 準備服務器**

```bash
# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝 Python 和依賴
sudo apt install -y python3.11 python3.11-venv python3-pip nginx git

# 創建應用用戶
sudo useradd -m -s /bin/bash dacapp
sudo su - dacapp
```

**2. 部署應用**

```bash
# 克隆代碼
git clone https://github.com/markl-a/Data-Analysis-with-Chatbots.git
cd Data-Analysis-with-Chatbots

# 創建虛擬環境
python3.11 -m venv venv
source venv/bin/activate

# 安裝依賴
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .

# 初始化專案
python -m data_analysis_chatbots.init --with-examples

# 下載數據（可選）
python -m data_analysis_chatbots.data_downloader --sample
```

**3. 配置 Systemd 服務**

創建 `/etc/systemd/system/dac-streamlit.service`：

```ini
[Unit]
Description=Data Analysis Chatbots Streamlit App
After=network.target

[Service]
Type=simple
User=dacapp
Group=dacapp
WorkingDirectory=/home/dacapp/Data-Analysis-with-Chatbots
Environment="PATH=/home/dacapp/Data-Analysis-with-Chatbots/venv/bin"
ExecStart=/home/dacapp/Data-Analysis-with-Chatbots/venv/bin/streamlit run app.py \
    --server.port=8501 \
    --server.address=127.0.0.1 \
    --server.headless=true \
    --server.enableCORS=false \
    --server.enableXsrfProtection=true
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal
SyslogIdentifier=dac-streamlit

[Install]
WantedBy=multi-user.target
```

啟動服務：

```bash
# 重新加載 systemd
sudo systemctl daemon-reload

# 啟動服務
sudo systemctl start dac-streamlit

# 設置開機自啟
sudo systemctl enable dac-streamlit

# 查看狀態
sudo systemctl status dac-streamlit

# 查看日誌
sudo journalctl -u dac-streamlit -f
```

**4. 配置 Nginx 反向代理**

創建 `/etc/nginx/sites-available/dac`：

```nginx
upstream streamlit {
    server 127.0.0.1:8501;
}

server {
    listen 80;
    server_name your-domain.com;

    # 請求大小限制
    client_max_body_size 100M;

    location / {
        proxy_pass http://streamlit;
        proxy_http_version 1.1;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $host;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    # 健康檢查端點
    location /healthz {
        proxy_pass http://streamlit/healthz;
    }
}
```

啟用配置：

```bash
# 創建軟鏈接
sudo ln -s /etc/nginx/sites-available/dac /etc/nginx/sites-enabled/

# 測試配置
sudo nginx -t

# 重新加載 Nginx
sudo systemctl reload nginx
```

**5. 配置 SSL/HTTPS（使用 Let's Encrypt）**

```bash
# 安裝 Certbot
sudo apt install -y certbot python3-certbot-nginx

# 獲取證書並自動配置 Nginx
sudo certbot --nginx -d your-domain.com

# 測試自動續期
sudo certbot renew --dry-run
```

#### 選項 2: Docker + Nginx

**1. 準備 docker-compose.prod.yml**

```yaml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    image: data-analysis-chatbots:latest
    container_name: dac-app-prod
    restart: always
    environment:
      - STREAMLIT_SERVER_PORT=8501
      - STREAMLIT_SERVER_HEADLESS=true
      - STREAMLIT_SERVER_ADDRESS=0.0.0.0
    volumes:
      - ./data:/app/data
      - ./config:/app/config
      - ./outputs:/app/outputs
      - ./logs:/app/logs
    networks:
      - dac-network
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G

  nginx:
    image: nginx:alpine
    container_name: dac-nginx
    restart: always
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    networks:
      - dac-network

networks:
  dac-network:
    driver: bridge
```

**2. 部署**

```bash
# 構建並啟動
docker-compose -f docker-compose.prod.yml up -d --build

# 查看日誌
docker-compose -f docker-compose.prod.yml logs -f

# 滾動更新
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

### AWS EC2 部署示例

```bash
# 1. 啟動 EC2 實例（Amazon Linux 2 或 Ubuntu）
# 2. SSH 連接到實例
ssh -i your-key.pem ec2-user@your-instance-ip

# 3. 安裝 Docker
sudo yum update -y
sudo yum install -y docker
sudo service docker start
sudo usermod -a -G docker ec2-user

# 4. 安裝 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 5. 克隆並部署
git clone https://github.com/markl-a/Data-Analysis-with-Chatbots.git
cd Data-Analysis-with-Chatbots
docker-compose up -d

# 6. 配置安全組
# 允許入站流量：80 (HTTP), 443 (HTTPS), 8501 (Streamlit)
```

### Azure App Service 部署

```bash
# 1. 安裝 Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# 2. 登錄 Azure
az login

# 3. 創建資源組
az group create --name dac-rg --location eastus

# 4. 創建 App Service 計劃
az appservice plan create --name dac-plan --resource-group dac-rg --sku B1 --is-linux

# 5. 創建 Web App
az webapp create --resource-group dac-rg --plan dac-plan --name dac-app --runtime "PYTHON:3.11"

# 6. 部署代碼
az webapp up --name dac-app --resource-group dac-rg --runtime "PYTHON:3.11"
```

---

## 環境變量配置

### 核心環境變量

| 變量名 | 描述 | 默認值 | 示例 |
|--------|------|--------|------|
| `DAC_CONFIG_PATH` | 配置文件路徑 | `config/config.yaml` | `/etc/dac/config.yaml` |
| `DAC_LOG_LEVEL` | 日誌級別 | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `DAC_LOG_DIR` | 日誌目錄 | `logs` | `/var/log/dac` |
| `DAC_DATA_DIR` | 數據根目錄 | `data` | `/data/dac` |
| `DAC_MODEL_DIR` | 模型目錄 | `models` | `/models/dac` |

### Kaggle API 配置

| 變量名 | 描述 | 必需 | 獲取方式 |
|--------|------|------|----------|
| `KAGGLE_USERNAME` | Kaggle 用戶名 | 否* | Kaggle Account Settings |
| `KAGGLE_KEY` | Kaggle API Key | 否* | Kaggle Account -> Create API Token |

\* 如果使用 Kaggle 數據下載功能則必需

### Streamlit 配置

| 變量名 | 描述 | 默認值 |
|--------|------|--------|
| `STREAMLIT_SERVER_PORT` | 服務器端口 | `8501` |
| `STREAMLIT_SERVER_ADDRESS` | 綁定地址 | `0.0.0.0` |
| `STREAMLIT_SERVER_HEADLESS` | 無頭模式 | `true` |
| `STREAMLIT_SERVER_ENABLE_CORS` | 啟用 CORS | `false` |
| `STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION` | 啟用 XSRF 保護 | `true` |

### 數據庫配置（可選）

| 變量名 | 描述 | 默認值 |
|--------|------|--------|
| `POSTGRES_HOST` | PostgreSQL 主機 | `localhost` |
| `POSTGRES_PORT` | PostgreSQL 端口 | `5432` |
| `POSTGRES_DB` | 數據庫名稱 | `dac_db` |
| `POSTGRES_USER` | 數據庫用戶 | `dac_user` |
| `POSTGRES_PASSWORD` | 數據庫密碼 | - |

### 性能配置

| 變量名 | 描述 | 默認值 |
|--------|------|--------|
| `DAC_N_JOBS` | 並行任務數 | `-1`（使用所有CPU） |
| `DAC_CHUNK_SIZE` | 數據塊大小 | `10000` |
| `DAC_CACHE_ENABLED` | 啟用緩存 | `true` |

### 配置示例

#### .env 文件

```bash
# .env
# 核心配置
DAC_CONFIG_PATH=config/config.yaml
DAC_LOG_LEVEL=INFO
DAC_DATA_DIR=/app/data

# Kaggle API
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key

# Streamlit
STREAMLIT_SERVER_PORT=8501
STREAMLIT_SERVER_HEADLESS=true

# 性能
DAC_N_JOBS=4
DAC_CACHE_ENABLED=true
```

#### 在代碼中讀取環境變量

```python
import os
from pathlib import Path
from dotenv import load_dotenv

# 加載 .env 文件
load_dotenv()

# 讀取環境變量
config_path = os.getenv('DAC_CONFIG_PATH', 'config/config.yaml')
log_level = os.getenv('DAC_LOG_LEVEL', 'INFO')
data_dir = Path(os.getenv('DAC_DATA_DIR', 'data'))
```

---

## 監控和日誌

### 日誌配置

專案使用 **Loguru** 進行日誌記錄，配置在 `config/config.yaml`:

```yaml
logging:
  level: "INFO"
  format: "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
  rotation: "10 MB"
  retention: "30 days"
```

### 日誌級別

- **DEBUG**: 詳細的調試信息
- **INFO**: 一般信息（默認）
- **WARNING**: 警告信息
- **ERROR**: 錯誤信息
- **CRITICAL**: 嚴重錯誤

### 查看日誌

#### 本地環境

```bash
# 查看最新日誌
tail -f logs/app.log

# 查看錯誤日誌
grep ERROR logs/app.log

# 查看特定日期的日誌
grep "2025-12-21" logs/app.log
```

#### Docker 環境

```bash
# 查看容器日誌
docker-compose logs -f app

# 查看最近 100 行
docker-compose logs --tail=100 app

# 查看特定時間範圍
docker-compose logs --since 1h app
```

#### Systemd 服務

```bash
# 查看服務日誌
sudo journalctl -u dac-streamlit -f

# 查看最近 100 行
sudo journalctl -u dac-streamlit -n 100

# 查看今天的日誌
sudo journalctl -u dac-streamlit --since today

# 查看錯誤級別日誌
sudo journalctl -u dac-streamlit -p err
```

### 健康檢查

#### HTTP 健康檢查端點

Streamlit 應用提供 `/healthz` 端點：

```bash
# 檢查應用健康狀態
curl http://localhost:8501/healthz

# 預期響應: 200 OK
```

#### Docker 健康檢查

```bash
# 查看容器健康狀態
docker inspect dac-app | grep -A 10 Health

# 查看 docker-compose 服務狀態
docker-compose ps
```

健康檢查配置（在 Dockerfile 中）：

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/healthz')" || exit 1
```

### 性能監控

#### 基本監控

```bash
# CPU 和內存使用
docker stats dac-app

# 磁盤使用
du -sh data/ models/ logs/

# 網絡連接
netstat -tuln | grep 8501
```

#### 進階監控（使用 Prometheus + Grafana）

詳見 `docs/PERFORMANCE_MONITORING.md`

### 錯誤追蹤

#### 捕獲異常

專案使用自定義異常系統（詳見 `src/data_analysis_chatbots/exceptions.py`）：

```python
from data_analysis_chatbots.exceptions import (
    DataLoadError,
    ClusteringError,
    ValidationError
)

try:
    # 你的代碼
    pass
except DataLoadError as e:
    logger.error(f"數據加載失敗: {e}")
    logger.error(f"文件路徑: {e.file_path}")
    logger.error(f"數據集名稱: {e.dataset_name}")
```

#### 常見錯誤模式

查看日誌中的常見錯誤：

```bash
# 統計錯誤類型
grep "ERROR" logs/app.log | cut -d'|' -f3 | sort | uniq -c | sort -rn

# 查找特定錯誤
grep "DataLoadError" logs/app.log

# 查找內存錯誤
grep "MemoryError" logs/app.log
```

---

## 故障排除

### 常見部署問題

#### 1. 端口已被佔用

**錯誤**: `OSError: [Errno 98] Address already in use`

**解決方案**:
```bash
# 查找佔用端口的進程
lsof -i :8501
# 或
netstat -tuln | grep 8501

# 終止進程
kill -9 <PID>

# 或更改端口
streamlit run app.py --server.port=8502
```

#### 2. 權限錯誤

**錯誤**: `PermissionError: [Errno 13] Permission denied`

**解決方案**:
```bash
# 檢查文件權限
ls -la data/ logs/

# 修改權限
chmod -R 755 data/ logs/

# 在 Docker 中，確保正確的用戶
docker-compose exec app chown -R appuser:appuser /app/data
```

#### 3. 內存不足

**錯誤**: `MemoryError` 或 容器被 OOM Killer 終止

**解決方案**:
```bash
# 增加 Docker 內存限制
# 在 docker-compose.yml 中:
deploy:
  resources:
    limits:
      memory: 8G

# 或在運行時指定
docker run --memory=8g ...

# 優化代碼，使用批處理
# 在 config.yaml 中:
performance:
  chunk_size: 5000  # 減小塊大小
```

更多故障排除信息，請參閱 [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## 性能優化

### 應用層優化

#### 1. 數據緩存

```python
import streamlit as st

@st.cache_data
def load_data():
    # 緩存數據加載
    return loader.load_mall_customers()

@st.cache_resource
def load_model():
    # 緩存模型加載
    return pickle.load(open('models/clusterer.pkl', 'rb'))
```

#### 2. 並行處理

```yaml
# config/config.yaml
performance:
  n_jobs: -1  # 使用所有 CPU 核心
  chunk_size: 10000
```

```python
from sklearn.cluster import KMeans

# 使用並行處理
clusterer = KMeans(n_clusters=5, n_jobs=-1)
```

#### 3. 批處理大數據

```python
import pandas as pd

# 使用 chunks 讀取大文件
chunks = pd.read_csv('large_file.csv', chunksize=10000)
for chunk in chunks:
    process_chunk(chunk)
```

### 基礎設施優化

#### 1. 使用生產級 WSGI 服務器

對於高流量場景，考慮使用 Gunicorn:

```bash
# 安裝 Gunicorn
pip install gunicorn

# 運行（不適用於 Streamlit，僅用於 Flask/Django）
# gunicorn -w 4 -b 0.0.0.0:8000 app:server
```

#### 2. 負載均衡

使用 Nginx 或 HAProxy 進行負載均衡：

```nginx
upstream streamlit_backend {
    server 127.0.0.1:8501;
    server 127.0.0.1:8502;
    server 127.0.0.1:8503;
}

server {
    listen 80;
    location / {
        proxy_pass http://streamlit_backend;
    }
}
```

#### 3. CDN 加速

- 使用 Cloudflare 或 AWS CloudFront 加速靜態資源
- 配置適當的緩存策略

#### 4. 數據庫優化

如果使用 PostgreSQL:

```sql
-- 創建索引
CREATE INDEX idx_customer_id ON customers(customer_id);
CREATE INDEX idx_invoice_date ON transactions(invoice_date);

-- 定期 VACUUM
VACUUM ANALYZE;
```

### 監控性能指標

```bash
# 安裝性能分析工具
pip install py-spy

# 分析 Python 應用
py-spy top --pid <PID>

# 生成火焰圖
py-spy record -o profile.svg --pid <PID>
```

---

## 安全最佳實踐

### 1. 敏感信息管理

- **永遠不要**在代碼中硬編碼密碼或 API 密鑰
- 使用環境變量或密鑰管理服務
- 將 `.env` 添加到 `.gitignore`

### 2. HTTPS 強制

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    # SSL 配置...
}
```

### 3. 防火牆配置

```bash
# 使用 ufw (Ubuntu)
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 4. 定期更新依賴

```bash
# 檢查安全漏洞
pip install safety
safety check

# 更新依賴
pip list --outdated
pip install --upgrade package-name
```

---

## 備份和恢復

### 備份策略

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backups/dac"
DATE=$(date +%Y%m%d_%H%M%S)

# 備份數據
tar -czf $BACKUP_DIR/data_$DATE.tar.gz data/

# 備份模型
tar -czf $BACKUP_DIR/models_$DATE.tar.gz models/

# 備份配置
tar -czf $BACKUP_DIR/config_$DATE.tar.gz config/

# 刪除 30 天前的備份
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
```

### 自動備份（cron）

```bash
# 編輯 crontab
crontab -e

# 每天凌晨 2 點執行備份
0 2 * * * /path/to/backup.sh
```

---

## 參考資源

- **官方文檔**: [README.md](README.md)
- **故障排除**: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **架構設計**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **FAQ**: [FAQ.md](FAQ.md)
- **Docker 文檔**: https://docs.docker.com
- **Streamlit 文檔**: https://docs.streamlit.io
- **Nginx 文檔**: https://nginx.org/en/docs

---

**最後更新**: 2025-12-21
**版本**: 1.0.0
