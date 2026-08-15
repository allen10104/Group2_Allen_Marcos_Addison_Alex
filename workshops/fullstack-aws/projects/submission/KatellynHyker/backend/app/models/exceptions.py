"""Domain exceptions.
 
Services raise these instead of thinking about HTTP at all; main.py maps
each one to a status code in one central place (see its exception handlers).
"""
 
 
class AppError(Exception):
    """Base class for every domain exception in this app."""
 
 
class NotFoundError(AppError):
    """The requested resource doesn't exist."""
 
 
class DuplicateError(AppError):
    """Attempted to create something that already exists (e.g. email taken)."""
 
 
class ValidationError(AppError):
    """Request is well-formed but violates a business rule."""
 
 
class UnauthorizedError(AppError):
    """Missing/invalid credentials, or a valid user acting on someone else's resource."""