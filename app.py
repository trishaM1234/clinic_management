import oracledb
import logging
from flask import Flask, request, jsonify, g, render_template
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps

# ========================
# APP CONFIG
# ========================
app = Flask(__name__)
app.config['DEBUG'] = True
logging.basicConfig(level=logging.INFO)

print("\n🚀 Clinic System Starting (ORACLE XE MODE)...\n")

# ========================
# ORACLE XE CONFIG
# ========================
ORACLE_USER = "system"
ORACLE_PASSWORD = "111225"
ORACLE_DSN = "localhost:1521/XE"
ORACLE_SCHEMA = "SYSTEM"

# ========================
# DB CONNECTION
# ========================
def get_db():
    if 'db' not in g:
        print("🔌 Connecting to Oracle XE...")

        conn = oracledb.connect(
            user=ORACLE_USER,
            password=ORACLE_PASSWORD,
            dsn=ORACLE_DSN
        )

        # ensure correct schema
        with conn.cursor() as cur:
            cur.execute(f"ALTER SESSION SET CURRENT_SCHEMA = {ORACLE_SCHEMA}")

        g.db = conn
        print("✅ Connected to Oracle XE")

    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop('db', None)
    if db:
        db.close()
        print("🔌 DB closed")


# ========================
# QUERY HELPER
# ========================
def execute_query(sql, params=None, fetch=False):
    conn = get_db()
    cursor = conn.cursor()

    try:
        print("\n📌 SQL:")
        print(sql)
        print("📦 Params:", params)

        cursor.execute(sql, params or {})

        if fetch:
            columns = [c[0].lower() for c in cursor.description]
            rows = cursor.fetchall()
            result = [dict(zip(columns, row)) for row in rows]
            print("📊 RESULT:", result)
            return result

        conn.commit()
        print("✅ QUERY OK")
        return True

    except Exception as e:
        conn.rollback()
        print("❌ SQL ERROR:", e)
        raise e

    finally:
        cursor.close()


# ========================
# TOKEN SYSTEM
# ========================
VALID_TOKEN = "admin123"

def token_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization", "")

        if not token or token.replace("Bearer ", "") != VALID_TOKEN:
            return jsonify({"error": "Unauthorized"}), 403

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
def admin_dashboard():
    return render_template("admin_dashboard.html")

@app.route("/staff")
def staff_dashboard():
    return render_template("staff_dashboard.html")

@app.route("/user")
def user_dashboard():
    return render_template("user_dashboard.html")


# ========================
# LOGIN
# ========================
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data:
        return jsonify({"success": False, "message": "No data"}), 400

    email = data.get("email", "").lower()
    password = data.get("password", "")

    user = execute_query("""
        SELECT id, name, email, password, role
        FROM users
        WHERE LOWER(email) = :email
    """, {"email": email}, fetch=True)

    if user:
        db_user = user[0]

        if check_password_hash(db_user["password"], password):
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

    hashed = generate_password_hash(data["password"])

    execute_query("""
        INSERT INTO users (name, email, password, role)
        VALUES (:name, :email, :password, :role)
    """, {
        "name": data["name"],
        "email": data["email"].lower(),
        "password": hashed,
        "role": data["role"]
    })

    return jsonify({"success": True})


# ========================
# USERS
# ========================
@app.route("/api/users")
@token_required
def users():
    data = execute_query(
        "SELECT id, name, email, role FROM users",
        fetch=True
    )
    return jsonify(data)


# ========================
# APPOINTMENTS
# ========================
@app.route("/api/appointments")
@token_required
def get_appointments():
    data = execute_query(
        "SELECT * FROM appointments ORDER BY id DESC",
        fetch=True
    )
    return jsonify(data)


@app.route("/api/appointments", methods=["POST"])
@token_required
def add_appointment():
    data = request.get_json()

    execute_query("""
        INSERT INTO appointments
        (user_id, staff_id, appointment_date, appointment_time, status)
        VALUES
        (:user_id, :staff_id,
         TO_DATE(:appointment_date, 'YYYY-MM-DD'),
         :appointment_time,
         :status)
    """, {
        "user_id": data["user_id"],
        "staff_id": data["staff_id"],
        "appointment_date": data["appointment_date"],
        "appointment_time": data["appointment_time"],
        "status": data.get("status", "Pending")
    })

    return jsonify({"success": True})


@app.route("/api/appointments/<int:id>", methods=["PUT"])
@token_required
def update_appointment(id):
    data = request.get_json()

    execute_query("""
        UPDATE appointments
        SET status = :status
        WHERE id = :id
    """, {
        "status": data["status"],
        "id": id
    })

    return jsonify({"success": True})


@app.route("/api/appointments/<int:id>", methods=["DELETE"])
@token_required
def delete_appointment(id):
    execute_query("""
        DELETE FROM appointments WHERE id = :id
    """, {"id": id})

    return jsonify({"success": True})


# ========================
# RUN SERVER
# ========================
if __name__ == "__main__":
    print("\n🚀 SERVER RUNNING ON http://localhost:5000\n")
    app.run(debug=True, port=5000)