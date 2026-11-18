"""Running queries against the flight database."""

import re
import math
from datetime import datetime


RECORD_KEYS = {
    "flight_id",
    "origin",
    "destination",
    "departure_datetime",
    "arrival_datetime",
    "price"
}

STRING_FILTERS = {
    "flight_id",
    "origin",
    "destination"
}

DATETIME_FILTERS = {
    "departure_datetime",
    "arrival_datetime"
}

NUMBER_FILTER = {
    "price",
    "min_price"
}

ALLOWED_KEYS = (
    RECORD_KEYS
    | STRING_FILTERS
    | DATETIME_FILTERS
    | NUMBER_FILTER
    | {"sort_by", "order", "limit"}
)


def valid_datetime(value: str) -> bool:
    """Check whether a datetime has the exact required format."""

    if not isinstance(value,str):
        return False

    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}", value):
        return False

    try:
        datetime.strptime(value, "%Y-%m-%d %H:%M")
        return True
    except ValueError:
        return False

    

def run_query(db: list[dict], query: dict) -> dict:
    """Return one response entry for one query object."""

    invalid_result = {
        "query": query,
        "error": "INVALID_QUERY",
        "matches": []
    }

    if not isinstance(query, dict):
        return invalid_result

    if any(key not in ALLOWED_KEYS for key in query):
        return invalid_result

    for key in STRING_FILTERS:
        if key in query and not isinstance(query[key], str):
            return invalid_result

    for key in DATETIME_FILTERS:
        if key in query and not valid_datetime(query[key]):
            return invalid_result

    for key in NUMBER_FILTER:
        if key in query:
            value = query[key]

            if isinstance(value, bool) or not isinstance(value, (int, float)):
                return invalid_result

            if not math.isfinite(value, float) and not math.isfinite(value):
                return invalid_result

    if "sort_by" in query:
        if not isinstance(query["sort_by"], str):
            return invalid_result

        if query["sort_by"] not in RECORD_KEYS:
            return invalid_result

    if "order" in query:
        if "sort_by" not in query:
            return invalid_result

        if query["order"] not in ("asc", "desc"):
            return invalid_result


    if "limit" in query:
        limit = query["limit"]

        if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
            return invalid_result

    matches = []

    for flight in db:
        if "flight_id" in query and flight["flight_id"] != query["flight_id"]:
            continue

        if "origin" in query and flight["origin"] != query["origin"]:
            continue

        if "destination" in query and flight["destination"] != query["destination"]:
            continue

        if "departure_datetime" in query:
            if flight["departure_datetime"] < query["departure_datetime"]:
                continue

        if "arrival_datetime" in query:
            if flight["arrival_datetime"] > query["arrival_datetime"]:
                continue

        if "price" in query and flight["price"] > query["price"]:
            continue

        if "min_price" in query and flight["price"] < query["min_price"]:
            continue

        matches.append(flight)

    if "sort_by" in query:
        reverse = query.get("order", "asc") == "desc"

        matches = sorted(
            matches,
            key=lambda flight: flight[query["sort_by"]],
            reverse=reverse
        )

    if "limit" in query:
        matches = matches[:query["limit"]]


    return {
        "query": query,
        "matches": matches
    }


def run_queries(db: list[dict], queries: dict | list) -> list[dict]:
    """Accept one query object or a list of them; always return a list."""

    if isinstance(queries, dict):
        queries = [queries]

    if not isinstance(queries, list):
        return []

    return [run_query(db, query) for query in queries]
