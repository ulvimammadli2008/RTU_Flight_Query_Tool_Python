"""Reading CSV files into flight records and error messages."""
import csv
import os

from validator import validate_row, to_record


def parse_files(paths: list[str], airports: set[str]) -> tuple[list[dict], list[str]]:
    """Process the CSV files in the order given."""

    records = []
    errors = []
    seen_flights = set()

    for path in paths:
        filename = os.path.basename(path)

        with open(path, "r", encoding="utf-8", newline="") as file:
            for line_number, line in enumerate(file, start=1):

                if line_number == 1:
                    continue

                original_line = line.rstrip("\r\n")

                if not original_line.strip():
                    continue

                if original_line.lstrip().startswith("#"):
                    continue

                fields = next(csv.reader([original_line]))

                error = validate_row(fields, airports)

                if error is not None:
                    errors.append(
                        f"{filename}:{line_number}: {error} | {original_line}"
                    )
                    continue

                stripped_fields = [field.strip() for field in fields]
                flight_key = (stripped_fields[0], stripped_fields[3])

                if flight_key in seen_flights:
                    errors.append(
                        f"{filename}:{line_number}: DUPLICATE_FLIGHT | {original_line}"
                    )
                    continue

                seen_flights.add(flight_key)

                records.append(to_record(fields))

    return records, errors