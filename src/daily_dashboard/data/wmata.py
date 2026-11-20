import json
import zipfile
from io import BytesIO, StringIO
from pathlib import Path
from typing import Iterable

from thefuzz import process
import contextlib
import requests
import pandas as pd
import re
from dataclasses import dataclass


class WmataException(Exception):

    def __init__(self, code: int, message: str):
        super().__init__(code, message)


class WmataApi:

    def __init__(self, api_key: str, gtfs_path: Path | str | None = None):
        self.api_key = api_key
        self.gtfs_path: Path | None = Path(gtfs_path) if gtfs_path else None
        self.bus_stops: pd.DataFrame = pd.DataFrame(
            columns=('stop_id', 'stop_code', 'stop_name', 'stop_desc', 'stop_lat', 'stop_lon', 'zone_id', 'stop_url'))

    def load_gtfs(self):
        if self.gtfs_path:
            if not self.gtfs_path.exists():
                gtfs_zip = self._get("https://api.wmata.com/gtfs/bus-gtfs-static.zip")
                with open(self.gtfs_path, "wb") as fp:
                    fp.write(gtfs_zip)
            else:
                with open(self.gtfs_path, "rb") as fp:
                    gtfs_zip = fp.read()
        else:
            gtfs_zip = self._get("https://api.wmata.com/gtfs/bus-gtfs-static.zip")
        zip_file = zipfile.ZipFile(BytesIO(gtfs_zip))
        assert "stops.txt" in zip_file.namelist()
        stops_csv = StringIO(zip_file.read("stops.txt").decode("UTF-8"))
        self.bus_stops = pd.read_csv(stops_csv)[['stop_code', 'stop_name', 'stop_lat', 'stop_lon']]

    def find_stops_by_name(self, name: str, count: int = 10) -> pd.DataFrame:
        assert len(self.bus_stops) > 0
        result = process.extract(name, self.bus_stops['stop_name'], limit=count)
        indexes = map(lambda r: r[2], result)
        return self.bus_stops.iloc[indexes]

    def get_bus_predictions(self, stops: Iterable[int], routes: Iterable[str] | None = None, limit: int = 1000) -> dict[
        str, dict[str, list[int]]]:
        predictions = {}
        for stop in stops:
            result = self._get_json("http://api.wmata.com/NextBusService.svc/json/jPredictions", StopID=stop)
            for prediction in result['Predictions']:
                route_id: str = prediction['RouteID']
                direction: str = prediction['DirectionText']
                eta_minutes: int = prediction['Minutes']
                if route_id not in predictions:
                    predictions[route_id] = {}
                if direction not in predictions[route_id]:
                    predictions[route_id][direction] = []
                predictions[route_id][direction].append(eta_minutes)

        if routes:
            routes = set(routes)
            predictions = {route: predictions[route] for route in predictions.keys() & routes}

        for route in predictions.keys():
            etas: list[int]
            for direction, etas in predictions[route].items():
                predictions[route][direction] = list(sorted(etas))[0:limit]
        return predictions

    def get_rail_incidents(self, lines: Iterable[str] | None = None) -> set[str]:
        if lines:
            lines_filter = set(lines)
        else:
            lines_filter = {'RD', 'YL', 'GR', 'BL', 'OR', 'SV'}
        incidents = self._get_json("http://api.wmata.com/Incidents.svc/json/Incidents")
        affected_lines = set()
        for incident in incidents["Incidents"]:
            affected_lines |= set(re.split(r';\s*', incident['LinesAffected']))
        return affected_lines & lines_filter

    def _get(self, url: str, **kwargs) -> bytes:
        r = requests.get(url, params={'api_key': self.api_key} | kwargs)
        content: bytes = r.content
        if r.status_code != 200:
            raise WmataException(r.status_code, content.decode("UTF-8"))
        return content

    def _get_json(self, url: str, **kwargs) -> dict:
        return json.loads(self._get(url, **kwargs))
