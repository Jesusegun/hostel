"""
Utility script to permanently delete categories and their issues.

Usage:
    python scripts/delete_category.py --names "Category One" "Category Two"

Steps performed for each category name:
1. Find the category by name (case-insensitive).
2. Delete all issues referencing that category.
3. Delete the category record itself.

Only run this for test data you are sure can be removed permanently.
"""

import argparse
from typing import List
from sqlalchemy import func
from app.database import SessionLocal
from app.models import Category, Issue


def delete_category_by_name(session, name: str) -> None:
    """Delete a category and its issues given the category name."""
    category = (
        session.query(Category)
        .filter(func.lower(Category.name) == name.lower())
        .first()
    )
    if not category:
        print(f"[SKIP] Category '{name}' not found.")
        return

    print(f"[INFO] Deleting category '{category.name}' (id={category.id})...")
    issues_deleted = (
        session.query(Issue)
        .filter(Issue.category_id == category.id)
        .delete(synchronize_session=False)
    )

    session.delete(category)
    session.commit()

    print(
        f"[DONE] Category '{category.name}' deleted. "
        f"Issues removed: {issues_deleted}."
    )


def delete_categories(category_names: List[str]) -> None:
    """Delete multiple categories by their names."""
    session = SessionLocal()
    try:
        for name in category_names:
            delete_category_by_name(session, name)
    except Exception as exc:
        session.rollback()
        print(f"[ERROR] Failed during deletion: {exc}")
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Permanently delete categories and their issues."
    )
    parser.add_argument(
        "--names",
        nargs="+",
        required=True,
        help="List of category names to delete (case-insensitive match).",
    )
    args = parser.parse_args()
    delete_categories(args.names)

