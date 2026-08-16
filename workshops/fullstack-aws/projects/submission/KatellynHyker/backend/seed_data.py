"""
Seed the database with demo users and notices for local development.

Run manually (never automatically) with your venv active, from inside
backend/:

    python seed_data.py

Safe to re-run -- skips anything that already exists instead of erroring
on duplicate emails. Only ever point this at a throwaway/dev database
(check DATABASE_URL in your .env) -- never run it against real user data.
"""

import time

from app.models.database import SessionLocal, UserORM, NoticeORM, init_db
from app.security.passwords import hash_password

DEMO_PASSWORD = "password123"

DEMO_USERS = [
    "alice@example.com",
    "bob@example.com",
    "carla@example.com",
]

DEMO_NOTICES = [
    (
        "alice@example.com",
        "Welcome to the board",
        "This is a shared notice board -- anyone logged in can post, but only "
        "you can edit or delete your own notices.",
    ),
    (
        "alice@example.com",
        "Office closed Friday",
        "Reminder that the office is closed this Friday for the holiday.",
    ),
    (
        "bob@example.com",
        "Free pizza in the break room",
        "There's leftover pizza from the team meeting -- help yourselves before 3pm!",
    ),
    (
        "bob@example.com",
        "Looking for a ride to the airport",
        "Anyone headed toward the airport Thursday morning? Could use a ride.",
    ),
    (
        "carla@example.com",
        "New coffee machine installed",
        "The new coffee machine is up and running on the 2nd floor.",
    ),
    (
        "carla@example.com",
        "Lost: blue water bottle",
        "Left a blue water bottle in the conference room, if anyone's seen it let me know.",
    ),
]

# (email, title, new content) -- applied as a follow-up edit after creation,
# so the seed data includes at least one notice showing the "(edited)"
# indicator in the UI.
EDITED_NOTICES = [
    (
        "bob@example.com",
        "Free pizza in the break room",
        "There's leftover pizza from the team meeting -- help yourselves before "
        "3pm! (Update: it's gone, sorry!)",
    ),
]


def seed():
    init_db()
    db = SessionLocal()
    try:
        users_by_email = {}
        created_users = 0
        for email in DEMO_USERS:
            user = db.query(UserORM).filter(UserORM.email == email).first()
            if user is None:
                user = UserORM(email=email, hashed_password=hash_password(DEMO_PASSWORD))
                db.add(user)
                db.flush()
                created_users += 1
            users_by_email[email] = user

        created_notices = 0
        for email, title, content in DEMO_NOTICES:
            author = users_by_email[email]
            existing = (
                db.query(NoticeORM)
                .filter(NoticeORM.user_id == author.user_id, NoticeORM.title == title)
                .first()
            )
            if existing is None:
                notice = NoticeORM(user_id=author.user_id, title=title, content=content)
                db.add(notice)
                created_notices += 1

        db.commit()

        # Follow-up edit so at least one notice shows the "(edited)" indicator
        # -- only applied if it hasn't already been edited (content doesn't
        # already match the "edited" version), so re-running stays a no-op.
        # The pause makes sure updated_at lands meaningfully after
        # created_at -- without it both timestamps land within the same
        # script execution (milliseconds apart), which is too small a gap
        # for the frontend to treat as a real edit.
        if created_notices > 0:
            time.sleep(1)
        edited_count = 0
        for email, title, new_content in EDITED_NOTICES:
            author = users_by_email[email]
            notice = (
                db.query(NoticeORM)
                .filter(NoticeORM.user_id == author.user_id, NoticeORM.title == title)
                .first()
            )
            if notice is not None and notice.content != new_content:
                notice.content = new_content
                edited_count += 1
        db.commit()

        print(
            f"Seed complete: {created_users} user(s) created, "
            f"{created_notices} notice(s) created, {edited_count} notice(s) edited."
        )
        print(f"\nDemo login (all seeded users share this password): {DEMO_PASSWORD}")
        for email in DEMO_USERS:
            print(f"  - {email}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()