#!/usr/bin/env python3
"""Self-contained SQL + Python test.

Runs anywhere Python 3 is installed -- no pip install, no database server.
The whole database lives in memory and disappears when the process exits.

    python3 sql_py_test.py          # run the tests
    python3 sql_py_test.py --demo   # print the data and query results instead
"""

import sqlite3
import sys
import unittest

SCHEMA = """
CREATE TABLE region (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE sale (
    id        INTEGER PRIMARY KEY,
    region_id INTEGER NOT NULL REFERENCES region(id),
    product   TEXT    NOT NULL,
    units     INTEGER NOT NULL CHECK (units > 0),
    unit_cost REAL    NOT NULL CHECK (unit_cost >= 0)
);
"""

REGIONS = [(1, "north"), (2, "south"), (3, "east")]

SALES = [
    (1, 1, "widget", 10, 2.50),
    (2, 1, "gadget", 4, 12.00),
    (3, 2, "widget", 7, 2.50),
    (4, 2, "widget", 3, 2.50),
    (5, 3, "gadget", 1, 12.00),
]


def build_db():
    """Return an in-memory database loaded with the sample data."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.executemany("INSERT INTO region VALUES (?, ?)", REGIONS)
    conn.executemany("INSERT INTO sale VALUES (?, ?, ?, ?, ?)", SALES)
    conn.commit()
    return conn


REVENUE_BY_REGION = """
SELECT r.name            AS region,
       SUM(s.units)      AS units,
       SUM(s.units * s.unit_cost) AS revenue
FROM sale s
JOIN region r ON r.id = s.region_id
GROUP BY r.name
ORDER BY revenue DESC
"""

TOP_PRODUCT = """
SELECT product, SUM(units) AS units
FROM sale
GROUP BY product
ORDER BY units DESC
LIMIT 1
"""


class SqlTest(unittest.TestCase):
    def setUp(self):
        self.conn = build_db()

    def tearDown(self):
        self.conn.close()

    def test_row_counts(self):
        count = self.conn.execute("SELECT COUNT(*) FROM sale").fetchone()[0]
        self.assertEqual(count, len(SALES))

    def test_revenue_by_region(self):
        rows = self.conn.execute(REVENUE_BY_REGION).fetchall()
        self.assertEqual([r["region"] for r in rows], ["north", "south", "east"])
        self.assertAlmostEqual(rows[0]["revenue"], 73.00)  # 10*2.50 + 4*12.00
        self.assertAlmostEqual(rows[1]["revenue"], 25.00)  # 10*2.50
        self.assertAlmostEqual(rows[2]["revenue"], 12.00)  # 1*12.00

    def test_top_product_by_units(self):
        row = self.conn.execute(TOP_PRODUCT).fetchone()
        self.assertEqual(row["product"], "widget")
        self.assertEqual(row["units"], 20)

    def test_check_constraint_rejects_zero_units(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO sale VALUES (99, 1, 'widget', 0, 2.50)"
            )

    def test_foreign_key_rejects_unknown_region(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute(
                "INSERT INTO sale VALUES (99, 42, 'widget', 1, 2.50)"
            )


def demo():
    conn = build_db()
    print("revenue by region")
    for row in conn.execute(REVENUE_BY_REGION):
        print(f"  {row['region']:<6} {row['units']:>3} units  {row['revenue']:>7.2f}")

    row = conn.execute(TOP_PRODUCT).fetchone()
    print(f"\ntop product: {row['product']} ({row['units']} units)")
    conn.close()


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo()
    else:
        unittest.main(verbosity=2)
