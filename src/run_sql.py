"""Run every query in sql/ with DuckDB and write the results to data/output/<query name>.csv."""
from pathlib import Path
import os
import duckdb

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "output"
OUT.mkdir(parents=True, exist_ok=True)
os.chdir(ROOT)                      # queries use paths relative to the project root

con = duckdb.connect()
for sql_file in sorted((ROOT / "sql").glob("*.sql")):
    df = con.sql(sql_file.read_text(encoding="utf-8")).df()
    df.to_csv(OUT / f"{sql_file.stem}.csv", index=False)
    print(f"{sql_file.name:28s} -> {len(df):>8,} rows")
