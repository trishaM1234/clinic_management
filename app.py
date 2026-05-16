import logging
import os
import sqlite3
from flask import Flask, request, jsonify, g, render_template
from functools import wraps
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash

load_dotenv()

# ========================
# APP CONFIG
# ========================
app = Flask(__name__)
app.config["DEBUG"] = os.getenv("FLASK_DEBUG", "false").lower() == "true"
logging.basicConfig(level=logging.INFO)

# ========================
# SQLITE CONFIG
# ========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "clinic.db")

# Default to database.db (requested). You can override with env var SQLITE_PATH.
SQLITE_PATH = os.getenv("SQLITE_PATH", DB_PATH).strip()
# DEBUG: ensure default path is used when env var is not set
# print("[DEBUG] SQLITE_PATH=", SQLITE_PATH)


if not os.path.isabs(SQLITE_PATH):

    SQLITE_PATH = os.path.join(BASE_DIR, SQLITE_PATH)


DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "clinic123")
DEMO_USERS = (
    ("Clinic", "Admin", "Clinic Admin", "admin@example.com", "admin", "General Medicine"),
    ("Patient", "User", "Patient User", "user@example.com", "user", ""),
)
DEMO_LOGIN_PASSWORDS = {
    "admin@example.com": {DEMO_PASSWORD, "admin123"},
    "user@example.com": {DEMO_PASSWORD, "user123"},
}


def get_db():
    if "db" not in g:
        conn = sqlite3.connect(SQLITE_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db:
        db.close()


def init_db():
    """Create required tables if they don't exist."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT,
            last_name TEXT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            doctor_specialization TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            staff_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            status TEXT NOT NULL,
            checkup_type TEXT NOT NULL DEFAULT 'Overall Check-up',
            checkup_notes TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (staff_id) REFERENCES users(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS transaction_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            entity TEXT NOT NULL,
            entity_id INTEGER,
            details TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    ensure_column(cursor, "users", "first_name", "TEXT")
    ensure_column(cursor, "users", "last_name", "TEXT")
    ensure_column(cursor, "users", "doctor_specialization", "TEXT")
    ensure_column(cursor, "users", "created_at", "TEXT")
    ensure_column(cursor, "users", "updated_at", "TEXT")
    ensure_column(cursor, "appointments", "checkup_type", "TEXT DEFAULT 'Overall Check-up'")
    ensure_column(cursor, "appointments", "checkup_notes", "TEXT")
    ensure_column(cursor, "appointments", "created_at", "TEXT")
    ensure_column(cursor, "appointments", "updated_at", "TEXT")
    cursor.execute(
        """
        UPDATE users
        SET first_name = CASE
                WHEN INSTR(name, ' ') > 0 THEN SUBSTR(name, 1, INSTR(name, ' ') - 1)
                ELSE name
            END
        WHERE first_name IS NULL OR first_name = ''
        """
    )
    cursor.execute(
        """
        UPDATE users
        SET last_name = CASE
                WHEN INSTR(name, ' ') > 0 THEN SUBSTR(name, INSTR(name, ' ') + 1)
                ELSE ''
            END
        WHERE last_name IS NULL
        """
    )
    cursor.execute("UPDATE users SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    cursor.execute("UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")
    cursor.execute("UPDATE appointments SET checkup_type = 'Overall Check-up' WHERE checkup_type IS NULL OR checkup_type = ''")
    cursor.execute("UPDATE appointments SET created_at = CURRENT_TIMESTAMP WHERE created_at IS NULL")
    cursor.execute("UPDATE appointments SET updated_at = CURRENT_TIMESTAMP WHERE updated_at IS NULL")

    seed_demo_users(cursor)
    conn.commit()
    cursor.close()


def ensure_column(cursor, table, column, definition):
    cursor.execute(f"PRAGMA table_info({table})")
    columns = [row["name"] for row in cursor.fetchall()]
    if column not in columns:
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def seed_demo_users(cursor):
    """Keep the documented demo accounts available for local login."""
    for first_name, last_name, name, email, role, specialization in DEMO_USERS:
        cursor.execute(
            """
            SELECT id, password, first_name, last_name, name, role, doctor_specialization
            FROM users
            WHERE LOWER(email) = :email
            """,
            {"email": email},
        )
        user = cursor.fetchone()

        if user is None:
            cursor.execute(
                """
                INSERT INTO users (first_name, last_name, name, email, password, role, doctor_specialization)
                VALUES (:first_name, :last_name, :name, :email, :password, :role, :doctor_specialization)
                """,
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "name": name,
                    "email": email,
                    "password": generate_password_hash(DEMO_PASSWORD),
                    "role": role,
                    "doctor_specialization": specialization,
                },
            )
            continue

        needs_password = not check_password_hash(user["password"], DEMO_PASSWORD)
        needs_profile = (
            (user["first_name"] or "") != first_name
            or (user["last_name"] or "") != last_name
            or
            user["name"] != name
            or user["role"] != role
            or (user["doctor_specialization"] or "") != specialization
        )

        if needs_password or needs_profile:
            cursor.execute(
                """
                UPDATE users
                SET first_name = :first_name,
                    last_name = :last_name,
                    name = :name,
                    password = :password,
                    role = :role,
                    doctor_specialization = :doctor_specialization,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = :id
                """,
                {
                    "id": user["id"],
                    "first_name": first_name,
                    "last_name": last_name,
                    "name": name,
                    "password": generate_password_hash(DEMO_PASSWORD) if needs_password else user["password"],
                    "role": role,
                    "doctor_specialization": specialization,
                },
            )


# ========================
# QUERY HELPER
# ========================
def execute_query(sql, params=None, fetch=False):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(sql, params or {})

        if fetch:
            rows = cursor.fetchall()
            result = []
            for r in rows:
                result.append({k.lower(): r[k] for k in r.keys()})
            return result
        else:
            conn.commit()
            return True

    except Exception as e:
        conn.rollback()
        logging.exception("Database error")
        raise e

    finally:
        cursor.close()


def log_transaction(action, entity, entity_id=None, user_id=None, details=None):
    try:
        execute_query(
            """
            INSERT INTO transaction_logs (user_id, action, entity, entity_id, details)
            VALUES (:user_id, :action, :entity, :entity_id, :details)
            """,
            {
                "user_id": user_id,
                "action": action,
                "entity": entity,
                "entity_id": entity_id,
                "details": details,
            },
        )
    except Exception:
        logging.exception("Failed to write transaction log")


@app.before_request
def _ensure_db():
    # Ensure tables exist before handling requests
    init_db()


# ========================
# TOKEN SYSTEM
# ========================
VALID_TOKEN = os.getenv("AUTH_TOKEN", "admin123")


def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization")

        if not token:
            return jsonify({"error": "Token missing"}), 401

        if token.replace("Bearer ", "") != VALID_TOKEN:
            return jsonify({"error": "Invalid token"}), 403

        return f(*args, **kwargs)

    return wrapper

# ========================
# PAGES
# ========================

@app.route("/sql-dev")
def sql_dev_page():
    # Guarded by existing token system (client-side navigation only is not enough)
    # Frontend will include token; server must enforce admin.
    token = request.headers.get("Authorization", "")
    if not token.replace("Bearer ", "") or token.replace("Bearer ", "") != VALID_TOKEN:
        return jsonify({"error": "Invalid token"}), 403

    # Determine role from DB using demo emails present in localStorage is not reliable; use cookie not available.
    # So we allow only admins by checking a special header set by JS.
    # Expect frontend to send X-User-Email.
    email = request.headers.get("X-User-Email", "").strip().lower()
    if not email:
        return jsonify({"error": "Missing X-User-Email"}), 400

    rows = execute_query("SELECT role FROM users WHERE LOWER(email)=:email", {"email": email}, fetch=True)
    if not rows:
        return jsonify({"error": "User not found"}), 404
    if (rows[0].get("role") or "").lower() != 'admin':
        return jsonify({"error": "Admin only"}), 403

    return render_template("sql_developer.html")


@app.route("/api/sql-exec", methods=["POST"])
@token_required
def sql_exec():
    data = request.get_json() or {}
    query = (data.get("query") or "").strip()
    limit = data.get("limit", 200)

    if not query:
        return jsonify({"success": False, "error": "query is required"}), 400

    try:
        limit = int(limit)
    except Exception:
        limit = 200

    limit = max(1, min(2000, limit))

    # Basic read-only enforcement
    q_lower = query.lower().lstrip()
    forbidden = [
        "insert", "update", "delete", "drop", "alter", "create", "truncate",
        "replace", "merge", "grant", "revoke", "comment", "pragma journal_mode",
        "execute", "call"
    ]
    for f in forbidden:
        if f in q_lower:
            return jsonify({"success": False, "error": f"Only read-only SELECT queries are allowed"}), 400

    if not q_lower.startswith("select") and not q_lower.startswith("with"):
        return jsonify({"success": False, "error": "Only SELECT queries are allowed"}), 400

    # If query does not specify LIMIT, append it.
    q_strip = query.strip().rstrip(';')
    if ' limit ' not in q_lower:
        query = f"{q_strip} LIMIT {limit}"

    # Enforce admin (server-side) by requiring client to send X-User-Email
    email = request.headers.get("X-User-Email", "").strip().lower()
    if not email:
        return jsonify({"success": False, "error": "Missing X-User-Email"}), 400

    role_rows = execute_query("SELECT role FROM users WHERE LOWER(email)=:email", {"email": email}, fetch=True)
    if not role_rows or (role_rows[0].get("role") or "").lower() != 'admin':
        return jsonify({"success": False, "error": "Admin only"}), 403

    try:
        rows = execute_query(query, fetch=True)
        return jsonify({"success": True, "rows": rows})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 400


# ========================
# PAGES
# ========================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/auth")
def auth():
    return render_template("auth.html")

@app.route("/admin")
def admin():
    return render_template("admin_dashboard.html")

@app.route("/staff")
def staff():
    return render_template("staff_dashboard.html")

@app.route("/user")
def user():
    return render_template("user_dashboard.html")

# ========================
# HEALTH CHECK
# ========================
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True})


# ========================
# DEBUG (HELPFUL FOR RENDER ENV VAR ISSUES)
# ========================
@app.route("/debug-env", methods=["GET"])
def debug_env():
    return jsonify({
        "SQLITE_PATH": SQLITE_PATH,
    })



# ========================
# LOGIN
# ========================
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "No data sent"}), 400

    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = execute_query("""
        SELECT * FROM users 
        WHERE LOWER(email) = :email
    """, {"email": email}, fetch=True)

    if user:
        db_user = user[0]
        stored_password = db_user["password"]

        password_matches = check_password_hash(stored_password, password)
        is_demo_password = password in DEMO_LOGIN_PASSWORDS.get(email, set())

        if password_matches or is_demo_password:
            if is_demo_password and not password_matches:
                execute_query(
                    """
                    UPDATE users
                    SET password = :password,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    """,
                    {
                        "id": db_user["id"],
                        "password": generate_password_hash(password),
                    },
                )

            log_transaction("LOGIN", "users", db_user["id"], db_user["id"], "User logged in")

            return jsonify({
                "success": True,
                "token": VALID_TOKEN,
                "user": {
                    "id": db_user["id"],
                    "email": db_user["email"],
                    "first_name": db_user.get("first_name", ""),
                    "last_name": db_user.get("last_name", ""),
                    "name": db_user["name"],
                    "role": db_user["role"],
                    "doctor_specialization": db_user.get("doctor_specialization", "")
                }
            })

    return jsonify({"success": False, "message": "Invalid credentials"}), 401

# ========================
# REGISTER
# ========================
@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "No data sent"}), 400

    try:
        first_name = data.get("first_name", "").strip()
        last_name = data.get("last_name", "").strip()
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")

        if not first_name or not last_name or not email or not password:
            return jsonify({
                "success": False,
                "message": "First name, last name, email, and password are required"
            }), 400

        hashed_password = generate_password_hash(password)
        full_name = f"{first_name} {last_name}"

        # New signups should always be normal users (no role field in the form)
        # Avoid crashing on duplicate signups
        existing = execute_query(
            "SELECT id FROM users WHERE LOWER(email) = :email",
            {"email": email},
            fetch=True,
        )
        if existing:
            return jsonify({"success": False, "message": "Email already registered"}), 409

        execute_query(
            """
            INSERT INTO users (first_name, last_name, name, email, password, role, doctor_specialization)
            VALUES (:first_name, :last_name, :name, :email, :password, :role, :doctor_specialization)
            """,
            {
                "first_name": first_name,
                "last_name": last_name,
                "name": full_name,
                "email": email,
                "password": hashed_password,
                "role": "user",
                "doctor_specialization": "",
            },
        )


        created_user = execute_query(
            "SELECT id FROM users WHERE LOWER(email) = :email",
            {"email": email},
            fetch=True,
        )
        if created_user:
            log_transaction("REGISTER", "users", created_user[0]["id"], created_user[0]["id"], "User registered")

        return jsonify({"success": True, "message": "User registered"})

    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# ========================
# USERS API
# ========================
@app.route("/api/users", methods=["GET"])
@token_required
def get_users():
    users = execute_query("""
        SELECT id, first_name, last_name, name, email, role, doctor_specialization, created_at, updated_at FROM users
    """, fetch=True)

    return jsonify({"users": users})


@app.route("/api/transactions", methods=["GET"])
@token_required
def get_transactions():
    logs = execute_query("""
        SELECT
            l.id,
            l.user_id,
            u.name AS user_name,
            l.action,
            l.entity,
            l.entity_id,
            l.details,
            l.created_at
        FROM transaction_logs l
        LEFT JOIN users u ON l.user_id = u.id
        ORDER BY l.id DESC
        LIMIT 100
    """, fetch=True)

    return jsonify({"transactions": logs})

# ========================
# APPOINTMENTS
# ========================

# ✅ FIXED (NOW RETURNS NAMES)
@app.route("/api/patient-record", methods=["GET"])
@token_required
def get_patient_record():
    patient_id = request.args.get("patient_id")
    if not patient_id:
        return jsonify({"success": False, "message": "patient_id is required"}), 400

    data = execute_query(
        """
        SELECT
            a.id,
            a.user_id,
            u.name AS user_name,
            a.staff_id,
            s.name AS staff_name,
            s.doctor_specialization AS doctor_specialization,
            a.appointment_date,
            a.appointment_time,
            a.status,
            a.checkup_type,
            a.checkup_notes,
            a.created_at,
            a.updated_at
        FROM appointments a
        LEFT JOIN users u ON a.user_id = u.id
        LEFT JOIN users s ON a.staff_id = s.id
        WHERE a.user_id = :patient_id
        ORDER BY a.id DESC
        """,
        {"patient_id": int(patient_id)},
        fetch=True,
    )

    return jsonify({"appointments": data})


@app.route("/api/appointments", methods=["GET"])
@token_required
def get_appointments():
    user_id = request.args.get("user_id")
    role = request.args.get("role")


    base_query = """
        SELECT 
            a.id,
            a.user_id,
            u.name AS user_name,
            a.staff_id,
            s.name AS staff_name,
            s.doctor_specialization AS doctor_specialization,
            a.appointment_date AS appointment_date,
            a.appointment_time,
            a.status,
            a.checkup_type,
            a.checkup_notes,
            a.created_at,
            a.updated_at
        FROM appointments a
        LEFT JOIN users u ON a.user_id = u.id
        LEFT JOIN users s ON a.staff_id = s.id
    """

    if role == "admin":
        query = base_query + " ORDER BY a.id DESC"
        data = execute_query(query, fetch=True)

    elif role == "staff":
        query = base_query + " WHERE a.staff_id = :user_id ORDER BY a.id DESC"
        data = execute_query(query, {"user_id": user_id}, fetch=True)

    else:
        query = base_query + " WHERE a.user_id = :user_id ORDER BY a.id DESC"
        data = execute_query(query, {"user_id": user_id}, fetch=True)

    # frontend expects these keys:
    # id, user_id, staff_id, appointment_date, appointment_time, status
    return jsonify({"appointments": data})



@app.route("/api/appointments", methods=["POST"])
@token_required
def add_appointment():
    data = request.get_json()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO appointments
        (user_id, staff_id, appointment_date, appointment_time, status, checkup_type, checkup_notes)
        VALUES (:user_id, :staff_id, :appointment_date, :appointment_time, :status, :checkup_type, :checkup_notes)
    """, {
        "user_id": data.get("user_id"),
        "staff_id": data.get("staff_id"),
        "appointment_date": data.get("appointment_date"),
        "appointment_time": data.get("appointment_time"),
        "status": data.get("status", "Pending"),
        "checkup_type": data.get("checkup_type", "Overall Check-up"),
        "checkup_notes": data.get("checkup_notes", "")
    })
    appointment_id = cursor.lastrowid
    conn.commit()
    cursor.close()

    log_transaction(
        "CREATE",
        "appointments",
        appointment_id,
        data.get("user_id"),
        f"{data.get('checkup_type', 'Overall Check-up')} appointment created for {data.get('appointment_date')} {data.get('appointment_time')}",
    )

    return jsonify({"success": True})



# ✅ UPDATE (USED BY YOUR BUTTON)
@app.route("/api/appointments/<int:id>", methods=["PUT"])
@token_required
def update_appointment(id): 
    data = request.get_json()

    execute_query("""
        UPDATE appointments
        SET status = :status,
            checkup_notes = COALESCE(:checkup_notes, checkup_notes),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = :id
    """, {
        "status": data.get("status"),
        "checkup_notes": data.get("checkup_notes"),
        "id": id
    })

    log_transaction(
        "UPDATE",
        "appointments",
        id,
        data.get("user_id"),
        f"Appointment status changed to {data.get('status')}",
    )

    return jsonify({"success": True})


# ✅ DELETE (USED BY YOUR BUTTON)
@app.route("/api/appointments/<int:id>", methods=["DELETE"])
@token_required
def delete_appointment(id):
    log_transaction(
        "DELETE_BLOCKED",
        "appointments",
        id,
        None,
        "Delete blocked because records are non-deletable",
    )
    return jsonify({
        "success": False,
        "message": "Records are non-deletable. Cancel or update the status instead."
    }), 405

# ========================
# LOGOUT
# ========================
@app.route("/api/logout", methods=["POST"])
def logout():
    return jsonify({"success": True})



# ========================
# RUN SERVER
# ========================
if __name__ == "__main__":

    port = int(os.getenv("PORT", "5000"))
    debug = app.config["DEBUG"]

    print(f"\nServer starting on http://0.0.0.0:{port}\n")

    app.run(
        host="0.0.0.0",
        port=port,
        debug=debug,
        use_reloader=False
    )

