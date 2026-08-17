"""Business rules - the layer between HTTP and storage.

    notice_service.py   publishing, archiving, the board query, the escalation rule
    auth_service.py     login and staff registration

Services receive their repository through the CONSTRUCTOR rather than importing a
global. That single decision is what lets tests/conftest.py write
NoticeService(InMemoryNoticeRepository()) - no app startup, no database, a 4-second
test becomes 5 milliseconds - and it is what let Phase 3 swap in Mongo as a wiring
change instead of a code change.

What belongs here versus in the domain: a rule an entity can decide alone (has this
notice expired?) lives on the entity. A rule that needs coordination or policy
(compliance notices may not be posted at LOW priority; an unidentified caller may not
archive anything) lives here.
"""
