"""Storage - ports and adapters.

    base.py     the PORTS: abstract classes saying what the application needs from
                storage, in the application vocabulary (find_board, find_by_username).
                No dicts, no BSON and no connection strings appear in those signatures.
    memory.py   adapter #1: a plain dict. Phase 2 storage, and still the test double.
    mongo.py    adapter #2: MongoDB. Phase 3 storage.

WHY THE ABSTRACT BASE CLASS EARNS ITS KEEP: the service layer depends on the port, not
on either adapter, so the single `settings.repository` value is the entire swap (see
dependencies.py). Adding Mongo changed no service, no route and no test.

The in-memory adapter is NOT throwaway code. It stays because it is a real object with
real behaviour that cannot drift from the interface the way a hand-written mock does -
which is exactly what you want in a test double.
"""
