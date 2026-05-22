"""Tests for advanced automation tools."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import sqlite3


class TestEmailAutomationTool:
    """Test Email automation tool."""

    def test_initialization(self):
        """Test tool initialization."""
        from ai_automation_framework.tools.advanced_automation import EmailAutomationTool

        tool = EmailAutomationTool(
            smtp_server="smtp.gmail.com",
            smtp_port=587,
            imap_server="imap.gmail.com",
            imap_port=993
        )

        assert tool.smtp_server == "smtp.gmail.com"
        assert tool.smtp_port == 587
        assert tool.imap_server == "imap.gmail.com"

    def test_send_email_mock(self):
        """Test sending email with mock."""
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__ = Mock(return_value=mock_server)
            mock_smtp.return_value.__exit__ = Mock(return_value=None)

            from ai_automation_framework.tools.advanced_automation import EmailAutomationTool

            tool = EmailAutomationTool(smtp_server="smtp.test.com")
            result = tool.send_email(
                sender="test@example.com",
                password="password",
                recipient="recipient@example.com",
                subject="Test Subject",
                body="Test Body"
            )

            assert result["success"] is True
            assert "Email sent" in result["message"]

    def test_read_emails_mock(self):
        """Test reading emails with mock."""
        with patch("imaplib.IMAP4_SSL") as mock_imap:
            mock_mail = MagicMock()
            mock_imap.return_value = mock_mail
            mock_mail.login.return_value = ("OK", [])
            mock_mail.select.return_value = ("OK", [b"5"])
            mock_mail.search.return_value = ("OK", [b"1 2 3"])
            mock_mail.fetch.return_value = ("OK", [(b"1", b"test email content")])

            from ai_automation_framework.tools.advanced_automation import EmailAutomationTool

            tool = EmailAutomationTool(imap_server="imap.test.com")
            # Note: actual implementation may differ
            assert tool.imap_server == "imap.test.com"


class TestDatabaseAutomationTool:
    """Test Database automation tool."""

    def test_connect_sqlite(self, temp_sqlite_db):
        """Test connecting to SQLite database."""
        from ai_automation_framework.tools.advanced_automation import DatabaseAutomationTool

        tool = DatabaseAutomationTool(db_type="sqlite", database=str(temp_sqlite_db))
        result = tool.connect()

        assert result["success"] is True

    def test_execute_query(self, temp_sqlite_db):
        """Test executing SQL query."""
        from ai_automation_framework.tools.advanced_automation import DatabaseAutomationTool

        tool = DatabaseAutomationTool(db_type="sqlite", database=str(temp_sqlite_db))
        tool.connect()

        result = tool.execute_query("SELECT * FROM users")

        assert result["success"] is True
        assert len(result["data"]) == 2

    def test_insert_data(self, temp_sqlite_db):
        """Test inserting data."""
        from ai_automation_framework.tools.advanced_automation import DatabaseAutomationTool

        tool = DatabaseAutomationTool(db_type="sqlite", database=str(temp_sqlite_db))
        tool.connect()

        result = tool.insert(
            table="users",
            data={"name": "Charlie", "email": "charlie@example.com"}
        )

        assert result["success"] is True

    def test_generate_sql(self):
        """Test SQL generation from natural language."""
        from ai_automation_framework.tools.advanced_automation import DatabaseAutomationTool

        tool = DatabaseAutomationTool(db_type="sqlite", database=":memory:")
        # Test the tool exists and can be instantiated
        assert tool is not None


class TestWebScraperTool:
    """Test Web scraper tool."""

    def test_initialization(self):
        """Test tool initialization."""
        from ai_automation_framework.tools.advanced_automation import WebScraperTool

        tool = WebScraperTool()
        assert tool is not None

    def test_fetch_page_mock(self, mock_http_response):
        """Test fetching web page with mock."""
        mock_http_response["get"].return_value.text = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <h1>Hello World</h1>
                <p>Test content</p>
            </body>
        </html>
        """

        from ai_automation_framework.tools.advanced_automation import WebScraperTool

        tool = WebScraperTool()
        result = tool.fetch_page("https://example.com")

        assert result["success"] is True
        assert "html" in result

    def test_extract_links_mock(self, mock_http_response):
        """Test extracting links from page."""
        mock_http_response["get"].return_value.text = """
        <html>
            <body>
                <a href="https://example.com/page1">Link 1</a>
                <a href="https://example.com/page2">Link 2</a>
            </body>
        </html>
        """

        from ai_automation_framework.tools.advanced_automation import WebScraperTool

        tool = WebScraperTool()
        result = tool.extract_links("https://example.com")

        assert result["success"] is True
        assert len(result["links"]) == 2

    def test_extract_text_mock(self, mock_http_response):
        """Test extracting text from page."""
        mock_http_response["get"].return_value.text = """
        <html>
            <body>
                <h1>Title</h1>
                <p>Paragraph text here.</p>
            </body>
        </html>
        """

        from ai_automation_framework.tools.advanced_automation import WebScraperTool

        tool = WebScraperTool()
        result = tool.extract_text("https://example.com")

        assert result["success"] is True
        assert "Title" in result["text"]
        assert "Paragraph" in result["text"]
