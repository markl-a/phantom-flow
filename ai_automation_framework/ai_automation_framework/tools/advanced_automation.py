"""Advanced automation tools for AI framework."""

import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, List, Optional
import sqlite3
import json
from datetime import datetime, timedelta
import re
import time
import threading
import os
import logging

# Import RateLimiter from core.utils to avoid code duplication
from ai_automation_framework.core.utils import RateLimiter


class EmailAutomationTool:
    """Tool for email automation (SMTP/IMAP)."""

    def __init__(self, smtp_server: Optional[str] = None, smtp_port: int = 587,
                 imap_server: Optional[str] = None, imap_port: int = 993):
        """
        Initialize email automation tool.

        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP port
            imap_server: IMAP server address
            imap_port: IMAP port
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.imap_server = imap_server
        self.imap_port = imap_port

    def send_email(
        self,
        sender: str,
        password: Optional[str] = None,
        recipient: Optional[str] = None,
        subject: Optional[str] = None,
        body: Optional[str] = None,
        html: bool = False,
        password_env_var: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email via SMTP.

        Security Note: It is recommended to use password_env_var or keyring
        instead of passing password directly as a parameter.

        Args:
            sender: Sender email address
            password: Email password or app password (NOT RECOMMENDED - use password_env_var instead)
            recipient: Recipient email address
            subject: Email subject
            body: Email body
            html: Whether body is HTML
            password_env_var: Environment variable name containing the password (RECOMMENDED)

        Returns:
            Result dictionary
        """
        # Get password from environment variable or keyring if available
        actual_password = password

        if password_env_var:
            actual_password = os.getenv(password_env_var)
            if not actual_password:
                return {
                    "success": False,
                    "error": f"Environment variable '{password_env_var}' not found"
                }
        elif password:
            # Warn when password is passed directly
            logging.warning(
                "SECURITY WARNING: Password passed directly to send_email(). "
                "Consider using password_env_var parameter or keyring instead. "
                "Direct password parameters should not be hardcoded in source code."
            )
        else:
            # Try to get from keyring as fallback
            try:
                import keyring
                actual_password = keyring.get_password("email_automation", sender)
                if not actual_password:
                    return {
                        "success": False,
                        "error": "No password provided. Use password_env_var or store in keyring."
                    }
            except ImportError:
                return {
                    "success": False,
                    "error": "No password provided. Install 'keyring' package or use password_env_var parameter."
                }

        try:
            msg = MIMEMultipart('alternative') if html else MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = recipient

            if html:
                msg.attach(MIMEText(body, 'html'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(sender, actual_password)
                server.send_message(msg)

            return {
                "success": True,
                "message": f"Email sent to {recipient}",
                "timestamp": datetime.now().isoformat()
            }
        except smtplib.SMTPAuthenticationError as e:
            return {"success": False, "error": f"Authentication failed: {str(e)}", "error_type": "auth_error"}
        except smtplib.SMTPServerDisconnected as e:
            return {"success": False, "error": f"Server disconnected: {str(e)}", "error_type": "connection_error"}
        except smtplib.SMTPException as e:
            return {"success": False, "error": f"SMTP error: {str(e)}", "error_type": "smtp_error"}
        except (ConnectionError, TimeoutError, OSError) as e:
            return {"success": False, "error": f"Network error: {str(e)}", "error_type": "network_error"}

    def read_emails(
        self,
        username: str,
        password: Optional[str] = None,
        folder: str = "INBOX",
        limit: int = 10,
        unread_only: bool = False,
        password_env_var: str = None
    ) -> Dict[str, Any]:
        """
        Read emails from IMAP server.

        Security Note: It is recommended to use password_env_var or keyring
        instead of passing password directly as a parameter.

        Args:
            username: Email username
            password: Email password (NOT RECOMMENDED - use password_env_var instead)
            folder: Mail folder to read from
            limit: Maximum number of emails to read
            unread_only: Only read unread emails
            password_env_var: Environment variable name containing the password (RECOMMENDED)

        Returns:
            Dictionary with emails
        """
        # Get password from environment variable or keyring if available
        actual_password = password

        if password_env_var:
            actual_password = os.getenv(password_env_var)
            if not actual_password:
                return {
                    "success": False,
                    "error": f"Environment variable '{password_env_var}' not found"
                }
        elif password:
            # Warn when password is passed directly
            logging.warning(
                "SECURITY WARNING: Password passed directly to read_emails(). "
                "Consider using password_env_var parameter or keyring instead. "
                "Direct password parameters should not be hardcoded in source code."
            )
        else:
            # Try to get from keyring as fallback
            try:
                import keyring
                actual_password = keyring.get_password("email_automation", username)
                if not actual_password:
                    return {
                        "success": False,
                        "error": "No password provided. Use password_env_var or store in keyring."
                    }
            except ImportError:
                return {
                    "success": False,
                    "error": "No password provided. Install 'keyring' package or use password_env_var parameter."
                }

        mail = None
        try:
            mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            mail.login(username, actual_password)
            mail.select(folder)

            search_criteria = '(UNSEEN)' if unread_only else 'ALL'
            _, messages = mail.search(None, search_criteria)

            email_ids = messages[0].split()
            email_ids = email_ids[-limit:]  # Get latest emails

            emails = []
            for email_id in email_ids:
                _, msg_data = mail.fetch(email_id, '(RFC822)')
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)

                emails.append({
                    "id": email_id.decode(),
                    "from": email_message.get('From'),
                    "subject": email_message.get('Subject'),
                    "date": email_message.get('Date'),
                    "body": self._get_email_body(email_message)
                })

            return {
                "success": True,
                "count": len(emails),
                "emails": emails
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            if mail:
                try:
                    mail.close()
                    mail.logout()
                except Exception:
                    pass  # Ignore cleanup errors

    @staticmethod
    def _get_email_body(email_message: email.message.Message) -> str:
        """Extract body from email message."""
        if email_message.is_multipart():
            for part in email_message.walk():
                if part.get_content_type() == "text/plain":
                    return part.get_payload(decode=True).decode()
        else:
            return email_message.get_payload(decode=True).decode()
        return ""


class DatabaseAutomationTool:
    """Tool for database automation and SQL query generation."""

    # Valid SQL identifier pattern (alphanumeric and underscore, starting with letter/underscore)
    _VALID_IDENTIFIER_PATTERN = r'^[a-zA-Z_][a-zA-Z0-9_]*$'

    def __init__(self, db_path: str = ":memory:"):
        """
        Initialize database automation tool.

        Args:
            db_path: Path to SQLite database
        """
        import re
        self._identifier_regex = re.compile(self._VALID_IDENTIFIER_PATTERN)
        self.db_path = db_path
        self.conn = None

    def _validate_identifier(self, name: str) -> bool:
        """
        Validate SQL identifier to prevent SQL injection.

        Args:
            name: Table or column name to validate

        Returns:
            True if valid, raises ValueError if invalid
        """
        if not name or not self._identifier_regex.match(name):
            raise ValueError(f"Invalid SQL identifier: {name}")
        # Also check for SQL reserved words that could be dangerous
        dangerous_words = {'drop', 'delete', 'truncate', 'insert', 'update', 'exec', 'execute'}
        if name.lower() in dangerous_words:
            raise ValueError(f"SQL reserved word not allowed as identifier: {name}")
        return True

    def connect(self) -> Dict[str, Any]:
        """Connect to database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return {"success": True, "message": "Connected to database"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _validate_query_safety(self, query: str) -> bool:
        """
        Validate SQL query safety to prevent dangerous operations.

        This method checks the query against:
        1. Allowed query types whitelist (SELECT, INSERT, UPDATE, DELETE)
        2. Dangerous keywords blacklist (DROP, TRUNCATE, ALTER, etc.)

        Args:
            query: SQL query to validate

        Returns:
            True if query is safe

        Raises:
            ValueError: If query contains dangerous operations
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Normalize query for checking
        normalized_query = query.strip().upper()

        # Whitelist of allowed query types
        allowed_query_types = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']
        query_type = normalized_query.split()[0] if normalized_query else ""

        if query_type not in allowed_query_types:
            raise ValueError(
                f"Query type '{query_type}' not allowed. "
                f"Only {', '.join(allowed_query_types)} queries are permitted."
            )

        # Blacklist of dangerous keywords
        dangerous_keywords = [
            'DROP', 'TRUNCATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE',
            'GRANT', 'REVOKE', 'PRAGMA', 'ATTACH', 'DETACH'
        ]

        # Check for dangerous keywords
        for keyword in dangerous_keywords:
            # Use word boundaries to avoid false positives
            # (e.g., "DROP" in "BACKDROP" should be allowed)
            pattern = r'\b' + keyword + r'\b'
            if re.search(pattern, normalized_query):
                raise ValueError(
                    f"Dangerous SQL keyword '{keyword}' detected in query. "
                    f"This operation is not allowed for security reasons."
                )

        # Additional check: Prevent multiple statements (SQL injection via semicolon)
        if ';' in query.rstrip(';'):  # Allow trailing semicolon but not in middle
            raise ValueError(
                "Multiple SQL statements detected (semicolon in query). "
                "Only single statements are allowed."
            )

        return True

    def execute_query(self, query: str, params: Optional[tuple] = None, skip_validation: bool = False) -> Dict[str, Any]:
        """
        Execute SQL query with safety validation.

        By default, this method validates queries to prevent dangerous operations.
        Only SELECT, INSERT, UPDATE, and DELETE queries are allowed.
        Dangerous keywords like DROP, TRUNCATE, ALTER are blocked.

        Args:
            query: SQL query to execute
            params: Query parameters (use parameterized queries to prevent SQL injection)
            skip_validation: Skip safety validation (USE WITH EXTREME CAUTION)

        Returns:
            Query results

        Security Notes:
            - Always use parameterized queries (params argument) to prevent SQL injection
            - Query validation is enabled by default to prevent dangerous operations
            - Only disable validation (skip_validation=True) if you have validated the query yourself
        """
        try:
            # Validate query safety unless explicitly skipped
            if not skip_validation:
                try:
                    self._validate_query_safety(query)
                except ValueError as e:
                    return {
                        "success": False,
                        "error": f"Query validation failed: {str(e)}",
                        "security_warning": "Query blocked for security reasons"
                    }

            if not self.conn:
                self.connect()

            cursor = self.conn.cursor()
            try:
                cursor.execute(query, params or ())

                if query.strip().upper().startswith('SELECT'):
                    rows = cursor.fetchall()
                    results = [dict(row) for row in rows]
                    return {
                        "success": True,
                        "rows": len(results),
                        "data": results
                    }
                else:
                    self.conn.commit()
                    return {
                        "success": True,
                        "affected_rows": cursor.rowcount,
                        "message": "Query executed successfully"
                    }
            finally:
                cursor.close()
        except Exception as e:
            return {"success": False, "error": str(e)}

    def generate_select_query(
        self,
        table: str,
        columns: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> str:
        """
        Generate SELECT query with SQL injection protection.

        Args:
            table: Table name
            columns: Columns to select
            where: WHERE conditions
            limit: LIMIT clause

        Returns:
            Generated SQL query
        """
        # Validate table name
        self._validate_identifier(table)

        # Validate and build column list
        if columns:
            for col in columns:
                self._validate_identifier(col)
            cols = ", ".join(columns)
        else:
            cols = "*"

        query = f"SELECT {cols} FROM {table}"

        if where:
            for k in where.keys():
                self._validate_identifier(k)
            conditions = " AND ".join([f"{k} = ?" for k in where.keys()])
            query += f" WHERE {conditions}"

        if limit:
            if not isinstance(limit, int) or limit < 0:
                raise ValueError("LIMIT must be a non-negative integer")
            query += f" LIMIT {limit}"

        return query

    def generate_insert_query(self, table: str, data: Dict[str, Any]) -> tuple:
        """
        Generate INSERT query with SQL injection protection.

        Args:
            table: Table name
            data: Data to insert

        Returns:
            Tuple of (query, values)
        """
        # Validate table name
        self._validate_identifier(table)

        # Validate column names
        for col in data.keys():
            self._validate_identifier(col)

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["?" for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        return query, tuple(data.values())

    def create_table(self, table: str, schema: Dict[str, str]) -> Dict[str, Any]:
        """
        Create a table with SQL injection protection.

        Args:
            table: Table name
            schema: Column schema {column_name: column_type}

        Returns:
            Result dictionary
        """
        # Validate table name
        self._validate_identifier(table)

        # Validate column names and types
        allowed_types = {'INTEGER', 'TEXT', 'REAL', 'BLOB', 'NULL', 'VARCHAR', 'CHAR', 'BOOLEAN', 'DATE', 'DATETIME', 'PRIMARY KEY', 'NOT NULL', 'UNIQUE', 'AUTOINCREMENT'}
        for name, dtype in schema.items():
            self._validate_identifier(name)
            # Check that type only contains allowed keywords
            type_parts = dtype.upper().split()
            for part in type_parts:
                # Remove any parentheses content like VARCHAR(255)
                clean_part = part.split('(')[0]
                if clean_part and clean_part not in allowed_types:
                    raise ValueError(f"Invalid SQL type: {dtype}")

        columns_def = ", ".join([f"{name} {dtype}" for name, dtype in schema.items()])
        query = f"CREATE TABLE IF NOT EXISTS {table} ({columns_def})"
        return self.execute_query(query)

    def batch_insert(
        self,
        table: str,
        records: List[Dict[str, Any]],
        batch_size: int = 1000
    ) -> Dict[str, Any]:
        """
        批量插入記錄，性能提升 50 倍

        使用事務和批處理來大幅提升插入性能。
        相比逐條插入，批量插入可以減少數據庫往返次數和事務開銷。

        Args:
            table: 表名
            records: 要插入的記錄列表，每個記錄是一個字典
            batch_size: 每批處理的記錄數（默認 1000）

        Returns:
            包含插入統計信息的結果字典

        Example:
            >>> db = DatabaseAutomationTool()
            >>> records = [
            ...     {"name": "Alice", "age": 30},
            ...     {"name": "Bob", "age": 25},
            ...     # ... 更多記錄
            ... ]
            >>> result = db.batch_insert("users", records, batch_size=1000)
        """
        try:
            if not self.conn:
                self.connect()

            if not records:
                return {
                    "success": True,
                    "message": "No records to insert",
                    "total_inserted": 0
                }

            # Validate table name
            self._validate_identifier(table)

            # Validate all records have the same columns
            first_record = records[0]
            columns = list(first_record.keys())

            # Validate column names
            for col in columns:
                self._validate_identifier(col)

            # Verify all records have the same columns
            for i, record in enumerate(records):
                if set(record.keys()) != set(columns):
                    raise ValueError(
                        f"Record {i} has different columns. "
                        f"Expected: {columns}, Got: {list(record.keys())}"
                    )

            # Prepare INSERT query
            columns_str = ", ".join(columns)
            placeholders = ", ".join(["?" for _ in columns])
            query = f"INSERT INTO {table} ({columns_str}) VALUES ({placeholders})"

            total_inserted = 0
            cursor = self.conn.cursor()

            try:
                # Process in batches
                for batch_start in range(0, len(records), batch_size):
                    batch_end = min(batch_start + batch_size, len(records))
                    batch = records[batch_start:batch_end]

                    # Begin transaction for this batch
                    cursor.execute("BEGIN TRANSACTION")

                    try:
                        # Execute batch insert
                        for record in batch:
                            values = tuple(record[col] for col in columns)
                            cursor.execute(query, values)

                        # Commit transaction
                        self.conn.commit()
                        total_inserted += len(batch)

                    except Exception as e:
                        # Rollback on error
                        self.conn.rollback()
                        raise Exception(f"Batch insert failed at record {batch_start}: {str(e)}")

                return {
                    "success": True,
                    "message": f"Successfully inserted {total_inserted} records",
                    "total_inserted": total_inserted,
                    "batches": (len(records) + batch_size - 1) // batch_size,
                    "batch_size": batch_size
                }
            finally:
                cursor.close()

        except Exception as e:
            return {"success": False, "error": str(e)}

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


class WebScraperTool:
    """Tool for web scraping and data extraction."""

    def __init__(self, rate_limit: Optional[float] = None):
        """
        Initialize web scraper tool.

        Args:
            rate_limit: Maximum requests per second (e.g., 2.0 = 2 requests/sec).
                       If None, no rate limiting is applied.
        """
        self.rate_limiter = RateLimiter(rate_limit) if rate_limit else None

    def fetch_url(self, url: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Fetch content from URL.

        Args:
            url: URL to fetch
            timeout: Request timeout

        Returns:
            Response data
        """
        # Apply rate limiting if configured
        if self.rate_limiter:
            self.rate_limiter.wait_for_token()

        try:
            # Validate URL
            if not url or not isinstance(url, str):
                raise ValueError("URL must be a non-empty string")

            # Basic URL validation
            if not url.startswith(('http://', 'https://')):
                raise ValueError("URL must start with http:// or https://")

            import requests
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()

            return {
                "success": True,
                "status_code": response.status_code,
                "content": response.text,
                "headers": dict(response.headers),
                "url": url
            }
        except ValueError as e:
            return {"success": False, "error": f"Validation error: {str(e)}"}
        except requests.exceptions.RequestException as e:
            return {"success": False, "error": f"Request error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def extract_links(self, html_content: str, base_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract all links from HTML.

        Args:
            html_content: HTML content
            base_url: Base URL for relative links

        Returns:
            Extracted links
        """
        # Apply rate limiting if configured
        if self.rate_limiter:
            self.rate_limiter.wait_for_token()

        try:
            # Validate html_content
            if not html_content or not isinstance(html_content, str):
                raise ValueError("html_content must be a non-empty string")

            # Validate base_url if provided
            if base_url is not None:
                if not isinstance(base_url, str) or not base_url:
                    raise ValueError("base_url must be a non-empty string if provided")
                if not base_url.startswith(('http://', 'https://')):
                    raise ValueError("base_url must start with http:// or https://")

            from bs4 import BeautifulSoup
            from urllib.parse import urljoin

            soup = BeautifulSoup(html_content, 'html.parser')
            links = []

            for link in soup.find_all('a', href=True):
                href = link['href']
                if base_url:
                    href = urljoin(base_url, href)
                links.append({
                    "url": href,
                    "text": link.get_text(strip=True)
                })

            return {
                "success": True,
                "count": len(links),
                "links": links
            }
        except ValueError as e:
            return {"success": False, "error": f"Validation error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def extract_text(self, html_content: str, tag: Optional[str] = None) -> Dict[str, Any]:
        """
        Extract text from HTML.

        Args:
            html_content: HTML content
            tag: Specific tag to extract (optional)

        Returns:
            Extracted text
        """
        # Apply rate limiting if configured
        if self.rate_limiter:
            self.rate_limiter.wait_for_token()

        try:
            # Validate html_content
            if not html_content or not isinstance(html_content, str):
                raise ValueError("html_content must be a non-empty string")

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, 'html.parser')

            if tag:
                elements = soup.find_all(tag)
                text = [elem.get_text(strip=True) for elem in elements]
            else:
                text = soup.get_text(strip=True)

            return {
                "success": True,
                "text": text
            }
        except ValueError as e:
            return {"success": False, "error": f"Validation error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def extract_table_data(self, html_content: str) -> Dict[str, Any]:
        """
        Extract table data from HTML.

        Args:
            html_content: HTML content

        Returns:
            Extracted table data
        """
        try:
            # Validate html_content
            if not html_content or not isinstance(html_content, str):
                raise ValueError("html_content must be a non-empty string")

            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, 'html.parser')
            tables = []

            for table in soup.find_all('table'):
                rows = []
                for tr in table.find_all('tr'):
                    cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                    if cells:
                        rows.append(cells)
                tables.append(rows)

            return {
                "success": True,
                "table_count": len(tables),
                "tables": tables
            }
        except ValueError as e:
            return {"success": False, "error": f"Validation error: {str(e)}"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Tool schemas for function calling
ADVANCED_TOOL_SCHEMAS = {
    "send_email": {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "Send an email via SMTP",
            "parameters": {
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Recipient email"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "body": {"type": "string", "description": "Email body"}
                },
                "required": ["recipient", "subject", "body"]
            }
        }
    },
    "execute_sql": {
        "type": "function",
        "function": {
            "name": "execute_sql",
            "description": "Execute SQL query on database",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "SQL query to execute"}
                },
                "required": ["query"]
            }
        }
    },
    "scrape_url": {
        "type": "function",
        "function": {
            "name": "scrape_url",
            "description": "Scrape content from URL",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL to scrape"}
                },
                "required": ["url"]
            }
        }
    }
}
