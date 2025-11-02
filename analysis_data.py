from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

DATASET_PATH = Path(__file__).with_name("movies_dataset.csv")


@dataclass
class MovieAnalytics:
    """Prepare reusable aggregates for the analysis dashboard."""

    dataframe: pd.DataFrame

    @classmethod
    def from_dataset(cls, dataset_path: Path = DATASET_PATH) -> "MovieAnalytics":
        df = pd.read_csv(dataset_path)
        numeric_cols = ["Budget", "Revenue", "Profit"]
        df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors="coerce")
        df["Release Year"] = pd.to_numeric(df["Release Year"], errors="coerce")
        df.dropna(subset=numeric_cols + ["Release Year"], inplace=True)
        df = df[df["Budget"] > 0]
        return cls(dataframe=df.reset_index(drop=True))

    def top_genres_by_average_profit(self, n: int = 8) -> List[Dict[str, Any]]:
        series = (
            self.dataframe.groupby("genre")["Profit"].mean().sort_values(ascending=False).head(n)
        )
        return [
            {"genre": genre, "average_profit": float(round(value / 1_000_000, 2))}
            for genre, value in series.items()
        ]

    def median_profit_margin_by_genre(self, n: int = 8) -> List[Dict[str, Any]]:
        df = self.dataframe.copy()
        df["margin"] = df["Profit"] / df["Budget"]
        series = df.groupby("genre")["margin"].median().sort_values(ascending=False).head(n)
        return [
            {"genre": genre, "median_margin": float(round(value, 3))}
            for genre, value in series.items()
        ]

    def revenue_profit_trend(self) -> List[Dict[str, Any]]:
        trend = (
            self.dataframe.groupby("Release Year")[["Revenue", "Profit"]]
            .mean()
            .sort_index()
        )
        return [
            {
                "release_year": int(year),
                "average_revenue": float(round(values["Revenue"] / 1_000_000, 2)),
                "average_profit": float(round(values["Profit"] / 1_000_000, 2)),
            }
            for year, values in trend.iterrows()
        ]

    def metric_correlations(self) -> List[Dict[str, Any]]:
        metrics = ["Budget", "Revenue", "Profit"]
        corr_matrix = self.dataframe[metrics].corr().round(3)
        pairs: List[Dict[str, Any]] = []
        for idx, metric in enumerate(metrics):
            for other in metrics[idx + 1 :]:
                pairs.append(
                    {
                        "pair": f"{metric} vs {other}",
                        "value": float(corr_matrix.loc[metric, other]),
                    }
                )
        return pairs

    def top_movies_by_profit_and_margin(self, n: int = 6) -> List[Dict[str, Any]]:
        df = self.dataframe.copy()
        df["margin"] = df["Profit"] / df["Budget"]
        ranked = df.sort_values(by=["Profit", "margin"], ascending=False).head(n)
        return [
            {
                "title": row["Movie Name"],
                "genre": row["genre"],
                "release_year": int(row["Release Year"]),
                "revenue": float(round(row["Revenue"] / 1_000_000, 2)),
                "profit": float(round(row["Profit"] / 1_000_000, 2)),
                "margin": float(round(row["margin"], 2)),
            }
            for _, row in ranked.iterrows()
        ]

    def summary_payload(self) -> Dict[str, Any]:
        return {
            "top_genres_average_profit": self.top_genres_by_average_profit(),
            "median_profit_margin_by_genre": self.median_profit_margin_by_genre(),
            "revenue_profit_trend": self.revenue_profit_trend(),
            "metric_correlations": self.metric_correlations(),
            "top_movies_by_profit_and_margin": self.top_movies_by_profit_and_margin(),
        }