"""
Dashboard Service

Provides analytics for the admin dashboards.

Responsibilities:
- Aggregate KPIs for the last 30 days (with trend comparison)
- Build hall/category breakdowns
- Produce timeline data for charts

Why a dedicated service?
- Keeps analytics logic separate from API/view layers
- Easier to extend with more metrics later
- Central place to harden performance-sensitive queries
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple
import logging

from sqlalchemy import case, func
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.models import Category, Hall, Issue
from app.models.issue import IssueStatus

logger = logging.getLogger(__name__)


def _now_utc() -> datetime:
    """Return timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


def _calc_change(current: float, previous: float) -> Tuple[float, str]:
    """
    Calculate percentage change and trend direction.

    Returns tuple of (percentage_change, trend_string)
    """
    if previous == 0:
        # Avoid division by zero. If no previous data but we have current,
        # treat as 100% increase. If both zero, change is flat.
        if current == 0:
            return 0.0, "flat"
        return 100.0, "up"

    delta = current - previous
    change = (delta / previous) * 100
    if delta > 0:
        trend = "up"
    elif delta < 0:
        trend = "down"
    else:
        trend = "flat"
    return round(change, 2), trend


def _shift_month(reference: datetime, offset: int) -> datetime:
    """
    Shift a datetime (assumed to be first day of month) by offset months.
    """
    year = reference.year + ((reference.month - 1 + offset) // 12)
    month = (reference.month - 1 + offset) % 12 + 1
    return datetime(year, month, 1, tzinfo=timezone.utc)


def get_admin_dashboard_summary(
    db: Session,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> Dict[str, Any]:
    """
    Build aggregated analytics required for the admin dashboard.

    Args:
        db: Database session
        date_from: Optional start date for filtering (defaults to 30 days ago)
        date_to: Optional end date for filtering (defaults to now)

    Returns:
        Dict[str, Any]: Structured payload for the API response.
    """

    now = _now_utc()
    
    # Default to last 30 days if no date range provided
    if date_from is None:
        date_from = now - timedelta(days=30)
    if date_to is None:
        date_to = now
    
    # Ensure dates are timezone-aware
    if date_from.tzinfo is None:
        date_from = date_from.replace(tzinfo=timezone.utc)
    if date_to.tzinfo is None:
        date_to = date_to.replace(tzinfo=timezone.utc)
    
    # Calculate previous period for trend comparison
    period_duration = date_to - date_from
    previous_period_start = date_from - period_duration
    previous_period_end = date_from

    def _count_issues(start: datetime, end: datetime | None = None, status: IssueStatus | None = None) -> int:
        """
        Count issues with error handling.
        
        Returns 0 if query fails (graceful degradation).
        """
        try:
            query = db.query(func.count(Issue.id))
            query = query.filter(Issue.created_at >= start)
            if end:
                query = query.filter(Issue.created_at < end)
            if status:
                query = query.filter(Issue.status == status)
            return query.scalar() or 0
        except SQLAlchemyError as e:
            logger.error(f"Error counting issues: {e}", exc_info=True)
            return 0
        except Exception as e:
            logger.error(f"Unexpected error counting issues: {e}", exc_info=True)
            return 0

    # Calculate current month start for "Issues This Month" KPI
    current_month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    previous_month_start = _shift_month(current_month_start, -1)
    
    # KPI counts (current period)
    total_current = _count_issues(date_from, date_to)
    total_previous = _count_issues(previous_period_start, previous_period_end)
    
    # Issues This Month
    issues_this_month = _count_issues(current_month_start, now)
    issues_previous_month = _count_issues(previous_month_start, current_month_start)

    pending_current = _count_issues(date_from, date_to, IssueStatus.PENDING)
    pending_previous = _count_issues(previous_period_start, previous_period_end, IssueStatus.PENDING)

    progress_current = _count_issues(date_from, date_to, IssueStatus.IN_PROGRESS)
    progress_previous = _count_issues(previous_period_start, previous_period_end, IssueStatus.IN_PROGRESS)

    done_current = _count_issues(date_from, date_to, IssueStatus.DONE)
    done_previous = _count_issues(previous_period_start, previous_period_end, IssueStatus.DONE)

    # Average resolution time (hours) for all time + trend
    try:
        avg_resolution_seconds = (
            db.query(
                func.avg(func.extract("epoch", Issue.resolved_at - Issue.created_at))
            )
            .filter(Issue.status == IssueStatus.DONE, Issue.resolved_at.isnot(None))
            .scalar()
        )
        avg_resolution_hours = round((avg_resolution_seconds or 0) / 3600, 2)
    except (SQLAlchemyError, Exception) as e:
        logger.error(f"Error calculating average resolution time: {e}", exc_info=True)
        avg_resolution_hours = 0.0

    try:
        avg_resolution_seconds_prev = (
            db.query(
                func.avg(func.extract("epoch", Issue.resolved_at - Issue.created_at))
            )
            .filter(
                Issue.status == IssueStatus.DONE,
                Issue.resolved_at.isnot(None),
                Issue.resolved_at >= previous_period_start,
                Issue.resolved_at < previous_period_end,
            )
            .scalar()
        )
        avg_resolution_hours_prev = round((avg_resolution_seconds_prev or 0) / 3600, 2)
    except (SQLAlchemyError, Exception) as e:
        logger.error(f"Error calculating previous period average resolution time: {e}", exc_info=True)
        avg_resolution_hours_prev = 0.0
    
    # Calculate Issues This Month trend
    month_change, month_trend = _calc_change(issues_this_month, issues_previous_month)

    total_change, total_trend = _calc_change(total_current, total_previous)
    pending_change, pending_trend = _calc_change(pending_current, pending_previous)
    progress_change, progress_trend = _calc_change(progress_current, progress_previous)
    done_change, done_trend = _calc_change(done_current, done_previous)
    resolution_change, resolution_trend = _calc_change(
        avg_resolution_hours,
        avg_resolution_hours_prev if avg_resolution_hours_prev else 0,
    )

    kpis = [
        {
            "label": "Total Issues",
            "value": total_current,
            "change": total_change,
            "trend": total_trend,
            "description": None,
            "lower_is_better": False,
        },
        {
            "label": "Pending",
            "value": pending_current,
            "change": pending_change,
            "trend": pending_trend,
            "description": "Lower is better",
            "lower_is_better": True,
        },
        {
            "label": "In Progress",
            "value": progress_current,
            "change": progress_change,
            "trend": progress_trend,
            "description": None,
            "lower_is_better": False,
        },
        {
            "label": "Resolved",
            "value": done_current,
            "change": done_change,
            "trend": done_trend,
            "description": None,
            "lower_is_better": False,
        },
        {
            "label": "Avg. Resolution (hrs)",
            "value": avg_resolution_hours,
            "change": resolution_change,
            "trend": resolution_trend,
            "description": "Lower is better",
            "lower_is_better": True,
        },
        {
            "label": "Issues This Month",
            "value": issues_this_month,
            "change": month_change,
            "trend": month_trend,
            "description": "Lower is better",
            "lower_is_better": True,
        },
    ]

    # Category breakdown (filtered by date range)
    try:
        category_rows = (
            db.query(
                Category.name.label("category_name"),
                func.count(Issue.id).label("count"),
            )
            .join(Issue, Issue.category_id == Category.id)
            .filter(Issue.created_at >= date_from, Issue.created_at < date_to)
            .group_by(Category.id)
            .order_by(func.count(Issue.id).desc())
            .all()
        )
        issues_by_category = [
            {"category_name": row.category_name, "count": row.count} for row in category_rows
        ]
    except (SQLAlchemyError, Exception) as e:
        logger.error(f"Error fetching category breakdown: {e}", exc_info=True)
        issues_by_category = []
    
    # Issues by Status (for Donut Chart)
    try:
        status_rows = (
            db.query(
                Issue.status,
                func.count(Issue.id).label("count"),
            )
            .filter(Issue.created_at >= date_from, Issue.created_at < date_to)
            .group_by(Issue.status)
            .all()
        )
        total_status_count = sum(row.count for row in status_rows)
        issues_by_status = []
        for row in status_rows:
            percentage = round((row.count / total_status_count * 100) if total_status_count > 0 else 0, 2)
            issues_by_status.append({
                "status": row.status.value,
                "count": row.count,
                "percentage": percentage,
            })
    except (SQLAlchemyError, Exception) as e:
        logger.error(f"Error fetching status breakdown: {e}", exc_info=True)
        issues_by_status = []

    # Hall performance (outer join to include halls with zero issues)
    status_case_pending = case((Issue.status == IssueStatus.PENDING, 1), else_=0)
    status_case_progress = case((Issue.status == IssueStatus.IN_PROGRESS, 1), else_=0)
    status_case_done = case((Issue.status == IssueStatus.DONE, 1), else_=0)

    try:
        hall_rows = (
            db.query(
                Hall.id.label("hall_id"),
                Hall.name.label("hall_name"),
                func.count(Issue.id).label("total"),
                func.sum(status_case_pending).label("pending"),
                func.sum(status_case_progress).label("in_progress"),
                func.sum(status_case_done).label("done"),
            )
            .outerjoin(Issue, (Issue.hall_id == Hall.id) & (Issue.created_at >= date_from) & (Issue.created_at < date_to))
            .group_by(Hall.id)
            .order_by(Hall.name.asc())
            .all()
        )
    except (SQLAlchemyError, Exception) as e:
        logger.error(f"Error fetching hall performance: {e}", exc_info=True)
        hall_rows = []

    try:
        prev_hall_counts = {
            hall_id: count
            for hall_id, count in db.query(
                Issue.hall_id,
                func.count(Issue.id),
            )
            .filter(
                Issue.created_at >= previous_period_start,
                Issue.created_at < previous_period_end,
            )
            .group_by(Issue.hall_id)
            .all()
        }
    except (SQLAlchemyError, Exception) as e:
        logger.error(f"Error fetching previous period hall counts: {e}", exc_info=True)
        prev_hall_counts = {}
    
    # Resolution Time by Hall
    try:
        resolution_time_rows = (
            db.query(
                Hall.id.label("hall_id"),
                Hall.name.label("hall_name"),
                func.avg(func.extract("epoch", Issue.resolved_at - Issue.created_at)).label("avg_seconds"),
            )
            .join(Issue, Issue.hall_id == Hall.id)
            .filter(
                Issue.status == IssueStatus.DONE,
                Issue.resolved_at.isnot(None),
                Issue.resolved_at >= date_from,
                Issue.resolved_at < date_to,
            )
            .group_by(Hall.id)
            .all()
        )
        resolution_time_by_hall = []
        for row in resolution_time_rows:
            avg_days = round((row.avg_seconds or 0) / 86400, 2)  # Convert seconds to days
            resolution_time_by_hall.append({
                "hall_name": row.hall_name,
                "avg_days": avg_days,
            })
    except (SQLAlchemyError, Exception) as e:
        logger.error(f"Error fetching resolution time by hall: {e}", exc_info=True)
        resolution_time_by_hall = []
    
    # Issues by Category per Hall (Stacked Bar Chart)
    try:
        category_by_hall_rows = (
            db.query(
                Hall.name.label("hall_name"),
                Category.name.label("category_name"),
                func.count(Issue.id).label("count"),
            )
            .join(Issue, Issue.hall_id == Hall.id)
            .join(Category, Issue.category_id == Category.id)
            .filter(Issue.created_at >= date_from, Issue.created_at < date_to)
            .group_by(Hall.id, Category.id)
            .order_by(Hall.name.asc(), func.count(Issue.id).desc())
            .all()
        )
        
        # Group by hall
        category_by_hall_dict: Dict[str, List[Dict[str, Any]]] = {}
        for row in category_by_hall_rows:
            if row.hall_name not in category_by_hall_dict:
                category_by_hall_dict[row.hall_name] = []
            category_by_hall_dict[row.hall_name].append({
                "category_name": row.category_name,
                "count": row.count,
            })
        
        category_by_hall_stacked = []
        for hall_name, categories in category_by_hall_dict.items():
            category_by_hall_stacked.append({
                "hall_name": hall_name,
                "categories": categories,
            })
    except (SQLAlchemyError, Exception) as e:
        logger.error(f"Error fetching category by hall data: {e}", exc_info=True)
        category_by_hall_stacked = []

    issues_by_hall = []
    for row in hall_rows:
        total = row.total or 0
        done_count = row.done or 0
        completion_rate = round((done_count / total * 100) if total else 0, 2)
        previous_total = prev_hall_counts.get(row.hall_id, 0)
        hall_change, hall_trend = _calc_change(total, previous_total)
        issues_by_hall.append(
            {
                "hall_name": row.hall_name,
                "total": total,
                "pending": row.pending or 0,
                "in_progress": row.in_progress or 0,
                "done": done_count,
                "completion_rate": completion_rate,
                "change": hall_change,
                "trend": hall_trend,
            }
        )

    # Timeline (last 6 months by month)
    months_to_show = 6
    current_month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    timeline_start = _shift_month(current_month_start, -(months_to_show - 1))

    # Timeline: Use date range if provided, otherwise last 6 months
    if date_from and date_to:
        # Use provided date range, but bucket by month
        timeline_start = datetime(date_from.year, date_from.month, 1, tzinfo=timezone.utc)
        timeline_end = date_to
        months_to_show = max(1, (date_to.year - date_from.year) * 12 + (date_to.month - date_from.month) + 1)
    else:
        # Default to last 6 months
        months_to_show = 6
        current_month_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        timeline_start = _shift_month(current_month_start, -(months_to_show - 1))
        timeline_end = now
    
    try:
        timeline_rows = (
            db.query(
                func.date_trunc("month", Issue.created_at).label("period"),
                func.count(Issue.id).label("total"),
                func.sum(status_case_pending).label("pending"),
                func.sum(status_case_progress).label("in_progress"),
                func.sum(status_case_done).label("done"),
            )
            .filter(Issue.created_at >= timeline_start, Issue.created_at < timeline_end)
            .group_by(func.date_trunc("month", Issue.created_at))
            .order_by(func.date_trunc("month", Issue.created_at))
            .all()
        )

        timeline_map = {
            row.period.date(): {
                "total": row.total or 0,
                "pending": row.pending or 0,
                "in_progress": row.in_progress or 0,
                "done": row.done or 0,
            }
            for row in timeline_rows
        }

        issues_over_time: List[Dict[str, Any]] = []
        for offset in range(months_to_show):
            month_start = _shift_month(timeline_start, offset)
            data = timeline_map.get(month_start.date(), {"total": 0, "pending": 0, "in_progress": 0, "done": 0})
            issues_over_time.append(
                {
                    "period": month_start.strftime("%Y-%m"),
                    "total": data["total"],
                    "pending": data["pending"],
                    "in_progress": data["in_progress"],
                    "done": data["done"],
                }
            )
    except (SQLAlchemyError, Exception) as e:
        logger.error(f"Error fetching timeline data: {e}", exc_info=True)
        # Return empty timeline data instead of failing completely
        issues_over_time = [
            {
                "period": _shift_month(timeline_start, offset).strftime("%Y-%m"),
                "total": 0,
                "pending": 0,
                "in_progress": 0,
                "done": 0,
            }
            for offset in range(months_to_show)
        ]

    return {
        "generated_at": now,
        "kpis": kpis,
        "issues_by_category": issues_by_category,
        "issues_by_hall": issues_by_hall,
        "issues_over_time": issues_over_time,
        "issues_by_status": issues_by_status,
        "resolution_time_by_hall": resolution_time_by_hall,
        "category_by_hall_stacked": category_by_hall_stacked,
        "date_range": {
            "from": date_from.isoformat(),
            "to": date_to.isoformat(),
        },
    }


