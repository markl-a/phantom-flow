#!/usr/bin/env python3
"""Count solutions per category"""
import os
from pathlib import Path

kaggle_dir = Path("kaggle_solutions")
categories = {}

for category_dir in sorted(kaggle_dir.iterdir()):
    if category_dir.is_dir():
        py_files = list(category_dir.rglob("*.py"))
        # Exclude run_all.py
        py_files = [f for f in py_files if f.name != "run_all.py"]
        categories[category_dir.name] = len(py_files)

# Sort by count
sorted_categories = sorted(categories.items(), key=lambda x: x[1])

print("Categories sorted by file count:")
print("=" * 50)
for cat, count in sorted_categories:
    print(f"{cat:30s}: {count:3d} files")

print("\n" + "=" * 50)
print(f"Total: {sum(categories.values())} files")
