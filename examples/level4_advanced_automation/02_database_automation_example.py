#!/usr/bin/env python3
"""
Database Automation Example
Demonstrates SQL query generation and database operations
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_automation_framework.tools.advanced_automation import DatabaseAutomationTool


def demo_database_automation():
    """Demonstrate database automation capabilities."""
    print("=" * 60)
    print("DATABASE AUTOMATION DEMO")
    print("=" * 60)

    try:
        # Initialize database tool (using in-memory SQLite)
        db = DatabaseAutomationTool(":memory:")

        print("\n1. CONNECTING TO DATABASE")
        print("-" * 60)
        result = db.connect()
        print(f"Status: {result}")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return

    try:
        print("\n2. CREATING TABLE")
        print("-" * 60)
        schema = {
            "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
            "name": "TEXT NOT NULL",
            "email": "TEXT UNIQUE",
            "age": "INTEGER",
            "created_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
        }
        result = db.create_table("users", schema)
        print(f"Created 'users' table: {result}")
    except Exception as e:
        print(f"Error creating table: {e}")
        return

    try:
        print("\n3. GENERATING AND EXECUTING INSERT QUERIES")
        print("-" * 60)
        users = [
            {"name": "Alice Johnson", "email": "alice@example.com", "age": 28},
            {"name": "Bob Smith", "email": "bob@example.com", "age": 35},
            {"name": "Carol White", "email": "carol@example.com", "age": 42},
            {"name": "David Brown", "email": "david@example.com", "age": 31},
            {"name": "Eve Davis", "email": "eve@example.com", "age": 29}
        ]

        for user in users:
            try:
                query, values = db.generate_insert_query("users", user)
                print(f"\nGenerated Query: {query}")
                print(f"Values: {values}")
                result = db.execute_query(query, values)
                print(f"Inserted: {user['name']} - {result}")
            except Exception as e:
                print(f"Error inserting {user['name']}: {e}")
                continue
    except Exception as e:
        print(f"Error in insert operations: {e}")
        return

    print("\n4. GENERATING AND EXECUTING SELECT QUERIES")
    print("-" * 60)

    # Select all users
    query = db.generate_select_query("users")
    print(f"\nQuery: {query}")
    result = db.execute_query(query)
    print(f"\nAll Users ({result['rows']} rows):")
    for row in result['data']:
        print(f"  • {row['name']} ({row['age']}) - {row['email']}")

    # Select users with age > 30
    query = "SELECT * FROM users WHERE age > 30"
    print(f"\n\nQuery: {query}")
    result = db.execute_query(query)
    print(f"\nUsers over 30 ({result['rows']} rows):")
    for row in result['data']:
        print(f"  • {row['name']} ({row['age']})")

    # Select with limit
    query = db.generate_select_query("users", limit=3)
    print(f"\n\nQuery: {query}")
    result = db.execute_query(query)
    print(f"\nFirst 3 Users:")
    for row in result['data']:
        print(f"  • {row['name']}")

    print("\n5. UPDATING RECORDS")
    print("-" * 60)
    query = "UPDATE users SET age = 36 WHERE name = 'Bob Smith'"
    print(f"Query: {query}")
    result = db.execute_query(query)
    print(f"Updated: {result}")

    print("\n6. COMPLEX QUERY - AGGREGATION")
    print("-" * 60)
    query = "SELECT AVG(age) as avg_age, COUNT(*) as total FROM users"
    print(f"Query: {query}")
    result = db.execute_query(query)
    print(f"\nStatistics:")
    print(f"  • Average Age: {result['data'][0]['avg_age']:.1f}")
    print(f"  • Total Users: {result['data'][0]['total']}")

    print("\n7. PRACTICAL USE CASE - SALES DATABASE")
    print("-" * 60)

    # Create sales table
    sales_schema = {
        "id": "INTEGER PRIMARY KEY AUTOINCREMENT",
        "product": "TEXT",
        "quantity": "INTEGER",
        "price": "REAL",
        "sale_date": "DATE"
    }
    db.create_table("sales", sales_schema)
    print("✓ Created sales table")

    # Insert sales data
    sales = [
        {"product": "Laptop", "quantity": 5, "price": 1200.00, "sale_date": "2025-01-10"},
        {"product": "Mouse", "quantity": 20, "price": 25.00, "sale_date": "2025-01-10"},
        {"product": "Keyboard", "quantity": 15, "price": 75.00, "sale_date": "2025-01-11"},
        {"product": "Monitor", "quantity": 8, "price": 300.00, "sale_date": "2025-01-11"},
    ]

    for sale in sales:
        query, values = db.generate_insert_query("sales", sale)
        db.execute_query(query, values)

    print("✓ Inserted sales data")

    # Calculate total revenue
    query = "SELECT SUM(quantity * price) as total_revenue FROM sales"
    result = db.execute_query(query)
    print(f"\nTotal Revenue: ${result['data'][0]['total_revenue']:,.2f}")

    # Sales by product
    query = "SELECT product, SUM(quantity) as total_qty, SUM(quantity * price) as revenue FROM sales GROUP BY product"
    result = db.execute_query(query)
    print("\nSales by Product:")
    for row in result['data']:
        print(f"  • {row['product']}: {row['total_qty']} units = ${row['revenue']:,.2f}")

    # Close database
    try:
        db.close()
        print("\n✓ Database operations completed successfully")
    except Exception as e:
        print(f"Error closing database: {e}")


if __name__ == "__main__":
    demo_database_automation()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nKey Features Demonstrated:")
    print("  ✓ Table creation")
    print("  ✓ Query generation (INSERT, SELECT)")
    print("  ✓ Data manipulation (UPDATE)")
    print("  ✓ Aggregation queries")
    print("  ✓ Practical business use case")
