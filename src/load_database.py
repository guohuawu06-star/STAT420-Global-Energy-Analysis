import csv
import json
import sqlite3
from contextlib import closing

import pandas as pd

from src.config import PROCESSED, RESULTS, ROOT

TABLES = ("source_release", "geography", "indicator", "energy_observation")


def query_specs():
    text = (ROOT / "sql/queries.sql").read_text(encoding="utf-8")
    return [(block.splitlines()[0].strip(), block.split("\n", 1)[1].strip())
            for block in text.split("-- name: ")[1:]]


def load(engine):
    ddl = (ROOT / "sql/schema.sql").read_text(encoding="utf-8")
    if engine == "postgres":
        import psycopg

        connection = psycopg.connect("")
        version = "PostgreSQL " + connection.info.parameter_status("server_version")
    else:
        connection = sqlite3.connect(RESULTS / "energy.sqlite3")
        connection.execute("PRAGMA foreign_keys = ON")
        version = "SQLite " + sqlite3.sqlite_version

    with closing(connection), connection:
        cur = connection.cursor()
        if engine == "postgres":
            cur.execute("CREATE SCHEMA IF NOT EXISTS stat420_energy")
            cur.execute("SET LOCAL search_path = stat420_energy")
        else:
            cur.execute("BEGIN")
        for table in reversed(TABLES):
            cur.execute(f"DROP TABLE IF EXISTS {table}")
        for command in ddl.split(";"):
            if command.strip():
                cur.execute(command)

        for table in TABLES:
            with (PROCESSED / f"{table}.csv").open(encoding="utf-8", newline="") as source:
                reader = csv.reader(source)
                columns = next(reader)
                fields = ", ".join(columns)
                if engine == "postgres":
                    with cur.copy(f"COPY {table} ({fields}) FROM STDIN") as copy:
                        for row in reader:
                            copy.write_row([cell if cell else None for cell in row])
                else:
                    marks = ", ".join("?" for _ in columns)
                    cur.executemany(f"INSERT INTO {table} ({fields}) VALUES ({marks})",
                                    ([cell if cell else None for cell in row] for row in reader))

        counts = {}
        for table in TABLES:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[table] = cur.fetchone()[0]
        cur.execute("SELECT COUNT(value), COUNT(*) - COUNT(value), "
                    "SUM(CASE WHEN value = 0 THEN 1 ELSE 0 END) FROM energy_observation")
        present, missing, zeros = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM (SELECT release_id, geo_id, year, indicator_id FROM energy_observation "
                    "GROUP BY release_id, geo_id, year, indicator_id HAVING COUNT(*) > 1) AS duplicate_keys")
        assert cur.fetchone()[0] == 0
        if engine == "sqlite":
            assert not cur.execute("PRAGMA foreign_key_check").fetchall()

        queries = {}
        for name, statement in query_specs():
            cur.execute(statement)
            rows = cur.fetchall()
            frame = pd.DataFrame(rows, columns=[column[0] for column in cur.description])
            frame.to_csv(RESULTS / f"{name}.csv", index=False)
            queries[name] = len(rows)
    evidence = dict(engine=version, tables=counts, present=present, missing=missing, zeros=zeros,
                    duplicate_keys=0, foreign_keys_enforced=True, queries=queries)
    (RESULTS / "database_run.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    return evidence


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--db", choices=("postgres", "sqlite"), required=True)
    print(load(parser.parse_args().db))
