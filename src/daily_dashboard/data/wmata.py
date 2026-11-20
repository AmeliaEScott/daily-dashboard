import json
import zipfile
from io import BytesIO, StringIO
from pathlib import Path
from thefuzz import process
import contextlib
import requests
import pandas as pd


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
        result = process.extract(name, self.bus_stops['stop_name'], limit=count)
        indexes = map(lambda r: r[2], result)
        return self.bus_stops.iloc[indexes]

    def _get(self, url: str, **kwargs) -> bytes:
        r = requests.get(url, params={'api_key': self.api_key} | kwargs)
        content: bytes = r.content
        if r.status_code != 200:
            raise WmataException(r.status_code, content.decode("UTF-8"))
        return content

    def _get_json(self, url: str, **kwargs) -> dict:
        return json.loads(self._get(url, **kwargs))
