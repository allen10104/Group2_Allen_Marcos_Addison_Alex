"""Login and staff registration."""

import logging

from app.domain.employee import Employee
from app.domain.enums import Role
from app.errors import InvalidCredentialsError
from app.repositories.base import EmployeeRepository
from app.schemas.auth import LoginRequest, LoginResponse
from app.security.jwt_service import create_access_token
from app.security.password import hash_password, verify_password

log = logging.getLogger(__name__)


class AuthService:
    """Turns credentials into a token, and creates staff accounts.

    Same constructor-injection shape as NoticeService, and for the same reasons: the
    tests can hand it an in-memory repository, and Phase 3 swapped in Mongo without
    touching a line in here.

    This service is the ONLY caller of hash_password / verify_password. Keeping that
    surface tiny is deliberate - if you ever need to audit how passwords are handled,
    it is this file plus security/password.py, and nothing else.
    """

    def __init__(self, repository: EmployeeRepository) -> None:
        self._repo = repository

    def login(self, request: LoginRequest) -> LoginResponse:
        """Verify credentials and mint a JWT.

        The three failure paths below all raise the SAME exception on purpose, which
        the handler in main.py turns into an identical 401. Read the comment on the
        first one - it is the reason, and it applies to all three.
        """
        employee = self._repo.find_by_username(request.username)

        # SAME exception whether the username is unknown or the password is wrong.
        # Distinct messages let an attacker enumerate valid usernames - "user not
        # found" vs "wrong password" tells them which half to keep guessing. At a bank
        # that is a findable defect in a pen test report.
        if employee is None:
            log.warning("Failed login: unknown username=%s", request.username)
            raise InvalidCredentialsError()

        if not verify_password(request.password, employee.password_hash):
            log.warning("Failed login: bad password for username=%s", request.username)
            raise InvalidCredentialsError()

        # A disabled account is a valid password that must still not get in - think
        # of someone who left the bank on Friday. Same generic error again: telling a
        # caller "this account is disabled" confirms the username exists.
        if not employee.enabled:
            raise InvalidCredentialsError()

        token, expires_in = create_access_token(employee)
        log.info("Successful login: username=%s roles=%s", employee.username, employee.roles)

        # The profile fields ride along with the token so React can render the user
        # box and decide whether to show "New notice" WITHOUT decoding the JWT
        # client-side. Decoding it in the browser would work, but it teaches the
        # frontend the token format - and then changing a claim breaks the UI.
        return LoginResponse(
            access_token=token,
            expires_in=expires_in,
            employee_id=employee.employee_id,
            username=employee.username,
            full_name=employee.full_name,
            department=employee.department,
            roles=sorted(employee.roles, key=lambda r: r.value),
            can_publish=employee.can_publish,
        )

    def register(
        self, employee_id: str, username: str, password: str,
        full_name: str, department: str | None = None, roles: set[Role] | None = None,
    ) -> Employee:
        """Create a staff account. ADMIN-only at the HTTP edge (see api/auth.py).

        Raising a plain ValueError for a duplicate username is intentional: main.py
        already maps ValueError to a 400, so this needs no HTTP knowledge and no new
        exception type. The uniqueness check here is application-level, not a database
        constraint - good enough for a workshop, but a unique index on `username` is
        what would actually prevent a race between two simultaneous registrations.
        """
        if self._repo.find_by_username(username) is not None:
            raise ValueError("Username already taken")

        # THE line that matters: hash before construction, so a raw password never
        # reaches the Employee object and therefore can never reach the database.
        employee = Employee.create(
            employee_id=employee_id,
            username=username,
            password_hash=hash_password(password),
            full_name=full_name,
            department=department,
            roles=roles or {Role.EMPLOYEE},     # least privilege by default
        )
        return self._repo.save(employee)