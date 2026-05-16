# SQLite migration TODO (Oracle -> SQLite)

## app.py changes
- [ ] Replace Oracle driver (`oracledb`) with Python built-in `sqlite3`
- [ ] Implement `get_db()` that connects to `clinic.db` (or env `SQLITE_PATH`) 
- [ ] Implement `execute_query()` compatible with SQLite and parameter binding

- [ ] Update SQL queries:
  - [ ] `SELECT ... TO_CHAR(appointment_date, ...)` -> store ISO strings and return directly
  - [ ] `TO_DATE(:appointment_date, ...)` -> insert the plain `YYYY-MM-DD` string
  - [ ] Remove Oracle-only joins/formatting
- [ ] Add on-start DB initialization:
  - [ ] Create tables `users` and `appointments` if they don’t exist

## requirements.txt
- [ ] Remove `oracledb`
- [ ] Add any missing dependencies (likely none)

## render.yaml
- [ ] Remove ORACLE_* env vars
- [ ] (Optional) add `SQLITE_PATH`

## Test plan
- [ ] Run `python app.py` locally
- [ ] Register/login
- [ ] Create appointment, update status, delete appointment

## Notes
- SQLite is file-based; for Render “production-like” persistence you’d need volume/persistent storage.

