# FastAPI is the class we use to create the actual application instance.
from fastapi import FastAPI

# CORSMiddleware is what lets a browser page served from another origin call
# this API. Without it the browser blocks the response and the frontend sees
# a CORS error even though the request reached the server and succeeded.
from fastapi.middleware.cors import CORSMiddleware

# Import the controllers that hold the routes. A controller is the top
# layer: it defines the routes and calls down into a service, which is the
# only layer that talks to Supabase.
from app.controllers import auth_controller, notice_controller, reaction_controller

# Create the FastAPI application.
#
# title and version are what appear on the generated documentation at /docs,
# which is worth setting because that page is how the frontend team will
# read this API.
app = FastAPI(
    title="Notice Board API",
    version="0.1.0",
)


# Allow requests from any origin, for now.
#
# "*" is deliberately temporary. It is the right setting while the frontend
# does not exist yet and the API is only ever reached from localhost or a
# tool like curl, and it means nothing has to be changed here when the Vite
# dev server picks a different port. Once the frontend is deployed behind
# CloudFront this should become that one origin, because "*" lets any page
# on the internet call this API from a visitor's browser.
#
# allow_credentials stays False, and that is not an oversight. The CORS spec
# forbids pairing credentials with a "*" origin, and browsers enforce it by
# rejecting the response, so turning it on here would break every request
# rather than enable anything. This API sends no cookies and reads no auth
# header today, so nothing needs it. Turn it on at the same time as
# replacing "*" with the real origin, not before.
#
# allow_methods and allow_headers cover DELETE and Content-Type, which the
# defaults do not: without them the browser preflight for POST and DELETE
# would fail while a plain GET carried on working, which is a confusing way
# to find out.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register each controller's router so its routes become part of the app.
# Each router carries its own prefix, /auth and /notices, so nothing is
# added here.
app.include_router(auth_controller.router)
app.include_router(notice_controller.router)

# The reaction router also sits under /notices. Its only path is
# /{notice_id}/reactions, which cannot collide with the notice routes, so
# registering it separately keeps the two concerns in their own files.
app.include_router(reaction_controller.router)


# GET /health
# Answers 200 with a small JSON body if the process is up.
#
# This is what a load balancer or the ECS/EC2 health check polls to decide
# whether this instance should receive traffic, and it is the first thing to
# curl when something looks wrong.
#
# It deliberately does not touch Supabase. A health check that queries the
# database turns a database hiccup into an instance the load balancer kills
# and replaces, which does not help, and it means every poll spends a round
# trip on the database. This answers one question only: is the application
# running and able to serve a request.
@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
