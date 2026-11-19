"""Console script for daily_dashboard."""

from daily_dashboard.data import wmata
import asyncio
import configargparse
from dotenv import load_dotenv


async def main():
    load_dotenv()

    parser = configargparse.ArgumentParser()

    parser.add_argument("--config", help="Run interactive configuration tool", action="store_true")

    parser.add_argument("--wmata-key", type=str, env_var="WMATA_API_KEY",
                        help="API key for developer.wmata.com", required=True)

    args = parser.parse_args()


def app() -> None:
    """Console script for daily_dashboard."""
    asyncio.run(main())


if __name__ == "__main__":
    app()
