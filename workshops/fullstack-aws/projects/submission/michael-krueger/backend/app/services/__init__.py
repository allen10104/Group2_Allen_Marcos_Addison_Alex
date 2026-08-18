# Marks app/services/ as a Python package so the controllers can do
# "from app.services import notice_service".
#
# Kept empty on purpose, unlike app/models/__init__.py. The models are
# re-exported there because they are referred to by name all over the app.
# The services are always called as notice_service.create_notice(...), which
# is worth keeping: it says at the call site that the work is happening in
# the service layer rather than in the controller.
