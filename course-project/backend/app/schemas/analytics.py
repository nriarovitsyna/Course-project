from pydantic import BaseModel


class PlotlyFigure(BaseModel):
    data: list[dict]
    layout: dict


class AnalyticsDashboardOut(BaseModel):
    figures: list[PlotlyFigure]
