"""Console script for daily_dashboard."""
import json

from daily_dashboard.data import wmata
import asyncio
import configargparse
from dotenv import load_dotenv

from daily_dashboard.data.wmata import WmataApi


def main():
    load_dotenv()

    parser = configargparse.ArgumentParser()

    parser.add_argument("--config", help="Run interactive configuration tool", action="store_true")

    parser.add_argument(
        "--wmata-key",
        type=str,
        help="API key for developer.wmata.com",
        env_var="WMATA_API_KEY",
        required=True
    )

    parser.add_argument(
        "--wmata-bus-stop-codes",
        type=str,
        help="Comma-separated list of bus stop code for real-time bus predictions.",
        default="",
        env_var="WMATA_BUS_STOP_CODES"
    )

    parser.add_argument(
        "--wmata-bus-route-ids",
        type=str,
        help="Comma-separated list of dus route IDs for real-time predictions.",
        default="",
        env_var="WMATA_BUS_ROUTE_IDS"
    )

    parser.add_argument(
        "--wmata-eta-limit",
        type=int,
        help="Number of ETAs to include for each route.",
        default=1000,
        env_var="WMATA_ETA_LIMIT"
    )

    args = parser.parse_args()

    print(args.wmata_bus_stop_codes)
    print(args.wmata_bus_route_ids)

    context = {}

    wmata_api = WmataApi(args.wmata_key)

    bus_predictions = wmata_api.get_bus_predictions(
        map(int, args.wmata_bus_stop_codes.split(",")),
        args.wmata_bus_route_ids.split(","),
        limit=args.wmata_eta_limit
    )

    context['bus_predictions'] = bus_predictions

    rail_incidents = wmata_api.get_rail_incidents()

    context['rail_incidents'] = list(rail_incidents)

    print(json.dumps(context, indent=2))


def app() -> None:
    """Console script for daily_dashboard."""
    main()


if __name__ == "__main__":
    app()
