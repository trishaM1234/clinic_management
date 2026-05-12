import logging
import os
from flask import Flask, request, jsonify, g, render_template
from functools import wraps
import oracledb
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
# ORACLE CONFIG
# ========================
ORACLE_USER = os.getenv("ORACLE_USER")
ORACLE_PASSWORD = os.getenv("ORACLE_PASSWORD")
ORACLE_DSN = os.getenv("ORACLE_DSN", "").strip()
ORACLE_HOST = os.getenv("ORACLE_HOST", "").strip()
ORACLE_PORT = os.getenv("ORACLE_PORT", "1521").strip()
ORACLE_SERVICE_NAME = os.getenv("ORACLE_SERVICE_NAME", "").strip()


def get_oracle_dsn():
    if ORACLE_HOST and ORACLE_SERVICE_NAME:
        return f"{ORACLE_HOST}:{ORACLE_PORT}/{ORACLE_SERVICE_NAME}"

    if not ORACLE_DSN:
        return ""

    is_connect_descriptor = ORACLE_DSN.startswith("(")
    is_easy_connect = "/" in ORACLE_DSN or ":" in ORACLE_DSN

    if not is_connect_descriptor and not is_easy_connect:
        raise RuntimeError(
            "ORACLE_DSN must be a full Easy Connect string like "
            "'host:1521/XE', not just an alias like 'XE'. "
            "On Render, set ORACLE_HOST, ORACLE_PORT, and "
            "ORACLE_SERVICE_NAME instead."
        )

    return ORACLE_DSN

# ========================
# DB CONNECTION
# ========================
def get_db():
    oracle_dsn = get_oracle_dsn()
    missing_config = [
        name for name, value in {
            "ORACLE_USER": ORACLE_USER,
            "ORACLE_PASSWORD": ORACLE_PASSWORD,
            "ORACLE_DSN or ORACLE_HOST + ORACLE_SERVICE_NAME": oracle_dsn,
        }.items()
        if not value
    ]

    if missing_config:
        raise RuntimeError(
            "Missing required database configuration: "
            + ", ".join(missing_config)
        )

    if 'db' not in g:
        g.db = oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=oracle_dsn
        )
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db:
        db.close()

# ========================
# QUERY HELPER
# ========================
def execute_query(sql, params=None, fetch=False):
    conn = get_db()
    cursor = conn.cursor()

    try:
        cursor.execute(sql, params or {})

        if fetch:
            columns = [col[0].lower() for col in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
        else:
            conn.commit()
            return True

    except Exception as e:
        conn.rollback()
        logging.exception("Database error")
        raise e

    finally:
        cursor.close()

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

        if check_password_hash(stored_password, password):
            return jsonify({
                "success": True,
                "token": VALID_TOKEN,
                "user": {
                    "id": db_user["id"],
                    "name": db_user["name"],
                    "role": db_user["role"]
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
        hashed_password = generate_password_hash(data["password"])

        execute_query("""
            INSERT INTO users (name, email, password, role)
            VALUES (:name, :email, :password, :role)
        """, {
            "name": data["name"],
            "email": data["email"].strip().lower(),
            "password": hashed_password,
            "role": data["role"]
        })

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
        SELECT id, name, email, role FROM users
    """, fetch=True)

    return jsonify({"users": users})

# ========================
# APPOINTMENTS
# ========================

# ✅ FIXED (NOW RETURNS NAMES)
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
            TO_CHAR(a.appointment_date, 'YYYY-MM-DD') AS appointment_date,
            a.appointment_time,
            a.status
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

    return jsonify({"appointments": data})


@app.route("/api/appointments", methods=["POST"])
@token_required
def add_appointment():
    data = request.get_json()

    execute_query("""
        INSERT INTO appointments 
        (user_id, staff_id, appointment_date, appointment_time, status)
        VALUES (:user_id, :staff_id, TO_DATE(:appointment_date, 'YYYY-MM-DD'), :appointment_time, :status)
    """, {
        "user_id": data.get("user_id"),
        "staff_id": data.get("staff_id"),
        "appointment_date": data.get("appointment_date"),
        "appointment_time": data.get("appointment_time"),
        "status": data.get("status", "Pending")
    })

    return jsonify({"success": True})


# ✅ UPDATE (USED BY YOUR BUTTON)
@app.route("/api/appointments/<int:id>", methods=["PUT"])
@token_required
def update_appointment(id): 
    data = request.get_json()

    execute_query("""
        UPDATE appointments
        SET status = :status
        WHERE id = :id
    """, {
        "status": data.get("status"),
        "id": id
    })

    return jsonify({"success": True})


# ✅ DELETE (USED BY YOUR BUTTON)
@app.route("/api/appointments/<int:id>", methods=["DELETE"])
@token_required
def delete_appointment(id):
    execute_query(
        "DELETE FROM appointments WHERE id = :id",
        {"id": id}
    )
    return jsonify({"success": True})

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

