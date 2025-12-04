"""
Utility script to remove a hall and its related data.

Usage:
    python scripts/delete_hall.py --name "Hall Name"

The script will:
1. Find the hall by name.
2. Delete all issues associated with the hall.
3. Delete all users linked to the hall (typically the hall admin).
4. Delete the hall record itself.

Only use this for maintenance/cleanup tasks (e.g., removing test data).
"""

import argparse
from app.database import SessionLocal
from app.models import Hall, User, Issue


def delete_hall(hall_name: str) -> None:
    """Delete a hall and its related users/issues."""
    session = SessionLocal()
    try:
        hall = session.query(Hall).filter(Hall.name == hall_name).first()
        if not hall:
            print(f"Hall '{hall_name}' not found.")
            return

        issues_deleted = (
            session.query(Issue)
            .filter(Issue.hall_id == hall.id)
            .delete(synchronize_session=False)
        )
        users_deleted = (
            session.query(User)
            .filter(User.hall_id == hall.id)
            .delete(synchronize_session=False)
        )

        session.delete(hall)
        session.commit()

        print(
            f"Deleted hall '{hall_name}'. "
            f"Users removed: {users_deleted}. Issues removed: {issues_deleted}."
        )
    except Exception as exc:
        session.rollback()
        print(f"Failed to delete hall '{hall_name}': {exc}")
    finally:
        session.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Delete a hall and associated records."
    )
    parser.add_argument(
        "--name",
        required=True,
        help="Exact hall name to delete (case-sensitive).",
    )
    args = parser.parse_args()
    delete_hall(args.name)

