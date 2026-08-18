# Marks app/controllers/ as a Python package so main.py can do
# "from app.controllers import notice_controller".
#
# Kept empty on purpose. Importing the controllers here would create a
# circular import the moment a controller ever needs something from the app
# package itself.
