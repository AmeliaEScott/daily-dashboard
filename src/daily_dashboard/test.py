import os

from daily_dashboard.data.wmata import WmataApi
from pathlib import Path
import asyncio
import pandas as pd
from dotenv import load_dotenv


async def main():
    load_dotenv()

    api: WmataApi
    async with WmataApi(os.environ["WMATA_API_KEY"], "gtfs.zip") as api:
        print(api.bus_stops.to_string(
            columns=('stop_code', 'stop_name', 'stop_lat', 'stop_lon')
        ))
        print("\n\n")
        print(api.find_stops_by_name("srhfdtgjdsrgsf", count=5))


if __name__ == "__main__":
    asyncio.run(main())
