"""HTTP layer: the only package that knows this application is a web API.

Routers translate between HTTP and the service layer and do nothing else - no business
rules, no database calls. A rule that leaks into a route becomes untestable without
spinning up the whole app, and it can no longer be reused by a CLI, a scheduled job or
a future message consumer.

Two routers live here: notices.py (the board) and auth.py (login / register / me).
Both are mounted in main.py, which is also where exceptions become HTTP responses - so
the routes themselves contain no try/except and no status-code juggling.

The security split is visible in notices.py: the GET routes take no identity, because
reads are public and a visitor to the deployed site must see content immediately, while
POST / PUT / DELETE each declare `me: CurrentUser = Depends(get_current_user)`.
"""
