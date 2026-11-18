"""Flight Schedule Parser and Query Tool - command-line entry point."""

import sys
import os
import json
import argparse
import logging
from datetime import datetime

from validator import load_airports
from csv_loader import parse_files
from query import run_queries

# TODO: fill in your details: plain ASCII, no spaces or underscores.
STUDENT_ID = "251ADB078"
FIRST_NAME = "Ulvi"
LAST_NAME = "Mammadli"


def main(argv: list[str] | None = None) -> int:
    """Run the whole program and return the exit code (0, 1 or 2)."""

    parser = argparse.ArgumentParser(
        description="Flight Schedule Parser and Query Tool"
    )

    source = parser.add_mutually_exclusive_group(required=True)

    source.add_argument("-i", metavar="FILE", help="Parse one CSV file")
    source.add_argument("-d", metavar="FOLDER", help="Parse CSV files in a folder")
    source.add_argument("-j", metavar="FILE", help="Load an existing JSON database")

    parser.add_argument("-a", metavar="FILE", help="Airport list file")
    parser.add_argument("-o", metavar="FILE", help="Output databse path")
    parser.add_argument("-q", metavar="FILE", help="Query JSON file")
    parser.add_argument("-r", metavar="FOLDER", default=".", help="Response folder")

    args = parser.parse_args(argv)

    if (args.i is not None or args.d is not None) and args.a is None:
        parser.error("-a is required with -i or -d")

    if args.j and args.o:
        parser.error("-o cannot be used with -j")

    output_path = args.o if args.o else "db.json"

    logger = None
    handler = None

    try:
        if args.j:
            with open(args.j, "r", encoding="utf-8") as file:
                db = json.load(file)

            if not isinstance(db, list) or not all(
                isinstance(record, dict) for record in db
            ):
                raise ValueError("JSON database must be an array of objects")

        else:
            if args.i:
                paths = [args.i]

            else:
                if not os.path.isdir(args.d):
                    raise FileNotFoundError(f"Folder not found: {args.d}")

                paths = [
                    os.path.join(args.d, name)
                    for name in sorted(os.listdir(args.d))
                    if name.endswith(".csv")
                    and os.path.isfile(os.path.join(args.d, name))
                ]

                if not paths:
                    raise ValueError("No CSV files found in folder")

            airports = load_airports(args.a)

            log_path = os.path.join(
                os.path.dirname(os.path.abspath(output_path)),
                "errors.log"
            )

            logger = logging.getLogger("flight_parser")
            logger.setLevel(logging.INFO)

            handler = logging.FileHandler(
                log_path,
                mode="w",
                encoding="utf-8"
            )

            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )

            logger.addHandler(handler)

            db, errors = parse_files(paths, airports)

            for error in errors:
                logger.warning(error)

            with open(output_path, "w", encoding="utf-8") as file:
                json.dump(db, file, indent=2)

            print(f"Databse created: {output_path}")
            print(f"Valid flights: {len(db)}")
            print(f"Invalid rows: {len(errors)}")

        if args.q:
            with open(args.q, "r", encoding="utf-8") as file:
                queries = json.load(file)

            if not isinstance(queries, (dict, list)):
                raise ValueError("Query file must contain an object or array")

            results = run_queries(db, queries)

            if not os.path.isdir(args.r):
                raise FileNotFoundError(
                    f"Response folder not found: {args.r}"
                )

            timestamp = datetime.now().strftime("%Y%m%d_%H%M")

            response_name = (
                f"response_{STUDENT_ID}_{FIRST_NAME}_{LAST_NAME}_"
                f"{timestamp}.json"
            )

            response_path = os.path.join(args.r, response_name)

            with open(response_path, "w", encoding="utf-8") as file:
                json.dump(results, file, indent=2)

            print(f"Query response created: {response_path}")

        return 0

    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    finally:
        if logger is not None and handler is not None:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    sys.exit(main())
