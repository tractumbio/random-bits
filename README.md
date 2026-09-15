# random-bits

## sql_py_test.py

A self-contained SQL + Python test. No dependencies beyond Python 3 itself --
`sqlite3` and `unittest` are both standard library, and the database is built in
memory each run.

```bash
python3 sql_py_test.py          # run the tests
python3 sql_py_test.py --demo   # print the data and query results instead
```

It builds a two-table schema, loads sample rows, and asserts against the results
of aggregate queries as well as the `CHECK` and `FOREIGN KEY` constraints.
