# SQL Developer + Admin login fixes checklist

- [ ] Fix `app.py` route ordering/duplicate corrupted section: remove embedded/garbled `/sql-dev` and `sql_exec` code and place clean route definitions before the normal page routes.
- [ ] Ensure login response `user` includes `email` and `role`.
- [ ] Ensure backend uses correct DB file by default (`clinic.db`).
- [ ] Verify admin login redirects to `/admin`.
- [ ] Add/verify SQL Developer UI (`templates/sql_developer.html`) and JS (`static/js/sql_developer.js`).
- [ ] Verify `/api/sql-exec` allows admin-only read-only SELECT (server-side) and returns rows.
- [ ] Run quick manual tests:
  - [ ] Login as admin -> `/admin`
  - [ ] Login as user -> `/user`
  - [ ] Admin open SQL Developer and run `SELECT * FROM users LIMIT 10;`

