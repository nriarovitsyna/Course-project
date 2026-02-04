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
                "tuition_cost_rub_year": r.tuition_cost_rub_year,
                "budget_places": r.budget_places,
                "level": r.level,
            }
            for r in rows
        ]
        return pd.DataFrame(data)

    def build_dashboard(self):
        df = self._load_df()
        figures = []

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
                    "data": [{"type": "bar", "x": city_counts.index.tolist(), "y": city_counts.values.tolist(), "name": "Programs"}],
                    "layout": {"title": "Top cities by programs count"},
                }
            )

        df_scatter = df.dropna(subset=["tuition_cost_rub_year", "budget_places"])
        if not df_scatter.empty:
            figures.append(
                {
                    "data": [
                        {
                            "type": "scatter",
                            "mode": "markers",
                            "x": df_scatter["tuition_cost_rub_year"].tolist(),
                            "y": df_scatter["budget_places"].tolist(),
                            "name": "Programs",
                        }
                    ],
                    "layout": {
                        "title": "Tuition cost vs budget places",
                        "xaxis": {"title": "Tuition cost (RUB/year)"},
                        "yaxis": {"title": "Budget places"},
                    },
                }
            )

        level_counts = df.dropna(subset=["level"]).groupby("level")["id"].count()
        if not level_counts.empty:
            figures.append(
                {
                    "data": [{"type": "pie", "labels": level_counts.index.tolist(), "values": level_counts.values.tolist()}],
                    "layout": {"title": "Programs by level"},
                }
            )

        return {"figures": figures}