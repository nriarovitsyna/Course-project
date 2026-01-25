"""
Аналитика: считаем агрегаты и отдаём Plotly JSON.

ТЗ прямо говорит: analyticsservice.py, groupby/mean/count и отдача Plotly JSON schema,
а на фронте Plotly.newPlot строит bar/scatter/pie. [file:1]
"""

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.program import Program


class AnalyticsService:
    def __init__(self, db: Session):
        self.db = db

    def _load_df(self) -> pd.DataFrame:
        rows = self.db.execute(select(Program)).scalars().all()
        data = [
            {
                "id": r.id,
                "city": r.city,
                "tuitionfee": r.tuitionfee,
                "budgetplaces": r.budgetplaces,
                "educationallevel": r.educationallevel,
            }
            for r in rows
        ]
        return pd.DataFrame(data)

    def build_dashboard(self):
        df = self._load_df()

        figures = []

        # 1) Bar: количество программ по городам (top 10)
        if not df.empty:
            city_counts = (
                df.dropna(subset=["city"])
                .groupby("city")["id"]
                .count()
                .sort_values(ascending=False)
                .head(10)
            )
            figures.append(
                {
                    "data": [
                        {
                            "type": "bar",
                            "x": city_counts.index.tolist(),
                            "y": city_counts.values.tolist(),
                            "name": "Programs",
                        }
                    ],
                    "layout": {"title": "Top cities by programs count"},
                }
            )

        # 2) Scatter: tuitionfee vs budgetplaces (если есть данные)
        df_scatter = df.dropna(subset=["tuitionfee", "budgetplaces"])
        if not df_scatter.empty:
            figures.append(
                {
                    "data": [
                        {
                            "type": "scatter",
                            "mode": "markers",
                            "x": df_scatter["tuitionfee"].tolist(),
                            "y": df_scatter["budgetplaces"].tolist(),
                            "name": "Programs",
                        }
                    ],
                    "layout": {"title": "Tuition fee vs budget places", "xaxis": {"title": "Tuition fee"}, "yaxis": {"title": "Budget places"}},
                }
            )

        # 3) Pie: доли уровней (educationallevel)
        level_counts = df.dropna(subset=["educationallevel"]).groupby("educationallevel")["id"].count()
        if not level_counts.empty:
            figures.append(
                {
                    "data": [
                        {
                            "type": "pie",
                            "labels": level_counts.index.tolist(),
                            "values": level_counts.values.tolist(),
                        }
                    ],
                    "layout": {"title": "Programs by level"},
                }
            )

        return {"figures": figures}
