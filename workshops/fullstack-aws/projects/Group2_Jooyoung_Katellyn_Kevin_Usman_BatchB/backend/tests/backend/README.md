# Backend unit tests

- **Plan:** [UNIT_TESTING_PLAN.md](./UNIT_TESTING_PLAN.md)
- **P0 suite:** `conftest.py` + `test_*.py` in this folder

## Run

From `Group2_Jooyoung_Katellyn_Kevin_Usman_BatchB/`:

```powershell
.\venv\Scripts\Activate.ps1
pytest backend/tests/backend -v
```

`conftest.py` sets `NOTICE_BOARD_REPO=memory` so tests never need Supabase.
