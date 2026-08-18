# Marks app/ as a Python package so "app.main", "app.db" and the models,
# services and controllers packages underneath are importable. Uvicorn is
# started with "app.main:app", which only resolves because this file exists.
#
# Intentionally empty. Putting imports here would make them run on every
# "import app.anything", which is a slow and surprising side effect.
