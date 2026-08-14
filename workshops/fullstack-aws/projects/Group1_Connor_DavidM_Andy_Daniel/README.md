# Notice Board

A full-stack notice board application: React frontend, Python Lambda backend, MongoDB database.

## Read the Assignment

👉 See [ASSIGNMENT.md](./ASSIGNMENT.md) for the full instructions, tiers, and submission checklist.

---

## What's Provided

| File | Description |
|------|-------------|
| `frontend/` | React app: do not modify |
| `backend/lambda_function.py` | Python Lambda handler: do not modify |
| `backend/requirements.txt` | Python dependencies |
| `build.py` | Packages the Lambda zip |
| `terraform/main.tf` | Scaffold with TODOs: you complete this |
| `terraform/variables.tf` | Variables already defined |
| `terraform/outputs.tf` | Scaffold with TODOs: you complete this |

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/notices` | Return all notices |
| POST | `/notices` | Create a notice `{ "name": "...", "message": "..." }` |
| DELETE | `/notices/{id}` | Delete a notice by ID |

# Group 1's Unique Selling Point!
We added a priority feature to notices in which notices can be marked as important.
- Important notices show up in a unique bright yellow card.
- Important notices appear before regular notices.