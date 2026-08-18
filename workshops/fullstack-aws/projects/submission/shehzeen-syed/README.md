# Notice Board — Shehzeen Syed

This is my submission for the Notice Board deployment assignment. Below I've
explained what the app does, what I built on top of the base assignment, what
I used to deploy it, and how you can test it live.

## Try it live

**App:** https://dn9tfs5rsbz2.cloudfront.net

**Admin login** (so you can test the admin-only features — pinning notices and
deleting/editing anyone's post, not just your own):

```
Username: admin
Password: hunter22222
```

You can also just click "Sign up" and create your own regular account to test
posting, editing, and deleting your own notices.

## What the app does

It's a shared corkboard: anyone can view the notices without logging in, but
you need an account to post one. Notices show up as sticky notes pinned to a
corkboard background, each with a slightly different color and tilt so they
don't look perfectly aligned — like an actual board. You can edit or delete
your own notices any time. Admin accounts can additionally pin a notice as
"important" (it jumps to the top and stays there, with a red tack and a
ribbon so it stands out), and can edit or delete anyone's notice, not just
their own.

## What I built beyond the assignment

I extended the app with a few features I thought made it feel more like a real product:

- **Email at sign-up** — registration now asks for and validates an email
  address, not just a username and password
- **Editing your own notices** — instead of only being able to delete and
  repost, you can now correct a notice after posting it (it gets marked
  "(edited)" with a timestamp)
- **Admin accounts** — some usernames can be granted admin rights, letting
  them moderate the board (edit/delete anyone's notice)
- **Pin as important** — admins can pin a notice so it always stays at the
  top of the board, even as newer notices get posted
- **A full corkboard redesign** — I rebuilt the whole UI to actually look
  like a corkboard with sticky notes, tacks/tape, a handwritten font, and a
  torn-corner delete button, instead of a plain list

## What I used

- **Backend:** Python, FastAPI, running on AWS Lambda through Mangum, sitting
  behind an API Gateway HTTP API
- **Database:** PostgreSQL — I used [Neon](https://neon.tech) (a managed,
  serverless Postgres host) instead of an EC2 instance. More on why below.
- **Frontend:** React + Vite, hosted as a static site on S3
- **CDN:** CloudFront in front of the S3 bucket, so the app is served over
  HTTPS with the S3 bucket itself locked down to CloudFront-only access
- **Infrastructure:** Terraform for everything in AWS
- **CI/CD:** GitHub Actions — every push to `main` that touches this project
  automatically rebuilds the Lambda, redeploys it, rebuilds the frontend,
  re-uploads it to S3, and invalidates the CloudFront cache

## One deviation worth explaining: Postgres on Neon, not EC2

The assignment's prerequisite is a PostgreSQL instance already running on
EC2 from an earlier lab. I didn't have one set up for this project, and this
training AWS account doesn't allow students to create IAM roles or several
other account-wide resources — I ran into `AccessDenied` errors trying to
provision things the "normal" way. Rather than get stuck, I used Neon, a
free managed Postgres provider, which the Lambda reaches over the internet
exactly the same way it would reach an EC2-hosted database — same
`psycopg2` connection code, same environment variables (`PG_HOST`, `PG_DB`,
etc.), no code differences at all. Functionally it satisfies the assignment's
actual requirement ("notices save to PostgreSQL and appear on the page"),
just hosted somewhere else.

## Deployment status — all three core tiers are done

- ✅ **Tier 1 (manual deploy):** S3 static site, Lambda, API Gateway, all
  resources prefixed `student-shehzeen-syed-`
- ✅ **Tier 2 (GitHub Actions):** pushing to `main` auto-deploys both the
  backend and frontend with no manual AWS CLI commands — see
  `.github/workflows/deploy-shehzeen-syed-notice-board.yml` at the repo root
- ✅ **Tier 3 (CloudFront):** the app is served over HTTPS via CloudFront,
  the S3 bucket is no longer publicly reachable directly, and every deploy
  automatically invalidates the CloudFront cache
- ⬜ Tier 4 (observability) — not attempted, this was the optional bonus tier

## How to test the full thing

1. Open the live URL above
2. You should see existing notices on the board already
3. Log in as `admin` (password above)
4. Post a notice — it should appear instantly
5. Pin it — it should jump to the top with a red tack and "Important" ribbon
6. Post a second notice as admin, or log out and sign up as a new user and
   post one — confirm the pinned one still stays on top
7. Try editing and deleting your own notice
8. Log in as a non-admin account and confirm you *can't* pin notices or
   delete/edit ones that aren't yours (only your own)

## Project structure, if you want to look at the code

```
notice-board/
├── backend/
│   ├── app.py                 # FastAPI app + Lambda entrypoint
│   ├── build.py                # Packages everything into lambda.zip
│   └── notice_board/           # Actual application code
│       ├── config.py            # Reads env vars
│       ├── database.py          # DB connection + table creation
│       ├── security.py          # Password hashing, JWT auth
│       ├── schemas.py           # Request/response models
│       └── routers/             # auth.py and notices.py — the actual endpoints
├── frontend/
│   └── src/
│       ├── App.jsx              # Main app state/logic
│       ├── api.js               # All calls to the backend
│       └── components/          # LoginForm, Composer, NoteCard
└── terraform/                  # All the AWS infrastructure
```

## A couple of honest limitations

- Email addresses are validated for format but not checked for uniqueness —
  you could register two accounts with the same email
- Admin access is controlled by an environment variable
  (`ADMIN_USERNAMES`), not a database column, so granting/revoking admin
  requires a redeploy
