"""Presentation-ready catalog data without exposing draft content publicly."""
import json
from datetime import datetime
from app.models.catalog import CatalogModel
from app.services.screening_rules import as_datetime, sales_open


class CatalogService:
    @staticmethod
    def movies():
        movies = CatalogModel.movies()
        for movie in movies:
            metadata = movie.get("metadata_json") or {}
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except ValueError:
                    metadata = {}
            movie["poster_url"] = metadata.get("poster_url", "") if isinstance(metadata, dict) else ""
        return movies

    @staticmethod
    def screenings():
        screenings = CatalogModel.screenings()
        now = datetime.now()
        for show in screenings:
            show["start_time"] = as_datetime(show["start_time"])
            show["end_time"] = as_datetime(show["end_time"])
            show["sales_open"] = sales_open(show["start_time"], now)
        return screenings

    @staticmethod
    def drafts():
        return CatalogModel.drafts()