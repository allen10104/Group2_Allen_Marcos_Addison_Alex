# os.getenv reads the Supabase connection details out of the environment,
# so neither the project URL nor the API key is ever written in the source.
import os

# lru_cache remembers what a function returned and hands the same object back
# on later calls. See the note above get_client() for why that matters here.
from functools import lru_cache

# load_dotenv copies the values out of the .env file into the environment,
# so the key stays in an untracked file instead of in the repository.
from dotenv import load_dotenv

# create_client builds the supabase-py client that talks to the project's
# REST API. Client is the type it returns, used below only as an annotation.
from supabase import Client, create_client

# Builds the Supabase client, and after the first call returns the one it
# already built.
#
# maxsize=1 is all that is needed because the function takes no arguments,
# so there is only ever one result to remember.
#
# One client for the whole application is the right shape. The client owns a
# pooled HTTP session underneath, so building a fresh one per request would
# open a new connection every time and throw away the pool.
#
# Everything happens in here, including reading .env, rather than at module
# level, for two reasons.
#
# The first is that nothing should raise while this module is being imported.
# If it did, the whole app would fail to start and even /health would be
# unreachable, which is exactly the endpoint you want answering while you
# work out that the config is wrong. Reading the config at first use means
# the app starts, /health reports it is up, and only the endpoints that
# actually need the database fail, with a message that says what to fix.
#
# The second is that module level constants are read once, when Python first
# imports the file, and never again. Creating .env after the server was
# already running therefore had no effect: the values stayed as they were at
# import, and the app kept insisting they were missing even after they were
# not. Reading them here means the first request after the file appears
# picks it up, which is the behaviour you expect while setting the project
# up. The cache still guarantees this runs only once.
#
# The consequence is that changing .env later needs a restart to take effect.
# That is the right trade: config is meant to be fixed for the life of a
# process, and a client that could change underneath a request would be a
# far stranger thing to debug.
@lru_cache(maxsize=1)
def get_client() -> Client:
    # Copy the values out of .env into the environment. Calling this more
    # than once is harmless, it simply does nothing if they are already
    # loaded, and real environment variables set by the deployment always
    # win over the file, which is what you want on EC2.
    load_dotenv()

    # The project URL, for example https://abcdefghijkl.supabase.co
    # Found in the Supabase dashboard under Project Settings, API.
    supabase_url = os.getenv("SUPABASE_URL")

    # The API key the client authenticates with. This is a secret: the anon
    # key is safe to expose in a browser but not in a public repository, and
    # a service role key must never leave the server at all.
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_KEY are not set. "
            "Copy .env.example to .env and fill them in."
        )

    return create_client(supabase_url, supabase_key)
