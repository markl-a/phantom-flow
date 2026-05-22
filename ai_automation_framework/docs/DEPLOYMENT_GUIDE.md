# 部署指南 (Deployment Guide)

本指南提供了在各種雲平台上部署 AI Automation Framework 的詳細步驟。

## 目錄

- [Docker 部署](#docker-部署)
- [AWS 部署](#aws-部署)
- [Azure 部署](#azure-部署)
- [Google Cloud 部署](#google-cloud-部署)
- [監控和日誌](#監控和日誌)
- [擴展和優化](#擴展和優化)
- [故障排除](#故障排除)

---

## Docker 部署

### 本地 Docker 運行

#### 1. 基本部署

```bash
# 構建 Docker 映像
docker build -t ai-automation-framework .

# 運行容器
docker run -d \
  --name ai-automation \
  -p 8000:8000 \
  -p 8501:8501 \
  -e OPENAI_API_KEY=your_key \
  -e ANTHROPIC_API_KEY=your_key \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  ai-automation-framework
```

#### 2. Docker Compose 部署

```bash
# 複製環境變量文件
cp .env.example .env
# 編輯 .env 文件，添加您的 API 密鑰

# 啟動所有服務
docker-compose up -d

# 查看日誌
docker-compose logs -f ai-automation

# 停止服務
docker-compose down

# 完全清理（包括數據卷）
docker-compose down -v
```

#### 3. 服務訪問

- **主應用**: http://localhost:8000
- **Streamlit 演示**: http://localhost:8501
- **Grafana 監控**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **ChromaDB**: http://localhost:8001

---

## AWS 部署

### 選項 1: Amazon ECS (Elastic Container Service)

#### 前置需求

```bash
# 安裝 AWS CLI
pip install awscli

# 配置 AWS 憑證
aws configure
```

#### 步驟 1: 創建 ECR 倉庫

```bash
# 創建 ECR 倉庫
aws ecr create-repository \
  --repository-name ai-automation-framework \
  --region us-east-1

# 獲取登錄令牌
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com
```

#### 步驟 2: 構建並推送映像

```bash
# 構建映像
docker build -t ai-automation-framework .

# 標記映像
docker tag ai-automation-framework:latest \
  <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-automation-framework:latest

# 推送到 ECR
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-automation-framework:latest
```

#### 步驟 3: 創建 ECS 集群

```bash
# 創建 ECS 集群
aws ecs create-cluster --cluster-name ai-automation-cluster

# 創建任務定義
cat > task-definition.json <<EOF
{
  "family": "ai-automation-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "containerDefinitions": [
    {
      "name": "ai-automation",
      "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/ai-automation-framework:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {"name": "LOG_LEVEL", "value": "INFO"}
      ],
      "secrets": [
        {
          "name": "OPENAI_API_KEY",
          "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:openai-api-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/ai-automation",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
EOF

# 註冊任務定義
aws ecs register-task-definition --cli-input-json file://task-definition.json
```

#### 步驟 4: 創建服務

```bash
# 創建服務
aws ecs create-service \
  --cluster ai-automation-cluster \
  --service-name ai-automation-service \
  --task-definition ai-automation-task \
  --desired-count 2 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}" \
  --load-balancers "targetGroupArn=arn:aws:elasticloadbalancing:...,containerName=ai-automation,containerPort=8000"
```

### 選項 2: AWS Lambda (無伺服器)

#### 創建 Lambda 函數

```bash
# 安裝依賴到本地目錄
pip install -r requirements.txt -t lambda_package/

# 複製代碼
cp -r ai_automation_framework lambda_package/

# 創建部署包
cd lambda_package
zip -r ../lambda_function.zip .

# 創建 Lambda 函數
aws lambda create-function \
  --function-name ai-automation-lambda \
  --runtime python3.11 \
  --handler ai_automation_framework.lambda_handler \
  --zip-file fileb://../lambda_function.zip \
  --role arn:aws:iam::<account-id>:role/lambda-execution-role \
  --timeout 300 \
  --memory-size 3008 \
  --environment Variables={OPENAI_API_KEY=xxx,ANTHROPIC_API_KEY=xxx}
```

### 選項 3: AWS Elastic Beanstalk

```bash
# 安裝 EB CLI
pip install awsebcli

# 初始化 Elastic Beanstalk 應用
eb init -p docker ai-automation-app

# 創建環境並部署
eb create ai-automation-env

# 部署更新
eb deploy

# 查看日誌
eb logs
```

---

## Azure 部署

### 選項 1: Azure Container Instances (ACI)

#### 前置需求

```bash
# 安裝 Azure CLI
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# 登錄
az login
```

#### 步驟 1: 創建資源組

```bash
# 創建資源組
az group create \
  --name ai-automation-rg \
  --location eastus
```

#### 步驟 2: 創建 Container Registry

```bash
# 創建 ACR
az acr create \
  --resource-group ai-automation-rg \
  --name aiautomationacr \
  --sku Basic

# 登錄到 ACR
az acr login --name aiautomationacr
```

#### 步驟 3: 構建並推送映像

```bash
# 使用 ACR 構建
az acr build \
  --registry aiautomationacr \
  --image ai-automation-framework:latest \
  .
```

#### 步驟 4: 部署到 Container Instances

```bash
# 創建容器實例
az container create \
  --resource-group ai-automation-rg \
  --name ai-automation-container \
  --image aiautomationacr.azurecr.io/ai-automation-framework:latest \
  --cpu 2 \
  --memory 4 \
  --ports 8000 8501 \
  --dns-name-label ai-automation-app \
  --environment-variables \
    'LOG_LEVEL'='INFO' \
  --secure-environment-variables \
    'OPENAI_API_KEY'='your_key' \
    'ANTHROPIC_API_KEY'='your_key' \
  --registry-login-server aiautomationacr.azurecr.io \
  --registry-username aiautomationacr \
  --registry-password $(az acr credential show --name aiautomationacr --query "passwords[0].value" -o tsv)

# 查看容器狀態
az container show \
  --resource-group ai-automation-rg \
  --name ai-automation-container \
  --query "{FQDN:ipAddress.fqdn,ProvisioningState:provisioningState}" \
  --out table
```

### 選項 2: Azure Kubernetes Service (AKS)

#### 創建 AKS 集群

```bash
# 創建 AKS 集群
az aks create \
  --resource-group ai-automation-rg \
  --name ai-automation-aks \
  --node-count 3 \
  --node-vm-size Standard_D4s_v3 \
  --enable-managed-identity \
  --attach-acr aiautomationacr

# 獲取憑證
az aks get-credentials \
  --resource-group ai-automation-rg \
  --name ai-automation-aks

# 部署到 Kubernetes
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

### 選項 3: Azure App Service

```bash
# 創建 App Service 計劃
az appservice plan create \
  --name ai-automation-plan \
  --resource-group ai-automation-rg \
  --sku B2 \
  --is-linux

# 創建 Web App
az webapp create \
  --resource-group ai-automation-rg \
  --plan ai-automation-plan \
  --name ai-automation-webapp \
  --deployment-container-image-name aiautomationacr.azurecr.io/ai-automation-framework:latest

# 配置環境變量
az webapp config appsettings set \
  --resource-group ai-automation-rg \
  --name ai-automation-webapp \
  --settings \
    OPENAI_API_KEY=your_key \
    ANTHROPIC_API_KEY=your_key
```

---

## Google Cloud 部署

### 選項 1: Cloud Run (推薦)

#### 前置需求

```bash
# 安裝 gcloud CLI
curl https://sdk.cloud.google.com | bash

# 初始化並登錄
gcloud init
gcloud auth login
```

#### 步驟 1: 設置項目

```bash
# 設置項目 ID
export PROJECT_ID=your-project-id
gcloud config set project $PROJECT_ID

# 啟用必要的 API
gcloud services enable \
  run.googleapis.com \
  containerregistry.googleapis.com \
  cloudbuild.googleapis.com
```

#### 步驟 2: 構建並推送映像

```bash
# 使用 Cloud Build 構建映像
gcloud builds submit --tag gcr.io/$PROJECT_ID/ai-automation-framework

# 或使用本地 Docker
docker build -t gcr.io/$PROJECT_ID/ai-automation-framework .
docker push gcr.io/$PROJECT_ID/ai-automation-framework
```

#### 步驟 3: 部署到 Cloud Run

```bash
# 部署服務
gcloud run deploy ai-automation-service \
  --image gcr.io/$PROJECT_ID/ai-automation-framework \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 4Gi \
  --cpu 2 \
  --max-instances 10 \
  --set-env-vars "LOG_LEVEL=INFO" \
  --set-secrets "OPENAI_API_KEY=openai-key:latest,ANTHROPIC_API_KEY=anthropic-key:latest"

# 獲取服務 URL
gcloud run services describe ai-automation-service \
  --region us-central1 \
  --format 'value(status.url)'
```

### 選項 2: Google Kubernetes Engine (GKE)

#### 創建 GKE 集群

```bash
# 創建 GKE 集群
gcloud container clusters create ai-automation-cluster \
  --num-nodes 3 \
  --machine-type n1-standard-4 \
  --zone us-central1-a \
  --enable-autoscaling \
  --min-nodes 1 \
  --max-nodes 10

# 獲取憑證
gcloud container clusters get-credentials ai-automation-cluster \
  --zone us-central1-a

# 部署應用
kubectl apply -f k8s/
```

### 選項 3: Compute Engine (VM)

```bash
# 創建 VM 實例
gcloud compute instances create ai-automation-vm \
  --machine-type n1-standard-4 \
  --zone us-central1-a \
  --image-family ubuntu-2204-lts \
  --image-project ubuntu-os-cloud \
  --boot-disk-size 50GB \
  --tags http-server,https-server

# SSH 到 VM
gcloud compute ssh ai-automation-vm --zone us-central1-a

# 在 VM 上安裝 Docker 和部署
# (在 VM 內執行)
sudo apt-get update
sudo apt-get install -y docker.io docker-compose
sudo usermod -aG docker $USER
# 然後使用 docker-compose 部署
```

---

## 監控和日誌

### Prometheus 監控

#### 配置應用指標

在應用中添加 Prometheus 指標：

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# 創建指標
request_count = Counter('app_requests_total', 'Total requests')
request_duration = Histogram('app_request_duration_seconds', 'Request duration')
active_users = Gauge('app_active_users', 'Active users')

# 在應用中使用
@app.route('/api/chat')
def chat():
    request_count.inc()
    with request_duration.time():
        # 處理請求
        pass
```

### CloudWatch (AWS)

```bash
# 創建 CloudWatch 日誌組
aws logs create-log-group --log-group-name /ai-automation/app

# 創建指標過濾器
aws logs put-metric-filter \
  --log-group-name /ai-automation/app \
  --filter-name ErrorCount \
  --filter-pattern "[ERROR]" \
  --metric-transformations \
    metricName=ErrorCount,metricNamespace=AIAutomation,metricValue=1

# 創建告警
aws cloudwatch put-metric-alarm \
  --alarm-name high-error-rate \
  --alarm-description "Alert on high error rate" \
  --metric-name ErrorCount \
  --namespace AIAutomation \
  --statistic Sum \
  --period 300 \
  --threshold 10 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 1
```

### Azure Monitor

```bash
# 啟用 Application Insights
az monitor app-insights component create \
  --app ai-automation-insights \
  --location eastus \
  --resource-group ai-automation-rg

# 獲取 Instrumentation Key
INSTRUMENTATION_KEY=$(az monitor app-insights component show \
  --app ai-automation-insights \
  --resource-group ai-automation-rg \
  --query instrumentationKey -o tsv)

# 在容器中設置環境變量
az container create \
  ... \
  --environment-variables \
    'APPINSIGHTS_INSTRUMENTATIONKEY'=$INSTRUMENTATION_KEY
```

### Google Cloud Monitoring

```bash
# 已自動集成到 Cloud Run 和 GKE
# 查看日誌
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ai-automation-service" \
  --limit 50 \
  --format json

# 創建告警策略
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="High Error Rate" \
  --condition-display-name="Error rate > 5%" \
  --condition-threshold-value=5 \
  --condition-threshold-duration=60s
```

---

## 擴展和優化

### 水平擴展

#### AWS ECS Auto Scaling

```bash
# 註冊可擴展目標
aws application-autoscaling register-scalable-target \
  --service-namespace ecs \
  --resource-id service/ai-automation-cluster/ai-automation-service \
  --scalable-dimension ecs:service:DesiredCount \
  --min-capacity 2 \
  --max-capacity 10

# 創建擴展策略
aws application-autoscaling put-scaling-policy \
  --policy-name cpu-scaling \
  --service-namespace ecs \
  --resource-id service/ai-automation-cluster/ai-automation-service \
  --scalable-dimension ecs:service:DesiredCount \
  --policy-type TargetTrackingScaling \
  --target-tracking-scaling-policy-configuration \
    '{"TargetValue": 70.0, "PredefinedMetricSpecification": {"PredefinedMetricType": "ECSServiceAverageCPUUtilization"}}'
```

#### Azure Auto Scaling

```bash
# 創建自動擴展規則
az monitor autoscale create \
  --resource-group ai-automation-rg \
  --resource ai-automation-container \
  --resource-type Microsoft.ContainerInstance/containerGroups \
  --name autoscale-rule \
  --min-count 2 \
  --max-count 10 \
  --count 2

az monitor autoscale rule create \
  --resource-group ai-automation-rg \
  --autoscale-name autoscale-rule \
  --condition "Percentage CPU > 70 avg 5m" \
  --scale out 1
```

#### GCP Cloud Run Auto Scaling

```bash
# Cloud Run 自動擴展（已內建）
gcloud run services update ai-automation-service \
  --min-instances 2 \
  --max-instances 100 \
  --concurrency 80 \
  --cpu-throttling \
  --region us-central1
```

### 性能優化

#### 1. 緩存策略

```python
# 使用 Redis 緩存
import redis
from functools import lru_cache

redis_client = redis.Redis(host='redis', port=6379, db=0)

def cache_response(key, ttl=3600):
    def decorator(func):
        def wrapper(*args, **kwargs):
            cached = redis_client.get(key)
            if cached:
                return json.loads(cached)
            result = func(*args, **kwargs)
            redis_client.setex(key, ttl, json.dumps(result))
            return result
        return wrapper
    return decorator
```

#### 2. 連接池

```python
# 數據庫連接池
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=0,
    pool_pre_ping=True
)
```

#### 3. 異步處理

```python
# 使用 Celery 進行後台任務
from celery import Celery

celery = Celery('tasks', broker='redis://redis:6379/0')

@celery.task
def process_large_document(document_id):
    # 處理大型文檔
    pass
```

---

## 故障排除

### 常見問題

#### 1. 容器無法啟動

```bash
# 檢查容器日誌
docker logs ai-automation

# 檢查容器狀態
docker inspect ai-automation

# 進入容器調試
docker exec -it ai-automation /bin/bash
```

#### 2. API 密鑰問題

```bash
# 驗證環境變量
docker exec ai-automation env | grep API_KEY

# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id openai-api-key

# Azure Key Vault
az keyvault secret show --vault-name your-vault --name openai-api-key

# GCP Secret Manager
gcloud secrets versions access latest --secret="openai-api-key"
```

#### 3. 內存不足

```bash
# 增加容器內存限制
docker run -m 8g ai-automation-framework

# Docker Compose
# 在 docker-compose.yml 中添加：
services:
  ai-automation:
    deploy:
      resources:
        limits:
          memory: 8G
```

#### 4. 網絡連接問題

```bash
# 檢查網絡
docker network ls
docker network inspect ai-automation-network

# 測試連接
docker exec ai-automation ping redis
docker exec ai-automation curl http://chroma:8000/api/v1/heartbeat
```

### 日誌收集

#### Centralized Logging

```bash
# 使用 ELK Stack
docker run -d \
  --name elasticsearch \
  -p 9200:9200 \
  elasticsearch:8.5.0

docker run -d \
  --name logstash \
  -p 5000:5000 \
  logstash:8.5.0

docker run -d \
  --name kibana \
  -p 5601:5601 \
  kibana:8.5.0
```

### 性能分析

```bash
# 使用 cProfile
python -m cProfile -o profile.stats your_script.py

# 使用 py-spy
py-spy record -o profile.svg --pid <pid>

# 使用 memory_profiler
python -m memory_profiler your_script.py
```

---

## 安全最佳實踐

### 1. API 密鑰管理

- 永不將 API 密鑰硬編碼在代碼中
- 使用雲平台的密鑰管理服務
- 定期輪換密鑰
- 使用環境變量或密鑰管理服務

### 2. 網絡安全

```bash
# 使用 HTTPS
# 配置 SSL/TLS 證書（Let's Encrypt）
certbot certonly --standalone -d your-domain.com

# 限制 IP 訪問
# 在安全組或防火牆中配置
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxx \
  --protocol tcp \
  --port 8000 \
  --cidr 1.2.3.4/32
```

### 3. 容器安全

```bash
# 掃描映像漏洞
docker scan ai-automation-framework

# 使用非 root 用戶
# 在 Dockerfile 中添加：
USER nobody
```

---

## 成本優化

### AWS 成本優化

- 使用 Spot Instances 進行非關鍵工作負載
- 啟用 S3 生命週期策略
- 使用 Reserved Instances 進行長期部署
- 監控 CloudWatch 指標以識別未使用的資源

### Azure 成本優化

- 使用 Azure Cost Management
- 利用 Reserved VM Instances
- 自動關閉開發/測試環境

### GCP 成本優化

- 使用 Committed Use Discounts
- 啟用 Cloud Run 的最小實例數為 0（按需計費）
- 使用 Preemptible VMs

---

## 備份和災難恢復

### 數據備份

```bash
# PostgreSQL 備份
docker exec postgres pg_dump -U postgres ai_automation > backup.sql

# ChromaDB 備份
docker cp ai-automation-chroma:/chroma/chroma ./chroma_backup

# 自動化備份腳本
cat > backup.sh <<'EOF'
#!/bin/bash
BACKUP_DIR=/backups/$(date +%Y%m%d)
mkdir -p $BACKUP_DIR
docker exec postgres pg_dump -U postgres ai_automation > $BACKUP_DIR/db.sql
docker cp ai-automation-chroma:/chroma/chroma $BACKUP_DIR/chroma
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
EOF

# 設置 cron 任務
0 2 * * * /path/to/backup.sh
```

### 災難恢復

```bash
# 恢復 PostgreSQL
docker exec -i postgres psql -U postgres -d ai_automation < backup.sql

# 恢復 ChromaDB
docker cp ./chroma_backup ai-automation-chroma:/chroma/chroma
docker restart ai-automation-chroma
```

---

## 總結

本指南涵蓋了在各種雲平台上部署 AI Automation Framework 的完整流程。根據您的需求選擇合適的部署選項：

- **快速原型**: Docker Compose 或 Cloud Run
- **生產環境**: ECS/EKS、AKS 或 GKE
- **無伺服器**: AWS Lambda、Azure Functions 或 Cloud Functions
- **成本優化**: Cloud Run 或 Container Instances

記得根據實際情況調整資源配置、監控設置和安全措施。
