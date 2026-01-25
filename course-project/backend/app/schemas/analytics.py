"""
Схема ответа для /api/v1/analytics/dashboard.

По ТЗ backend отдаёт JSON под Plotly (traces/layout). [file:1]
Здесь упрощённо: возвращаем массив "figures", каждая фигура = {data, layout}.
"""

from pydantic import BaseModel


class PlotlyFigure(BaseModel):
    data: list[dict]
    layout: dict


class AnalyticsDashboardOut(BaseModel):
    figures: list[PlotlyFigure]
