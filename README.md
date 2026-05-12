# Clinic Monitoring System

A beginner-friendly full-stack clinic monitoring system using:

- Frontend: HTML, CSS, JavaScript (vanilla)
- Backend: Python + Flask
- Database: Oracle APEX / Oracle Database

## Features

- Landing page with clinic overview
- Register and login flows
- Role-based dashboards for Admin, Staff, and User (Patient)
- Appointment booking, status updates, and management
- Secure password hashing and JWT authentication

## Folder Structure

```
clinic appointment/
├── app.py
├── requirements.txt
├── .env.example
├── README.md
├── templates/
│   ├── index.html
│   ├── auth.html
│   ├── admin_dashboard.html
│   ├── staff_dashboard.html
│   └── user_dashboard.html
├── static/
│   ├── css/
│   │   └── styles.css
│   └── js/
│       ├── auth.js
│       └── dashboard.js
└── sql/
    └── clinic_schema.sql
```

## Run Locally

1. Create a virtual environment and activate it.

```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and update the Oracle connection settings.

4. Create the database tables in Oracle using the SQL script in `sql/clinic_schema.sql`.

5. Start the backend server.

```bash
python app.py
```

6. Open the site in your browser:

```
http://localhost:5000
```

## Deploy on Render

This repository includes a `render.yaml` blueprint for a Render Python web service.

1. Push the project to GitHub, GitLab, or Bitbucket.
2. In Render, create a new Blueprint or Web Service from the repository.
3. Use these settings if creating the service manually:

```text
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
Health Check Path: /health
```

4. Add these environment variables in Render:

```text
FLASK_DEBUG=false
AUTH_TOKEN=<secure-random-token>
ORACLE_USER=<your-oracle-user>
ORACLE_PASSWORD=<your-oracle-password>
ORACLE_DSN=<public-or-private-oracle-host>:1521/<service-name>
```

The Oracle database must be reachable from Render. A local DSN like `localhost:1521/XE`
only works on your computer and will not work after deployment.

## Notes

- Use the register page to create users, staff, and admin accounts.
- Admin can manage all users and appointments.
- Staff can update assignment status only on their assigned appointments.
- Users can book appointments and review their history.
