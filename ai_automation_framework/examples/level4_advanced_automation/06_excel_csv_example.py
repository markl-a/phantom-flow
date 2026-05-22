#!/usr/bin/env python3
"""
Excel/CSV Processing Example
Demonstrates advanced data file processing
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from ai_automation_framework.tools.data_processing import ExcelAutomationTool, CSVProcessingTool, DataAnalysisTool


def demo_excel_csv():
    """Demonstrate Excel and CSV processing."""
    print("=" * 60)
    print("EXCEL/CSV PROCESSING DEMO")
    print("=" * 60)

    excel_tool = ExcelAutomationTool()
    csv_tool = CSVProcessingTool()
    analysis_tool = DataAnalysisTool()

    # Create temp directory for output files
    try:
        temp_dir = tempfile.mkdtemp()
        print(f"\nTemp directory: {temp_dir}")
    except Exception as e:
        print(f"Error creating temp directory: {e}")
        return

    print("\n1. CREATING EXCEL FILE")
    print("-" * 60)

    # Sample sales data
    sales_data = [
        {"date": "2025-01-01", "product": "Laptop", "quantity": 5, "price": 1200, "region": "North"},
        {"date": "2025-01-02", "product": "Mouse", "quantity": 20, "price": 25, "region": "South"},
        {"date": "2025-01-03", "product": "Keyboard", "quantity": 15, "price": 75, "region": "East"},
        {"date": "2025-01-04", "product": "Monitor", "quantity": 8, "price": 300, "region": "West"},
        {"date": "2025-01-05", "product": "Laptop", "quantity": 3, "price": 1200, "region": "South"},
        {"date": "2025-01-06", "product": "Mouse", "quantity": 25, "price": 25, "region": "North"},
        {"date": "2025-01-07", "product": "Keyboard", "quantity": 10, "price": 75, "region": "East"},
        {"date": "2025-01-08", "product": "Monitor", "quantity": 12, "price": 300, "region": "West"},
    ]

    try:
        excel_path = Path(temp_dir) / "sales_data.xlsx"
        result = excel_tool.write_excel(
            str(excel_path),
            sales_data,
            sheet_name="Sales",
            auto_format=True
        )

        print(f"✓ Created Excel file: {result['file']}")
        print(f"✓ Rows: {result['rows']}, Columns: {result['columns']}")
    except Exception as e:
        print(f"Error creating Excel file: {e}")
        return

    print("\n2. READING EXCEL FILE")
    print("-" * 60)

    try:
        result = excel_tool.read_excel(str(excel_path))

        print(f"✓ Read {result['rows']} rows")
        print(f"✓ Columns: {', '.join(result['columns'])}")
        print("\nPreview (first 3 rows):")
        for row in result['preview'][:3]:
            print(f"  {row}")
    except FileNotFoundError:
        print(f"Error: Excel file not found at {excel_path}")
        return
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    print("\n3. EXCEL TO CSV CONVERSION")
    print("-" * 60)

    try:
        csv_path = Path(temp_dir) / "sales_data.csv"
        result = excel_tool.excel_to_csv(str(excel_path), str(csv_path))

        print(f"✓ Converted Excel to CSV")
        print(f"✓ Output: {result['output']}")
        print(f"✓ Rows: {result['rows']}")
    except Exception as e:
        print(f"Error converting Excel to CSV: {e}")
        return

    print("\n4. READING CSV FILE")
    print("-" * 60)

    try:
        result = csv_tool.read_csv(str(csv_path))

        print(f"✓ Read {result['rows']} rows")
        print(f"✓ Data types: {result['dtypes']}")
    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_path}")
        return
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    print("\n5. FILTERING CSV DATA")
    print("-" * 60)

    try:
        filtered_path = Path(temp_dir) / "laptops_only.csv"
        result = csv_tool.filter_csv(
            str(csv_path),
            column='product',
            value='Laptop',
            output_path=str(filtered_path)
        )

        print(f"✓ Original rows: {result['original_rows']}")
        print(f"✓ Filtered rows: {result['filtered_rows']}")
        print(f"\nFiltered data:")
        for row in result['data']:
            print(f"  {row}")
    except Exception as e:
        print(f"Error filtering CSV data: {e}")

    print("\n6. AGGREGATING CSV DATA")
    print("-" * 60)

    result = csv_tool.aggregate_csv(
        str(csv_path),
        group_by='product',
        aggregations={'quantity': 'sum', 'price': 'mean'}
    )

    print(f"✓ Groups: {result['groups']}")
    print("\nAggregated Sales by Product:")
    for row in result['data']:
        print(f"  • {row['product']}: {row['quantity']} units, Avg price: ${row['price']:.2f}")

    print("\n7. DATA ANALYSIS - STATISTICS")
    print("-" * 60)

    # Calculate quantity statistics
    stats = analysis_tool.get_statistics(sales_data, 'quantity')

    print(f"✓ Quantity Statistics:")
    print(f"  • Count: {stats['count']}")
    print(f"  • Mean: {stats['mean']:.2f}")
    print(f"  • Std Dev: {stats['std']:.2f}")
    print(f"  • Min: {stats['min']}")
    print(f"  • Max: {stats['max']}")
    print(f"  • Median (50%): {stats['50%']:.2f}")

    # Calculate price statistics
    stats = analysis_tool.get_statistics(sales_data, 'price')

    print(f"\n✓ Price Statistics:")
    print(f"  • Mean: ${stats['mean']:.2f}")
    print(f"  • Min: ${stats['min']:.2f}")
    print(f"  • Max: ${stats['max']:.2f}")

    print("\n8. MERGING MULTIPLE EXCEL FILES")
    print("-" * 60)

    try:
        # Create additional data files
        jan_data = [{"month": "Jan", "sales": 15000, "expenses": 8000}]
        feb_data = [{"month": "Feb", "sales": 18000, "expenses": 9000}]
        mar_data = [{"month": "Mar", "sales": 20000, "expenses": 9500}]

        jan_file = Path(temp_dir) / "jan.xlsx"
        feb_file = Path(temp_dir) / "feb.xlsx"
        mar_file = Path(temp_dir) / "mar.xlsx"
        merged_file = Path(temp_dir) / "q1_summary.xlsx"

        excel_tool.write_excel(str(jan_file), jan_data)
        excel_tool.write_excel(str(feb_file), feb_data)
        excel_tool.write_excel(str(mar_file), mar_data)

        result = excel_tool.merge_excel_files(
            [str(jan_file), str(feb_file), str(mar_file)],
            str(merged_file)
        )

        print(f"✓ Merged {result['files_merged']} files")
        print(f"✓ Total rows: {result['total_rows']}")
        print(f"✓ Output: {result['output']}")
    except Exception as e:
        print(f"Error merging Excel files: {e}")

    print("\n9. PRACTICAL USE CASE - SALES REPORT")
    print("-" * 60)

    # Calculate total revenue by product
    print("\nRevenue by Product:")
    for row in sales_data:
        revenue = row['quantity'] * row['price']
        print(f"  • {row['date']}: {row['product']} = ${revenue:,}")

    # Calculate totals
    total_revenue = sum(r['quantity'] * r['price'] for r in sales_data)
    total_units = sum(r['quantity'] for r in sales_data)

    print(f"\n📊 Summary:")
    print(f"  • Total Revenue: ${total_revenue:,}")
    print(f"  • Total Units Sold: {total_units}")
    print(f"  • Average Order Value: ${total_revenue / len(sales_data):.2f}")

    # Clean up
    print(f"\n✓ Example files created in: {temp_dir}")


if __name__ == "__main__":
    demo_excel_csv()

    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print("\nKey Features:")
    print("  ✓ Excel file creation with auto-formatting")
    print("  ✓ Reading Excel/CSV files")
    print("  ✓ Format conversion (Excel ↔ CSV)")
    print("  ✓ Data filtering and aggregation")
    print("  ✓ Statistical analysis")
    print("  ✓ Multiple file merging")
    print("  ✓ Business reporting")
