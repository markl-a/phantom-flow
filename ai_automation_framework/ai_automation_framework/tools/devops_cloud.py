"""Git automation, cloud storage, browser automation, and PDF tools."""

import subprocess
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
import json


class GitAutomationTool:
    """Git operations automation tool."""

    def __init__(self, repo_path: str = "."):
        """
        Initialize Git tool.

        Args:
            repo_path: Path to git repository
        """
        self.repo_path = Path(repo_path)

    def _run_git_command(self, args: List[str]) -> Dict[str, Any]:
        """Run git command and return result."""
        try:
            result = subprocess.run(
                ["git"] + args,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
                timeout=30  # 30 second timeout for git operations
            )
            return {
                "success": True,
                "output": result.stdout.strip(),
                "error": result.stderr.strip()
            }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": e.stderr.strip() or str(e)
            }
        except subprocess.TimeoutExpired as e:
            return {
                "success": False,
                "error": f"Git command timed out after 30 seconds: {' '.join(args)}"
            }

    def clone(self, url: str, destination: Optional[str] = None) -> Dict[str, Any]:
        """Clone a repository."""
        args = ["clone", url]
        if destination:
            args.append(destination)
        return self._run_git_command(args)

    def status(self) -> Dict[str, Any]:
        """Get repository status."""
        return self._run_git_command(["status"])

    def add(self, files: str = ".") -> Dict[str, Any]:
        """Stage files for commit."""
        return self._run_git_command(["add", files])

    def commit(self, message: str) -> Dict[str, Any]:
        """Commit staged changes."""
        return self._run_git_command(["commit", "-m", message])

    def push(self, remote: str = "origin", branch: str = "main") -> Dict[str, Any]:
        """Push commits to remote."""
        return self._run_git_command(["push", remote, branch])

    def pull(self, remote: str = "origin", branch: str = "main") -> Dict[str, Any]:
        """Pull changes from remote."""
        return self._run_git_command(["pull", remote, branch])

    def create_branch(self, branch_name: str) -> Dict[str, Any]:
        """Create a new branch."""
        return self._run_git_command(["checkout", "-b", branch_name])

    def switch_branch(self, branch_name: str) -> Dict[str, Any]:
        """Switch to a different branch."""
        return self._run_git_command(["checkout", branch_name])

    def merge(self, branch_name: str) -> Dict[str, Any]:
        """Merge branch into current branch."""
        return self._run_git_command(["merge", branch_name])

    def get_log(self, max_count: int = 10) -> Dict[str, Any]:
        """Get commit history."""
        return self._run_git_command(["log", f"-{max_count}", "--oneline"])

    def diff(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """Show changes in working directory."""
        args = ["diff"]
        if file_path:
            args.append(file_path)
        return self._run_git_command(args)


class CloudStorageTool:
    """Cloud storage integration tool (S3/GCS compatible)."""

    def __init__(self, provider: str = "s3", **credentials):
        """
        Initialize cloud storage tool.

        Args:
            provider: Cloud provider ('s3' or 'gcs')
            **credentials: Provider-specific credentials
        """
        self.provider = provider
        self.credentials = credentials

    def _validate_s3_credentials(self) -> Dict[str, Any]:
        """Validate S3 credentials before use."""
        required_keys = {'aws_access_key_id', 'aws_secret_access_key'}
        provided_keys = set(self.credentials.keys())

        # Allow region_name as optional
        valid_keys = required_keys | {'region_name', 'endpoint_url'}

        missing_keys = required_keys - provided_keys
        if missing_keys:
            return {
                "success": False,
                "error": f"Missing required S3 credentials: {', '.join(missing_keys)}"
            }

        invalid_keys = provided_keys - valid_keys
        if invalid_keys:
            return {
                "success": False,
                "error": f"Invalid S3 credential keys: {', '.join(invalid_keys)}"
            }

        # Check for empty values
        for key in required_keys:
            if not self.credentials.get(key):
                return {
                    "success": False,
                    "error": f"S3 credential '{key}' cannot be empty"
                }

        return {"success": True}

    def _validate_gcs_credentials(self) -> Dict[str, Any]:
        """Validate GCS credentials before use."""
        # GCS uses application default credentials or service account file
        # Check if GOOGLE_APPLICATION_CREDENTIALS env var is set
        if 'credentials' not in self.credentials and not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            return {
                "success": False,
                "error": "GCS requires 'credentials' parameter or GOOGLE_APPLICATION_CREDENTIALS environment variable"
            }
        return {"success": True}

    def upload_file_s3(
        self,
        file_path: str,
        bucket: str,
        object_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Upload file to AWS S3.

        Args:
            file_path: Local file path
            bucket: S3 bucket name
            object_name: S3 object name

        Returns:
            Upload result
        """
        # Validate credentials first
        validation = self._validate_s3_credentials()
        if not validation["success"]:
            return validation

        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            # Validate file exists
            if not Path(file_path).exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            object_name = object_name or Path(file_path).name

            s3_client = boto3.client('s3', **self.credentials)
            s3_client.upload_file(file_path, bucket, object_name)

            return {
                "success": True,
                "bucket": bucket,
                "object": object_name,
                "provider": "s3"
            }
        except NoCredentialsError:
            return {"success": False, "error": "AWS credentials not found or invalid"}
        except ClientError as e:
            return {"success": False, "error": f"AWS S3 error: {e.response['Error']['Message']}"}
        except Exception as e:
            return {"success": False, "error": f"Upload failed: {str(e)}"}

    def download_file_s3(
        self,
        bucket: str,
        object_name: str,
        file_path: str
    ) -> Dict[str, Any]:
        """Download file from AWS S3."""
        # Validate credentials first
        validation = self._validate_s3_credentials()
        if not validation["success"]:
            return validation

        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            # Ensure output directory exists
            output_dir = Path(file_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            s3_client = boto3.client('s3', **self.credentials)
            s3_client.download_file(bucket, object_name, file_path)

            return {
                "success": True,
                "bucket": bucket,
                "object": object_name,
                "local_path": file_path
            }
        except NoCredentialsError:
            return {"success": False, "error": "AWS credentials not found or invalid"}
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return {"success": False, "error": f"Object not found: {object_name}"}
            return {"success": False, "error": f"AWS S3 error: {e.response['Error']['Message']}"}
        except Exception as e:
            return {"success": False, "error": f"Download failed: {str(e)}"}

    def list_objects_s3(self, bucket: str, prefix: str = "") -> Dict[str, Any]:
        """List objects in S3 bucket."""
        # Validate credentials first
        validation = self._validate_s3_credentials()
        if not validation["success"]:
            return validation

        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            s3_client = boto3.client('s3', **self.credentials)
            response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)

            objects = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    objects.append({
                        "key": obj['Key'],
                        "size": obj['Size'],
                        "modified": obj['LastModified'].isoformat()
                    })

            return {
                "success": True,
                "bucket": bucket,
                "count": len(objects),
                "objects": objects
            }
        except NoCredentialsError:
            return {"success": False, "error": "AWS credentials not found or invalid"}
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchBucket':
                return {"success": False, "error": f"Bucket not found: {bucket}"}
            return {"success": False, "error": f"AWS S3 error: {e.response['Error']['Message']}"}
        except Exception as e:
            return {"success": False, "error": f"List operation failed: {str(e)}"}

    def upload_file_gcs(
        self,
        file_path: str,
        bucket: str,
        object_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Upload file to Google Cloud Storage."""
        # Validate credentials first
        validation = self._validate_gcs_credentials()
        if not validation["success"]:
            return validation

        try:
            from google.cloud import storage
            from google.api_core.exceptions import GoogleAPIError, NotFound

            # Validate file exists
            if not Path(file_path).exists():
                return {"success": False, "error": f"File not found: {file_path}"}

            object_name = object_name or Path(file_path).name

            # Use credentials if provided, otherwise use default
            if 'credentials' in self.credentials:
                client = storage.Client(credentials=self.credentials['credentials'])
            else:
                client = storage.Client()

            bucket_obj = client.bucket(bucket)
            blob = bucket_obj.blob(object_name)

            blob.upload_from_filename(file_path)

            return {
                "success": True,
                "bucket": bucket,
                "object": object_name,
                "provider": "gcs"
            }
        except NotFound:
            return {"success": False, "error": f"GCS bucket not found: {bucket}"}
        except GoogleAPIError as e:
            return {"success": False, "error": f"GCS API error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"Upload failed: {str(e)}"}


class BrowserAutomationTool:
    """Browser automation tool using Selenium/Playwright."""

    def __init__(self, driver_type: str = "selenium", headless: bool = True):
        """
        Initialize browser automation.

        Args:
            driver_type: Browser driver ('selenium' or 'playwright')
            headless: Run in headless mode
        """
        self.driver_type = driver_type
        self.headless = headless
        self.driver = None

    def start_selenium(self) -> Dict[str, Any]:
        """Start Selenium WebDriver."""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options

            options = Options()
            if self.headless:
                options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')

            self.driver = webdriver.Chrome(options=options)

            return {"success": True, "message": "Selenium WebDriver started"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL."""
        try:
            if not self.driver:
                self.start_selenium()

            self.driver.get(url)

            return {
                "success": True,
                "url": url,
                "title": self.driver.title
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_page_text(self) -> Dict[str, Any]:
        """Get all text from current page."""
        try:
            from selenium.webdriver.common.by import By

            if not self.driver:
                return {"success": False, "error": "Driver not started"}

            text = self.driver.find_element(By.TAG_NAME, "body").text

            return {
                "success": True,
                "text": text,
                "length": len(text)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def screenshot(self, output_path: str) -> Dict[str, Any]:
        """Take screenshot of current page."""
        try:
            if not self.driver:
                return {"success": False, "error": "Driver not started"}

            self.driver.save_screenshot(output_path)

            return {
                "success": True,
                "screenshot": output_path
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def fill_form(self, field_id: str, value: str) -> Dict[str, Any]:
        """Fill form field."""
        try:
            from selenium.webdriver.common.by import By

            if not self.driver:
                return {"success": False, "error": "Driver not started"}

            element = self.driver.find_element(By.ID, field_id)
            element.clear()
            element.send_keys(value)

            return {
                "success": True,
                "field_id": field_id,
                "value": value
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def click_element(self, element_id: str) -> Dict[str, Any]:
        """Click element by ID."""
        try:
            from selenium.webdriver.common.by import By

            if not self.driver:
                return {"success": False, "error": "Driver not started"}

            element = self.driver.find_element(By.ID, element_id)
            element.click()

            return {
                "success": True,
                "element_id": element_id
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def close(self) -> Dict[str, Any]:
        """Close browser."""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None

            return {"success": True, "message": "Browser closed"}
        except Exception as e:
            return {"success": False, "error": str(e)}


class PDFAdvancedTool:
    """Advanced PDF processing and generation tool."""

    @staticmethod
    def merge_pdfs(input_pdfs: List[str], output_pdf: str) -> Dict[str, Any]:
        """Merge multiple PDF files."""
        try:
            from PyPDF2 import PdfMerger

            # Validate input files exist
            for pdf in input_pdfs:
                if not Path(pdf).exists():
                    return {"success": False, "error": f"Input file not found: {pdf}"}

            # Use context manager for proper resource handling
            with PdfMerger() as merger:
                for pdf in input_pdfs:
                    merger.append(pdf)

                with open(output_pdf, 'wb') as f:
                    merger.write(f)

            return {
                "success": True,
                "input_files": len(input_pdfs),
                "output": output_pdf
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"PDF merge failed: {str(e)}"}

    @staticmethod
    def split_pdf(input_pdf: str, output_dir: str) -> Dict[str, Any]:
        """Split PDF into separate pages."""
        try:
            from PyPDF2 import PdfReader, PdfWriter

            # Validate input file exists
            if not Path(input_pdf).exists():
                return {"success": False, "error": f"Input file not found: {input_pdf}"}

            # Use context manager for reading PDF
            with open(input_pdf, 'rb') as f:
                reader = PdfReader(f)
                output_files = []

                Path(output_dir).mkdir(parents=True, exist_ok=True)

                for i, page in enumerate(reader.pages):
                    writer = PdfWriter()
                    writer.add_page(page)

                    output_file = Path(output_dir) / f"page_{i+1}.pdf"
                    with open(output_file, 'wb') as out_f:
                        writer.write(out_f)

                    output_files.append(str(output_file))

                total_pages = len(reader.pages)

            return {
                "success": True,
                "total_pages": total_pages,
                "output_files": output_files
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"PDF split failed: {str(e)}"}

    @staticmethod
    def extract_pdf_text(pdf_path: str) -> Dict[str, Any]:
        """Extract text from PDF."""
        try:
            from PyPDF2 import PdfReader

            # Validate input file exists
            if not Path(pdf_path).exists():
                return {"success": False, "error": f"File not found: {pdf_path}"}

            # Use context manager for reading PDF
            with open(pdf_path, 'rb') as f:
                reader = PdfReader(f)
                text = ""

                for page in reader.pages:
                    text += page.extract_text() + "\n"

                num_pages = len(reader.pages)

            return {
                "success": True,
                "pages": num_pages,
                "text": text.strip(),
                "char_count": len(text)
            }
        except FileNotFoundError as e:
            return {"success": False, "error": f"File not found: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": f"PDF text extraction failed: {str(e)}"}

    @staticmethod
    def create_pdf_from_text(text: str, output_path: str) -> Dict[str, Any]:
        """Create PDF from text."""
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)

            c = canvas.Canvas(output_path, pagesize=letter)
            width, height = letter

            y = height - 50
            for line in text.split('\n'):
                if y < 50:
                    c.showPage()
                    y = height - 50
                c.drawString(50, y, line[:100])  # Limit line length
                y -= 15

            c.save()

            return {
                "success": True,
                "output": output_path
            }
        except Exception as e:
            return {"success": False, "error": f"PDF creation failed: {str(e)}"}


# Tool schemas
DEVOPS_CLOUD_SCHEMAS = {
    "git_commit": {
        "type": "function",
        "function": {
            "name": "git_commit",
            "description": "Commit changes to git",
            "parameters": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                },
                "required": ["message"]
            }
        }
    },
    "upload_to_cloud": {
        "type": "function",
        "function": {
            "name": "upload_to_cloud",
            "description": "Upload file to cloud storage",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string"},
                    "bucket": {"type": "string"}
                },
                "required": ["file_path", "bucket"]
            }
        }
    }
}
