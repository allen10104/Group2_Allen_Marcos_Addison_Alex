"""The domain: entities, enums and the business behaviour that belongs with them.

THE ONE RULE HERE - no framework imports. This package uses only the standard library.
No pydantic, no pymongo, no fastapi. Two concrete payoffs, both visible in this repo:

  1. The Phase 3 database swap was cheap, because nothing in here knew what a database
     was in the first place.
  2. tests/test_domain.py needs no fixtures, no app startup and no I/O - it is the
     fastest part of the suite, so it is the part people actually run.

BEHAVIOUR LIVES WITH DATA. Notice.is_expired(), Notice.is_visible_to() and
Role.can_publish are methods on the objects that own the data, not helpers in the
service layer. A service that reaches into an object to compute what that object
already knows is the "anemic domain model" smell.
"""
