"""Pydantic DTOs - the wire contract, kept deliberately separate from the domain.

WHY NOT JUST RETURN THE DOMAIN OBJECTS? Two reasons, one of them a security bug:

  1. Coupling. Return the Notice dataclass from a route and the HTTP contract IS the
     storage model. Rename a field for Mongo and the React app breaks silently.
  2. Leakage. Employee carries password_hash. Serialise it straight out of a route and
     every staff password hash has been published to the browser.

These classes are the seam that prevents both. They also buy validation and the
generated OpenAPI docs at /docs from the same declaration.

The asymmetry between NoticeCreate and NoticeResponse is the point, not duplication:
what a client may SEND (title, body, category...) is a smaller set than what the server
SENDS BACK (id, author, timestamps, derived labels). Fields a client must not control -
author, id, status - are absent from the input model, so they are designed out rather
than validated away.
"""
