#!/usr/bin/env python3
"""
Email Automation Example
Demonstrates sending and reading emails using the EmailAutomationTool
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_automation_framework.tools.advanced_automation import EmailAutomationTool


def demo_email_automation():
    """Demonstrate email automation capabilities."""
    print("=" * 60)
    print("EMAIL AUTOMATION DEMO")
    print("=" * 60)

    # Initialize email tool
    # Note: Replace with your actual SMTP/IMAP servers
    email_tool = EmailAutomationTool(
        smtp_server="smtp.gmail.com",
        smtp_port=587,
        imap_server="imap.gmail.com",
        imap_port=993
    )

    print("\n1. SENDING EMAIL (Simulated)")
    print("-" * 60)

    # Example 1: Send a simple email
    # NOTE: This will fail without real credentials
    # Replace with actual credentials to test
    print("Configuration:")
    print("  • SMTP Server: smtp.gmail.com:587")
    print("  • Recipient: example@example.com")
    print("  • Subject: Test Automation Email")
    print("\nNote: Use app-specific password for Gmail")
    print("Status: [DEMO MODE - requires real credentials]")

    # Example 2: Reading emails (simulated)
    print("\n\n2. READING EMAILS (Simulated)")
    print("-" * 60)
    print("Configuration:")
    print("  • IMAP Server: imap.gmail.com:993")
    print("  • Folder: INBOX")
    print("  • Limit: 10 latest emails")
    print("  • Filter: Unread only")
    print("\nStatus: [DEMO MODE - requires real credentials]")

    # Example 3: Practical use case
    print("\n\n3. PRACTICAL USE CASE")
    print("-" * 60)
    print("Use Case: Automated Daily Report Emailer")
    print("\nWorkflow:")
    print("  1. Generate report data")
    print("  2. Format as HTML email")
    print("  3. Send to stakeholders")
    print("  4. Log success/failure")

    # Simulated report
    report_data = {
        "date": "2025-01-15",
        "total_sales": 15000,
        "new_customers": 45,
        "orders": 120
    }

    html_body = f"""
    <html>
    <body>
        <h2>Daily Sales Report - {report_data['date']}</h2>
        <table border="1">
            <tr><td>Total Sales</td><td>${report_data['total_sales']}</td></tr>
            <tr><td>New Customers</td><td>{report_data['new_customers']}</td></tr>
            <tr><td>Total Orders</td><td>{report_data['orders']}</td></tr>
        </table>
    </body>
    </html>
    """

    print("\nGenerated HTML Report:")
    print(html_body[:200] + "...")

    print("\n✓ Email automation tool configured successfully")
    print("✓ Ready for production use with real credentials")


def setup_instructions():
    """Print setup instructions."""
    print("\n\n" + "=" * 60)
    print("SETUP INSTRUCTIONS")
    print("=" * 60)
    print("\nFor Gmail:")
    print("1. Enable 2FA in your Google account")
    print("2. Generate app-specific password")
    print("3. Use app password instead of regular password")
    print("\nFor other providers:")
    print("  • Outlook: smtp.office365.com:587")
    print("  • Yahoo: smtp.mail.yahoo.com:587")
    print("\nEnvironment Variables:")
    print("  export EMAIL_ADDRESS='your@email.com'")
    print("  export EMAIL_PASSWORD='your_app_password'")


if __name__ == "__main__":
    demo_email_automation()
    setup_instructions()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
