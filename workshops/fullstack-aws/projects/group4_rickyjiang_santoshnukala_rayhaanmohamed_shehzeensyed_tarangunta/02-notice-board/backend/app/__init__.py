"""Notice Board backend - a layered (clean / hexagonal) FastAPI application.

WHY LAYERS AT ALL, for an app this small? Because the assignment makes us swap the
database (Phase 3) and bolt authentication on (Phase 5) after the app already works.
Those are exactly the changes that wreck a single-file app. Here each one lands in one
layer:

    api/          HTTP in, HTTP out. Parses requests, calls a service, shapes JSON.
                  Knows FastAPI. Knows nothing about Mongo or bcrypt.
    services/     The business rules. Knows the domain and the repository INTERFACES.
                  Knows nothing about HTTP status codes or BSON.
    domain/       Entities and their behaviour. Pure standard library - no pydantic,
                  no pymongo, no fastapi. The part that would survive a rewrite.
    repositories/ Storage. base.py declares the ports; memory.py and mongo.py are two
                  interchangeable adapters.
    schemas/      Pydantic DTOs - the wire contract, deliberately separate from domain.
    security/     Password hashing and JWT mint / verify.

THE DEPENDENCY RULE: arrows point INWARD, toward the domain.
api -> services -> repository interface -> domain. Nothing in domain/ imports anything
above it, which is why the domain tests need no fixtures and run in under a millisecond.

The payoff is measurable in this repo: swapping the in-memory dict for MongoDB touched
dependencies.py and added mongo.py. No route, no service and no test changed.
"""
