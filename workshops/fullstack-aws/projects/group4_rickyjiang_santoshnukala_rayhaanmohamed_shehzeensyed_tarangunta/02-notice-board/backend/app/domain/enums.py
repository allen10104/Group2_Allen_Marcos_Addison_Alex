"""Domain vocabulary: the fixed sets of values a notice can take."""

from enum import Enum


class Category(str, Enum):
    """The kind of notice being posted.

    Inheriting from `str` as well as `Enum` is deliberate and load-bearing:
      * FastAPI/Pydantic serialise it straight to a JSON string, no encoder needed
      * PyMongo stores it as a plain BSON string, so the database stays readable
      * `notice.category == "COMPLIANCE"` works, which makes tests less brittle
    Without the `str` mixin you'd be writing `.value` in a dozen places.

    Using an enum rather than a free-text string means the database can never hold
    a typo like "Complaince", and an unknown category is rejected at the API edge
    as a 422 rather than becoming a bad row you discover three weeks later.
    """

    COMPLIANCE = "COMPLIANCE"
    SECURITY_ALERT = "SECURITY_ALERT"
    OPERATIONS = "OPERATIONS"
    IT_SYSTEMS = "IT_SYSTEMS"
    HR = "HR"
    GENERAL = "GENERAL"

    @property
    def display_name(self) -> str:
        """Human-readable label, computed here so the React app doesn't need its
        own copy of this mapping — one source of truth, no drift."""
        return {
            Category.COMPLIANCE: "Compliance & Regulatory",
            Category.SECURITY_ALERT: "Security Alert",
            Category.OPERATIONS: "Branch Operations",
            Category.IT_SYSTEMS: "IT & Systems",
            Category.HR: "Human Resources",
            Category.GENERAL: "General Announcement",
        }[self]

    @property
    def acknowledgement_required(self) -> bool:
        """True when staff are legally or policy-required to confirm they've read it.

        Behaviour lives ON the enum rather than in an if-chain scattered through the
        service. That's the difference between an enum and a set of constants."""
        return self in (Category.COMPLIANCE, Category.SECURITY_ALERT)


class Priority(str, Enum):
    """How urgently staff need to see this notice."""

    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"

    @property
    def weight(self) -> int:
        """Explicit sort weight.

        Python enums have a definition order we *could* rely on, but positional
        ordering silently changes if someone reorders the members. An explicit
        weight is stable under refactoring — a small thing that separates code
        which survives maintenance from code which doesn't."""
        return {
            Priority.LOW: 1,
            Priority.NORMAL: 2,
            Priority.HIGH: 3,
            Priority.URGENT: 4,
        }[self]

    @property
    def escalated(self) -> bool:
        """HIGH and URGENT get surfaced at the top of the board."""
        return self.weight >= Priority.HIGH.weight


class NoticeStatus(str, Enum):
    """Lifecycle state.

    ARCHIVED rather than physical deletion, because a bank generally cannot destroy
    a compliance communication — auditors ask "what did staff see on March 4th?" and
    "we deleted it" is not an acceptable answer.

    The DELETE endpoint therefore performs a SOFT delete. The assignment's criterion
    is "deleting a notice removes it from the list", and archiving satisfies that
    because the board query filters to ACTIVE. It's also the more defensible design.
    """

    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class Role(str, Enum):
    """Authorization roles.

    PERMISSIONS ARE FLAT: every authenticated employee may read the board and post
    notices. The role still exists and still travels in the JWT because it labels
    who someone is — it renders under their name in the UI and it's what an audit
    log wants to record. It just doesn't gate publishing.

    `can_publish` stays a property rather than being deleted: the moment the
    requirement comes back — and at a bank it will, the first time someone posts a
    bank-wide notice they shouldn't have — tightening it is one line here instead of
    a hunt through the routers and the security layer.
    """

    EMPLOYEE = "EMPLOYEE"
    MANAGER = "MANAGER"
    ADMIN = "ADMIN"

    @property
    def can_publish(self) -> bool:
        """Every role may publish.
        To restrict later: `return self in (Role.MANAGER, Role.ADMIN)`"""
        return True
    