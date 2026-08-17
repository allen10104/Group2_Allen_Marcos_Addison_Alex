"""Bank staff who can log into the board."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.domain.enums import Role


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class Employee:
    """A staff member.

    SECURITY NOTE, written down in Phase 1 so it can't be forgotten in Phase 5:
    this class stores `password_hash`, never `password`. Naming the field for what
    it actually holds is a cheap way to make the wrong thing feel wrong — if you
    ever find yourself writing `emp.password_hash = raw_password`, the name tells
    you you've made a mistake. The bcrypt hashing happens in the service layer.
    """

    # Business key, e.g. "E10432". Distinct from the database id on purpose —
    # the DB id is an implementation detail, the employee number is what HR uses.
    employee_id: str

    username: str
    password_hash: str
    full_name: str
    department: str | None = None

    roles: set[Role] = field(default_factory=lambda: {Role.EMPLOYEE})
    enabled: bool = True

    created_at: datetime = field(default_factory=_utc_now)
    updated_at: datetime = field(default_factory=_utc_now)
    id: str | None = None

    @classmethod
    def create(
        cls,
        employee_id: str,
        username: str,
        password_hash: str,
        full_name: str,
        department: str | None = None,
        roles: set[Role] | None = None,
    ) -> "Employee":
        if not username or not username.strip():
            raise ValueError("Username is required")
        if not password_hash:
            raise ValueError("Password hash is required")

        return cls(
            employee_id=employee_id,
            # Usernames are case-insensitive. Normalising on the way IN means the
            # lookup on the way out only has to lowercase once, and "P.Raman" and
            # "p.raman" can never become two accounts.
            username=username.strip().lower(),
            password_hash=password_hash,
            full_name=full_name,
            department=department,
            # set(roles) makes a defensive copy — if the caller mutates the set they
            # passed in, we don't silently gain or lose roles.
            roles=set(roles) if roles else {Role.EMPLOYEE},
        )

    @property
    def can_publish(self) -> bool:
        """Delegates to the Role enum rather than hardcoding the rule here. With flat
        permissions this is True for everyone — but keeping it a delegation means
        changing Role.can_publish changes the whole application in one place."""
        return any(role.can_publish for role in self.roles)

    def has_role(self, role: Role) -> bool:
        return role in self.roles
    