#!/usr/bin/env python3
"""
Web Scraping Example
Demonstrates web scraping and data extraction
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_automation_framework.tools.advanced_automation import WebScraperTool


def demo_web_scraping():
    """Demonstrate web scraping capabilities."""
    print("=" * 60)
    print("WEB SCRAPING DEMO")
    print("=" * 60)

    scraper = WebScraperTool()

    print("\n1. FETCHING WEB PAGE")
    print("-" * 60)
    # Using example.com as a safe test URL
    try:
        result = scraper.fetch_url("http://example.com")
    except Exception as e:
        print(f"Error fetching URL: {e}")
        print("Continuing with demo using cached HTML...")
        result = {'success': False}

    if result.get('success'):
        print(f"✓ Status Code: {result['status_code']}")
        print(f"✓ Content Length: {len(result['content'])} characters")
        print(f"✓ Content Type: {result['headers'].get('Content-Type', 'N/A')}")
        print(f"\nFirst 200 characters:")
        print(result['content'][:200])

        # Extract text from HTML
        try:
            print("\n2. EXTRACTING TEXT FROM HTML")
            print("-" * 60)
            text_result = scraper.extract_text(result['content'])
            if text_result['success']:
                print(f"✓ Extracted text:")
                print(f"  {text_result['text'][:300]}...")
        except Exception as e:
            print(f"Error extracting text: {e}")

        # Extract all links
        try:
            print("\n3. EXTRACTING LINKS")
            print("-" * 60)
            links_result = scraper.extract_links(result['content'], "http://example.com")
            if links_result['success']:
                print(f"✓ Found {links_result['count']} links")
                for link in links_result['links'][:5]:
                    print(f"  • {link['text']}: {link['url']}")
        except Exception as e:
            print(f"Error extracting links: {e}")
    else:
        print("✗ Failed to fetch URL, using sample HTML for demo")

    print("\n4. EXTRACTING SPECIFIC HTML ELEMENTS")
    print("-" * 60)

    # Sample HTML for demonstration
    sample_html = """
    <html>
    <body>
        <h1>Product Catalog</h1>
        <h2>Featured Items</h2>

        <table>
            <tr><th>Product</th><th>Price</th><th>Stock</th></tr>
            <tr><td>Laptop</td><td>$999</td><td>15</td></tr>
            <tr><td>Mouse</td><td>$25</td><td>150</td></tr>
            <tr><td>Keyboard</td><td>$75</td><td>80</td></tr>
        </table>

        <h2>Categories</h2>
        <div class="category">Electronics</div>
        <div class="category">Accessories</div>
        <div class="category">Software</div>
    </body>
    </html>
    """

    # Extract headings
    try:
        headings = scraper.extract_text(sample_html, tag='h2')
        if headings['success']:
            print(f"✓ Headings (h2):")
            for heading in headings['text']:
                print(f"  • {heading}")
    except Exception as e:
        print(f"Error extracting headings: {e}")

    # Extract table data
    try:
        print("\n5. EXTRACTING TABLE DATA")
        print("-" * 60)
        tables = scraper.extract_table_data(sample_html)
        if tables['success']:
            print(f"✓ Found {tables['table_count']} table(s)")
            for i, table in enumerate(tables['tables']):
                print(f"\nTable {i+1}:")
                for row in table:
                    print(f"  {' | '.join(row)}")
    except Exception as e:
        print(f"Error extracting table data: {e}")

    print("\n6. PRACTICAL USE CASE - PRICE MONITORING")
    print("-" * 60)
    print("Use Case: Monitor product prices on e-commerce sites")
    print("\nWorkflow:")
    print("  1. Fetch product page")
    print("  2. Extract price using CSS selectors")
    print("  3. Compare with previous price")
    print("  4. Send alert if price drops")
    print("  5. Log price history")

    # Simulated price extraction
    products = [
        {"name": "Laptop Pro", "current_price": 999, "previous_price": 1099},
        {"name": "Wireless Mouse", "current_price": 25, "previous_price": 25},
        {"name": "Mechanical Keyboard", "current_price": 75, "previous_price": 89},
    ]

    print("\nPrice Check Results:")
    for product in products:
        current = product['current_price']
        previous = product['previous_price']
        change = current - previous

        if change < 0:
            print(f"  🔽 {product['name']}: ${current} (${abs(change)} drop!)")
        elif change > 0:
            print(f"  🔼 {product['name']}: ${current} (${change} increase)")
        else:
            print(f"  ➖ {product['name']}: ${current} (no change)")

    print("\n7. DATA EXTRACTION SUMMARY")
    print("-" * 60)
    print("✓ HTTP requests")
    print("✓ HTML parsing")
    print("✓ Link extraction")
    print("✓ Text extraction")
    print("✓ Table parsing")
    print("✓ CSS selector support (via BeautifulSoup)")


def best_practices():
    """Print web scraping best practices."""
    print("\n\n" + "=" * 60)
    print("WEB SCRAPING BEST PRACTICES")
    print("=" * 60)
    print("\n1. LEGAL & ETHICAL:")
    print("  • Check robots.txt")
    print("  • Review terms of service")
    print("  • Respect rate limits")
    print("\n2. TECHNICAL:")
    print("  • Use proper User-Agent headers")
    print("  • Implement retry logic")
    print("  • Handle errors gracefully")
    print("  • Cache responses when appropriate")
    print("\n3. PERFORMANCE:")
    print("  • Add delays between requests")
    print("  • Use async for multiple URLs")
    print("  • Implement connection pooling")


if __name__ == "__main__":
    demo_web_scraping()
    best_practices()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
