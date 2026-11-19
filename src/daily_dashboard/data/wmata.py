import json
import zipfile
from io import BytesIO, StringIO
from pathlib import Path
from thefuzz import process
import contextlib
import aiohttp
import aiofiles
import pandas as pd


class WmataException(Exception):

    def __init__(self, code: int, message: str):
        super().__init__(code, message)


class WmataApi(contextlib.AbstractAsyncContextManager):

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, *args):
        await self.session.__aexit__(*args)

    def __init__(self, api_key: str, gtfs_path: Path | str | None = None):
        self.api_key = api_key
        self.gtfs_path: Path | None = Path(gtfs_path) if gtfs_path else None
        self.session: aiohttp.ClientSession
        self.bus_stops: pd.DataFrame = pd.DataFrame(
            columns=('stop_id', 'stop_code', 'stop_name', 'stop_desc', 'stop_lat', 'stop_lon', 'zone_id', 'stop_url'))

    async def connect(self):
        self.session = await aiohttp.ClientSession().__aenter__()
        if self.gtfs_path:
            if not self.gtfs_path.exists():
                gtfs_zip = await self._get("https://api.wmata.com/gtfs/bus-gtfs-static.zip")
                async with aiofiles.open(self.gtfs_path, "wb") as fp:
                    await fp.write(gtfs_zip)
            else:
                async with aiofiles.open(self.gtfs_path, "rb") as fp:
                    gtfs_zip = await fp.read()
        else:
            gtfs_zip = await self._get("https://api.wmata.com/gtfs/bus-gtfs-static.zip")
        zip_file = zipfile.ZipFile(BytesIO(gtfs_zip))
        assert "stops.txt" in zip_file.namelist()
        stops_csv = StringIO(zip_file.read("stops.txt").decode("UTF-8"))
        self.bus_stops = pd.read_csv(stops_csv)[['stop_code', 'stop_name', 'stop_lat', 'stop_lon']]

    def find_stops_by_name(self, name: str, count: int = 10) -> pd.DataFrame:
        result = process.extract(name, self.bus_stops['stop_name'], limit=count)
        indexes = map(lambda r: r[2], result)
        return self.bus_stops.iloc[indexes]

    async def _get(self, url: str, **kwargs) -> bytes:
        assert self.session is not None
        async with self.session.get(url, params={'api_key': self.api_key} | kwargs) as r:
            content: bytes = await r.content.read()
            if r.status != 200:
                raise WmataException(r.status, content.decode("UTF-8"))
            return content

    async def _get_json(self, url: str, **kwargs) -> dict:
        return json.loads(await self._get(url, **kwargs))
