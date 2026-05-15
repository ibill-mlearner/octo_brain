"""Real-data entrypoint for exercising the data logging package."""

from __future__ import annotations

from data_logging import DataLoggingArgumentParser, DatabaseLoggingRunner


def main() -> None:
    args = DataLoggingArgumentParser().parse_args()
    if args.steps < 1:
        raise ValueError("--steps must be at least 1")

    row_counts = DatabaseLoggingRunner().run(args.db_path, args.steps)
    print(f"database={args.db_path}")
    for table_name, row_count in row_counts.items():
        print(f"{table_name}={row_count}")


if __name__ == "__main__":
    main()
