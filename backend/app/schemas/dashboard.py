"""
Dashboard Schemas

Defines response models for admin dashboard analytics endpoints.
"""

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field


class KpiMetric(BaseModel):
    """Single KPI metric shown on the admin dashboard."""

    label: str
    value: float = Field(..., description="Metric value (count or duration)")
    change: float = Field(..., description="Percentage change vs previous period")
    trend: Literal["up", "down", "flat"]
    description: str | None = None
    lower_is_better: bool = Field(False, description="If True, down trend is good (green), up trend is bad (red)")


class CategoryBreakdown(BaseModel):
    """Category aggregation for pie charts."""

    category_name: str
    count: int


class HallPerformance(BaseModel):
    """Performance summary per hall."""

    hall_name: str
    total: int
    pending: int
    in_progress: int
    done: int
    completion_rate: float
    change: float
    trend: Literal["up", "down", "flat"]


class TimelinePoint(BaseModel):
    """Monthly aggregate used by time-series charts."""

    period: str = Field(..., description="YYYY-MM label for the bucket")
    total: int
    pending: int
    in_progress: int
    done: int


class StatusBreakdown(BaseModel):
    """Status aggregation for donut charts."""

    status: str = Field(..., description="Status name (pending, in_progress, done)")
    count: int
    percentage: float = Field(..., description="Percentage of total issues")


class ResolutionTimeByHall(BaseModel):
    """Average resolution time per hall."""

    hall_name: str
    avg_days: float = Field(..., description="Average days to resolve issues")


class CategoryCount(BaseModel):
    """Category count for stacked bar charts."""

    category_name: str
    count: int


class CategoryByHallStacked(BaseModel):
    """Category breakdown per hall for stacked bar charts."""

    hall_name: str
    categories: List[CategoryCount]


class DateRange(BaseModel):
    """Date range used for filtering analytics."""

    from_: str = Field(..., alias="from", description="Start date (ISO format)")
    to: str = Field(..., description="End date (ISO format)")


class AdminDashboardResponse(BaseModel):
    """
    Combined payload containing all analytics for the admin dashboard.
    """

    generated_at: datetime
    kpis: List[KpiMetric]
    issues_by_category: List[CategoryBreakdown]
    issues_by_hall: List[HallPerformance]
    issues_over_time: List[TimelinePoint]
    issues_by_status: List[StatusBreakdown]
    resolution_time_by_hall: List[ResolutionTimeByHall]
    category_by_hall_stacked: List[CategoryByHallStacked]
    date_range: DateRange


