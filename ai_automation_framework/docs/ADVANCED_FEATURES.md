# Advanced Automation Features Documentation

This document describes all advanced automation features added to the AI Automation Framework.

## Table of Contents

1. [Email Automation](#1-email-automation)
2. [Database Automation](#2-database-automation)
3. [Web Scraping](#3-web-scraping)
4. [Task Scheduler](#4-task-scheduler)
5. [API Testing](#5-api-testing)
6. [Excel/CSV Processing](#6-excelcsv-processing)
7. [Image Processing & OCR](#7-image-processing--ocr)
8. [Messaging Platforms (Slack/Discord)](#8-messaging-platforms)
9. [Git Automation](#9-git-automation)
10. [Cloud Storage (S3/GCS)](#10-cloud-storage)
11. [Browser Automation](#11-browser-automation)
12. [PDF Processing](#12-pdf-processing)
13. [External Framework Integrations](#13-external-framework-integrations)

---

## 1. Email Automation

**Module**: `ai_automation_framework.tools.advanced_automation.EmailAutomationTool`

### Features
- Send emails via SMTP
- Read emails via IMAP
- HTML email support
- Attachment handling
- Email filtering

### Example
```python
from ai_automation_framework.tools.advanced_automation import EmailAutomationTool

# Initialize
email_tool = EmailAutomationTool(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    imap_server="imap.gmail.com",
    imap_port=993
)

# Send email
result = email_tool.send_email(
    sender="your@email.com",
    password="your_app_password",
    recipient="recipient@email.com",
    subject="Daily Report",
    body="<h1>Report</h1><p>Content here...</p>",
    html=True
)

# Read emails
emails = email_tool.read_emails(
    username="your@email.com",
    password="your_password",
    folder="INBOX",
    limit=10,
    unread_only=True
)
```

### Use Cases
- Automated daily reports
- Alert systems
- Customer notifications
- Email-based workflows

---

## 2. Database Automation

**Module**: `ai_automation_framework.tools.advanced_automation.DatabaseAutomationTool`

### Features
- SQL query generation
- CRUD operations
- Schema management
- Aggregation queries
- Transaction support

### Example
```python
from ai_automation_framework.tools.advanced_automation import DatabaseAutomationTool

# Initialize (SQLite example)
db = DatabaseAutomationTool("database.db")
db.connect()

# Create table
schema = {
    "id": "INTEGER PRIMARY KEY",
    "name": "TEXT",
    "email": "TEXT UNIQUE"
}
db.create_table("users", schema)

# Generate and execute INSERT
query, values = db.generate_insert_query("users", {
    "name": "John Doe",
    "email": "john@example.com"
})
db.execute_query(query, values)

# Generate SELECT query
query = db.generate_select_query("users", where={"name": "John Doe"})
result = db.execute_query(query)
```

### Use Cases
- Data ETL pipelines
- Report generation
- Data validation
- Application backends

---

## 3. Web Scraping

**Module**: `ai_automation_framework.tools.advanced_automation.WebScraperTool`

### Features
- HTTP requests
- HTML parsing
- Link extraction
- Table parsing
- Text extraction

### Example
```python
from ai_automation_framework.tools.advanced_automation import WebScraperTool

scraper = WebScraperTool()

# Fetch webpage
result = scraper.fetch_url("https://example.com")

# Extract links
links = scraper.extract_links(result['content'], base_url="https://example.com")

# Extract tables
tables = scraper.extract_table_data(result['content'])

# Extract specific elements
text = scraper.extract_text(result['content'], tag='h2')
```

### Use Cases
- Price monitoring
- Content aggregation
- Data collection
- Market research

---

## 4. Task Scheduler

**Module**: `ai_automation_framework.tools.scheduler_and_testing.TaskScheduler`

### Features
- Cron-like scheduling
- Multiple time intervals
- Background execution
- Job management

### Example
```python
from ai_automation_framework.tools.scheduler_and_testing import TaskScheduler

scheduler = TaskScheduler()

# Schedule function to run every hour
def backup_data():
    print("Running backup...")

scheduler.schedule_task(backup_data, 'hours', interval=1)

# Schedule daily task at specific time
scheduler.schedule_task(generate_report, 'daily', at_time='09:00')

# Start scheduler
scheduler.start()
```

### Use Cases
- Automated backups
- Periodic reports
- Health checks
- Data synchronization

---

## 5. API Testing

**Module**: `ai_automation_framework.tools.scheduler_and_testing.APITestingTool`

### Features
- Endpoint testing
- Load testing
- Schema validation
- Performance metrics
- Test reporting

### Example
```python
from ai_automation_framework.tools.scheduler_and_testing import APITestingTool

tester = APITestingTool()

# Test single endpoint
result = tester.test_endpoint(
    url="https://api.example.com/users",
    method="GET",
    expected_status=200
)

# Test multiple endpoints
endpoints = [
    {"url": "https://api.example.com/users", "method": "GET"},
    {"url": "https://api.example.com/posts", "method": "GET"}
]
results = tester.test_multiple_endpoints(endpoints)

# Load test
load_result = tester.load_test(
    url="https://api.example.com/users",
    num_requests=100,
    concurrent=True
)

# Generate report
report = tester.get_test_report()
```

### Use Cases
- CI/CD pipeline testing
- API monitoring
- Performance testing
- Contract testing

---

## 6. Excel/CSV Processing

**Module**: `ai_automation_framework.tools.data_processing`

### Features
- Read/write Excel files
- CSV processing
- Data aggregation
- Statistical analysis
- File merging

### Example
```python
from ai_automation_framework.tools.data_processing import ExcelAutomationTool, CSVProcessingTool

excel = ExcelAutomationTool()

# Write Excel with auto-formatting
data = [
    {"name": "Product A", "sales": 1000},
    {"name": "Product B", "sales": 1500}
]
excel.write_excel("report.xlsx", data, auto_format=True)

# Read Excel
result = excel.read_excel("report.xlsx")

# Excel to CSV conversion
excel.excel_to_csv("report.xlsx", "report.csv")

# Merge multiple Excel files
excel.merge_excel_files(["file1.xlsx", "file2.xlsx"], "merged.xlsx")
```

### Use Cases
- Report generation
- Data analysis
- Business intelligence
- File format conversion

---

## 7. Image Processing & OCR

**Module**: `ai_automation_framework.tools.media_messaging`

### Features
- Image resizing/cropping
- Format conversion
- Filters and effects
- OCR (text extraction)
- Thumbnail generation

### Example
```python
from ai_automation_framework.tools.media_messaging import ImageProcessingTool, OCRTool

img_tool = ImageProcessingTool()

# Resize image
img_tool.resize_image("input.jpg", "output.jpg", 800, 600)

# Apply filter
img_tool.apply_filter("input.jpg", "output.jpg", "SHARPEN")

# Create thumbnail
img_tool.create_thumbnail("input.jpg", "thumb.jpg", size=(128, 128))

# OCR - Extract text from image
ocr = OCRTool()
result = ocr.extract_text_from_image("document.png")
```

### Use Cases
- Image optimization
- Document digitization
- Receipt processing
- Media pipelines

---

## 8. Messaging Platforms

**Modules**: `SlackTool`, `DiscordTool`

### Features
- Send messages
- Upload files
- Webhook support
- Rich formatting

### Example
```python
from ai_automation_framework.tools.media_messaging import SlackTool, DiscordTool

# Slack
slack = SlackTool(webhook_url="https://hooks.slack.com/...")
slack.send_message("Deployment successful! 🚀")

# Discord
discord = DiscordTool(webhook_url="https://discord.com/api/webhooks/...")
discord.send_embed(
    title="Alert",
    description="Server CPU usage high!",
    color=0xff0000
)
```

### Use Cases
- Team notifications
- Alert systems
- Bot interactions
- Monitoring alerts

---

## 9. Git Automation

**Module**: `ai_automation_framework.tools.devops_cloud.GitAutomationTool`

### Features
- Clone/pull/push operations
- Commit management
- Branch operations
- Merge support

### Example
```python
from ai_automation_framework.tools.devops_cloud import GitAutomationTool

git = GitAutomationTool("/path/to/repo")

# Get status
status = git.status()

# Add and commit
git.add(".")
git.commit("Auto-commit: daily update")

# Push to remote
git.push("origin", "main")

# Create branch
git.create_branch("feature/new-feature")
```

### Use Cases
- Automated commits
- CI/CD pipelines
- Repository synchronization
- Backup automation

---

## 10. Cloud Storage

**Module**: `ai_automation_framework.tools.devops_cloud.CloudStorageTool`

### Features
- AWS S3 support
- Google Cloud Storage
- Upload/download files
- Object listing

### Example
```python
from ai_automation_framework.tools.devops_cloud import CloudStorageTool

# S3
cloud = CloudStorageTool(
    provider="s3",
    aws_access_key_id="your_key",
    aws_secret_access_key="your_secret"
)

# Upload file
cloud.upload_file_s3("local.txt", "my-bucket", "remote.txt")

# Download file
cloud.download_file_s3("my-bucket", "remote.txt", "downloaded.txt")

# List objects
objects = cloud.list_objects_s3("my-bucket", prefix="folder/")
```

### Use Cases
- Cloud backups
- CDN file uploads
- Data archiving
- File distribution

---

## 11. Browser Automation

**Module**: `ai_automation_framework.tools.devops_cloud.BrowserAutomationTool`

### Features
- Selenium support
- Page navigation
- Form filling
- Screenshots
- Element interaction

### Example
```python
from ai_automation_framework.tools.devops_cloud import BrowserAutomationTool

browser = BrowserAutomationTool(driver_type="selenium", headless=True)

# Navigate to page
browser.navigate("https://example.com")

# Get page text
text = browser.get_page_text()

# Take screenshot
browser.screenshot("page.png")

# Fill form
browser.fill_form("username", "myuser")
browser.click_element("submit-button")

# Close browser
browser.close()
```

### Use Cases
- Web testing
- Data scraping
- UI automation
- Form submissions

---

## 12. PDF Processing

**Module**: `ai_automation_framework.tools.devops_cloud.PDFAdvancedTool`

### Features
- PDF merging
- PDF splitting
- Text extraction
- PDF generation

### Example
```python
from ai_automation_framework.tools.devops_cloud import PDFAdvancedTool

pdf = PDFAdvancedTool()

# Merge PDFs
pdf.merge_pdfs(["file1.pdf", "file2.pdf"], "merged.pdf")

# Split PDF into pages
pdf.split_pdf("document.pdf", "output_dir/")

# Extract text
text = pdf.extract_pdf_text("document.pdf")

# Create PDF from text
pdf.create_pdf_from_text("Hello World!", "output.pdf")
```

### Use Cases
- Document processing
- Report generation
- Archiving
- Document management

---

## 13. External Framework Integrations

### Zapier Integration

**Module**: `ai_automation_framework.integrations.ZapierIntegration`

```python
from ai_automation_framework.integrations import ZapierIntegration

zap = ZapierIntegration(webhook_url="https://hooks.zapier.com/...")

# Trigger zap
zap.trigger_zap({"name": "John", "event": "signup"})

# Send email via zap
zap.send_email_via_zap("user@example.com", "Welcome!", "Thanks for signing up!")
```

### n8n Integration

**Module**: `ai_automation_framework.integrations.N8NIntegration`

```python
from ai_automation_framework.integrations import N8NIntegration

n8n = N8NIntegration(base_url="https://n8n.example.com", api_key="your_key")

# Trigger workflow
n8n.trigger_webhook("/webhook/process-data", {"data": "value"})

# Execute workflow
n8n.execute_workflow("workflow-id", {"input": "data"})
```

### Airflow Integration

**Module**: `ai_automation_framework.integrations.AirflowIntegration`

```python
from ai_automation_framework.integrations import AirflowIntegration

airflow = AirflowIntegration(
    base_url="http://localhost:8080",
    username="admin",
    password="admin"
)

# Trigger DAG
airflow.trigger_dag("my_dag", conf={"param": "value"})

# Get DAG status
status = airflow.get_dag_status("my_dag", "run_id")

# Generate DAG template
code = airflow.generate_dag_template(
    "my_dag",
    "My workflow",
    tasks=["extract", "transform", "load"]
)
```

---

## Complete Feature Matrix

| Feature | Module | Tested | Production Ready |
|---------|--------|--------|------------------|
| Email Automation | `advanced_automation` | ✅ | ✅ |
| Database Automation | `advanced_automation` | ✅ | ✅ |
| Web Scraping | `advanced_automation` | ✅ | ✅ |
| Task Scheduler | `scheduler_and_testing` | ✅ | ✅ |
| API Testing | `scheduler_and_testing` | ✅ | ✅ |
| Excel/CSV Processing | `data_processing` | ✅ | ✅ |
| Image Processing | `media_messaging` | ✅ | ✅ |
| OCR | `media_messaging` | ✅ | ✅ |
| Slack Integration | `media_messaging` | ✅ | ✅ |
| Discord Integration | `media_messaging` | ✅ | ✅ |
| Git Automation | `devops_cloud` | ✅ | ✅ |
| Cloud Storage | `devops_cloud` | ✅ | ✅ |
| Browser Automation | `devops_cloud` | ✅ | ✅ |
| PDF Processing | `devops_cloud` | ✅ | ✅ |
| Zapier Integration | `integrations` | ✅ | ✅ |
| n8n Integration | `integrations` | ✅ | ✅ |
| Airflow Integration | `integrations` | ✅ | ✅ |

**Total: 17 Advanced Features** ✨

---

## Examples

All features have working examples in:
```
examples/level4_advanced_automation/
├── 01_email_automation_example.py
├── 02_database_automation_example.py
├── 03_web_scraping_example.py
├── 04_scheduler_example.py
├── 05_api_testing_example.py
├── 06_excel_csv_example.py
└── 07_all_features_demo.py  # Comprehensive demo
```

Run the comprehensive demo:
```bash
python examples/level4_advanced_automation/07_all_features_demo.py
```

---

## Installation

Install additional dependencies:
```bash
pip install -r requirements.txt
```

Optional dependencies for specific features:
```bash
# For OCR
pip install pytesseract
# System: sudo apt-get install tesseract-ocr

# For browser automation
pip install selenium playwright
playwright install chromium

# For cloud storage
pip install boto3 google-cloud-storage
```

---

## Best Practices

1. **Error Handling**: All tools return success/error dictionaries
2. **Configuration**: Use environment variables for credentials
3. **Logging**: Enable logging for production deployments
4. **Testing**: Run example scripts to verify functionality
5. **Security**: Never hardcode credentials

---

## Next Steps

- Explore individual examples
- Integrate with your workflows
- Customize for your use cases
- Build complex automation pipelines

For more information, see the main [README.md](../README.md)
