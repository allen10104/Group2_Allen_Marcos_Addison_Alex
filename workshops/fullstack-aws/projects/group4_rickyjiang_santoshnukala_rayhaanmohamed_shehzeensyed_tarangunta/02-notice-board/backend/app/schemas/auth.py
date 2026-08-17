"""Authentication request/response models."""

from pydantic import BaseModel, Field

from app.domain.enums import Role


class LoginRequest(BaseModel):
    """What the login form posts.

    min_length=1 rather than a real password policy: rules belong on REGISTRATION, not
    on login. Rejecting a short password at the login endpoint would leak the policy to
    an attacker and reject nothing a wrong password would not reject anyway.
    """

    username: str = Field(min_length=1)
    password: str = Field(min_length=1)

    def __repr__(self) -> str:
        """Never let a password reach a log.

        FastAPI logs request objects on some error paths, and a password in a
        CloudWatch log group is a genuine incident at a bank, not a style nit."""
        return f"LoginRequest(username={self.username!r}, password='***')"


class CurrentUser(BaseModel):
    """Who is making this request, reconstructed from the JWT claims.

    Small on purpose - no password, no account-expiry fields. The token already proved
    identity, so this carries only what routes actually need.
    """

    username: str
    employee_id: str
    full_name: str | None = None
    department: str | None = None
    roles: list[Role] = []

    @property
    def can_publish(self) -> bool:
        """Delegates to the Role enum instead of hardcoding the rule.

        Currently True for every role (permissions are flat - see Role). It stays a
        delegation so that restricting publishing later is one edit in enums.py rather
        than a hunt through routes, this class and the frontend."""
        return any(r.can_publish for r in self.roles)

    @property
    def is_admin(self) -> bool:
        """Used by require_admin for /api/auth/register.

        Flat permissions on NOTICES does not mean flat permissions on ACCOUNTS: letting
        any employee mint an account is a much worse problem than letting them post."""
        return Role.ADMIN in self.roles


class LoginResponse(BaseModel):
    """What a successful login returns.

    Profile fields travel alongside the token so React can render "Welcome, Priya" and
    decide whether to show the New Notice button without decoding the JWT client-side.

    NOTE: the frontend hiding a button is convenience, never security. The server
    enforces its rules independently.
    """

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    employee_id: str
    username: str
    full_name: str
    department: str | None
    roles: list[Role]
    can_publish: bool
    