const token = localStorage.getItem('clinicToken');

let currentUser = null;
try {
    currentUser = JSON.parse(localStorage.getItem('clinicUser') || 'null');
} catch (e) {
    currentUser = null;
}

let allAppointments = [];
let allUsers = [];
let allTransactions = [];

// ========================
// AUTH CHECK
// ========================
function requireLogin() { 
    if (!token || !currentUser || !currentUser.role) {
        window.location.href = '/auth';
        return false;
    }
    return true;
}

// Removed throw in browser-only JS to avoid breaking any tooling that attempts JS parsing.
// If token/user is missing, redirect happens inside requireLogin().
requireLogin();


// ========================
// HEADERS
// ========================
function apiHeaders() {
    return {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
    };
}

function display(value) {
    return value || "-";
}

// ========================
// FETCH WRAPPER
// ========================
async function fetchJson(url, options = {}) {
    try {
        const res = await fetch(url, options);

        if (res.status === 401 || res.status === 403) {
            logout();
            return null;
        }

        return await res.json();
    } catch (err) {
        console.error("Fetch error:", err);
        return null;
    }
}

// ========================
// LOGOUT
// ========================
function logout() {
    localStorage.removeItem('clinicToken');
    localStorage.removeItem('clinicUser');
    window.location.href = '/auth';
}

window.logout = logout;

// ========================
// RELOAD DASHBOARD
// ========================
function reloadDashboard() {
    const path = window.location.pathname;
    if (path === "/admin") loadAdminDashboard();
    if (path === "/staff") loadStaffDashboard();
    if (path === "/user") loadUserDashboard();
}

// ========================
// LOAD USERS
// ========================
async function loadUsers() {
    const res = await fetchJson('/api/users', { headers: apiHeaders() });
    allUsers = res?.users || [];

    const userSelect = document.getElementById("appointment-user");
    const staffSelect = document.getElementById("appointment-staff");
    const patientRecordSelect = document.getElementById('patient-record-patient');

    if (userSelect) {
        userSelect.innerHTML = allUsers
            .filter(u => u.role === "user")
            .map(u => `<option value="${u.id}">${u.name} (${u.email})</option>`)
            .join('');
    }

    if (patientRecordSelect) {
        patientRecordSelect.innerHTML = `
            <option value="">-- Select Patient --</option>
            ${allUsers
                .filter(u => u.role === "user")
                .map(u => `<option value="${u.id}">${u.name} (${u.email})</option>`)
                .join('')}
        `;
    }

    if (staffSelect) {
        staffSelect.innerHTML = allUsers
            .filter(u => u.role === "admin" || u.role === "staff")
            .map(u => {
                const specialization = u.doctor_specialization ? ` - ${u.doctor_specialization}` : "";
                return `<option value="${u.id}">${u.name}${specialization} (${u.email})</option>`;
            })
            .join('');
    }

    renderUsers();
}


// ========================
// RENDER USERS
// ========================
function renderUsers() {
    const container = document.getElementById('user-list');
    if (!container) return;

    container.innerHTML = `
        <table>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>First Name</th>
                <th>Last Name</th>
                <th>Email</th>
                <th>Role</th>
                <th>Doctor Specialization</th>
                <th>Created</th>
                <th>Updated</th>
            </tr>
            ${allUsers.map(u => `
                <tr>
                    <td>${u.id}</td>
                    <td>${u.name}</td>
                    <td>${display(u.first_name)}</td>
                    <td>${display(u.last_name)}</td>
                    <td>${u.email}</td>
                    <td>${u.role}</td>
                    <td>${display(u.doctor_specialization)}</td>
                    <td>${display(u.created_at)}</td>
                    <td>${display(u.updated_at)}</td>
                </tr>
            `).join('')}
        </table>
    `;
}

// ========================
// CREATE APPOINTMENT
// ========================
document.addEventListener("DOMContentLoaded", function () {

    const form = document.getElementById("appointment-form");
    const msg = document.getElementById("admin-message") || document.getElementById("user-message");

    function showMessage(text, type = "error") {
        if (!msg) return;
        msg.textContent = text;
        msg.className = `message ${type}`;
    }

    if (form) {
        form.addEventListener("submit", async function (e) {
            e.preventDefault();

            const user_id = document.getElementById("appointment-user")?.value || currentUser.id;
            const staff_id = document.getElementById("appointment-staff")?.value;
            const date = document.getElementById("appointment-date")?.value;
            const time = document.getElementById("appointment-time")?.value;
            const status = document.getElementById("appointment-status")?.value || "Pending";
            const checkup_type = document.getElementById("checkup-type")?.value || "Overall Check-up";
            const checkup_notes = document.getElementById("checkup-notes")?.value || "";

            if (!staff_id || !date || !time) {
                showMessage("Please fill all fields.");
                return;
            }

            try {
                const res = await fetch("/api/appointments", {
                    method: "POST",
                    headers: apiHeaders(),
                    body: JSON.stringify({
                        user_id: parseInt(user_id),
                        staff_id: parseInt(staff_id),
                        appointment_date: date,
                        appointment_time: time,
                        status,
                        checkup_type,
                        checkup_notes
                    })
                });

                const result = await res.json();

                if (res.ok) {
                    showMessage("Appointment created successfully!", "success");
                    form.reset();
                    reloadDashboard();
                } else {
                    showMessage(result.error || "Failed to create appointment");
                }

            } catch (err) {
                console.error(err);
                showMessage("Server error");
            }
        });
    }

    const logoutBtn = document.getElementById("logout-button");
    if (logoutBtn) logoutBtn.addEventListener("click", logout);
});

// ========================
// STATUS COLORS
// ========================
function statusClass(status) {
    switch ((status || "").toLowerCase()) {
        case "pending": return "status-yellow";
        case "confirmed": return "status-blue";
        case "completed": return "status-green";
        case "cancelled": return "status-red";
        default: return "";
    }
}

// ========================
// UPDATE STATUS
// ========================
async function updateStatus(id, status) {
    await fetchJson(`/api/appointments/${id}`, {
        method: "PUT",
        headers: apiHeaders(),
        body: JSON.stringify({ status, user_id: currentUser.id })
    });

    reloadDashboard();
}

// ========================
// ACTION BUTTONS (FIXED)
// ========================
function actionButtons(a) {
    if (!currentUser || !currentUser.role) return "";

    let html = "";
    const role = currentUser.role.toLowerCase();

    if (role === "staff") {
        if (a.status !== "Completed") {
            html += `<button onclick="updateStatus(${a.id}, 'Completed')">Mark Done</button>`;
        }
    }

    if (role === "admin") {
        html += `
            <button onclick="updateStatus(${a.id}, 'Confirmed')">Confirm</button>
            <button onclick="updateStatus(${a.id}, 'Completed')">Done</button>
            <button onclick="updateStatus(${a.id}, 'Cancelled')">Cancel</button>
        `;
    }

    return html;
}

// ========================
// RENDER APPOINTMENTS
// ========================
function renderAppointments(data) {
    const container = document.getElementById('appointment-list');
    if (!container) return;

    if (!Array.isArray(data)) data = [];

    allAppointments = data;

    container.innerHTML = `
        <input type="text" id="searchBox" placeholder="Search..." 
            onkeyup="filterAppointments()" 
            style="margin-bottom:10px;padding:8px;width:100%;" />

        <table>
            <tr>
                <th>ID</th>
                <th>User</th>
                <th>Patient Name</th>
                <th>Doctor</th>
                <th>Specialization</th>
                <th>Check-up</th>
                <th>Notes</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
                <th>Created</th>
                <th>Updated</th>
                <th>Actions</th>
            </tr>
            ${data.map(a => `
                <tr>
                    <td>${a.id}</td>
                    <td>${a.user_id}</td>
                    <td>${display(a.user_name)}</td>
                    <td>${display(a.staff_name)}</td>
                    <td>${display(a.doctor_specialization)}</td>
                    <td>${display(a.checkup_type)}</td>
                    <td>${display(a.checkup_notes)}</td>
                    <td>${display(a.appointment_date)}</td>
                    <td>${display(a.appointment_time)}</td>
                    <td class="${statusClass(a.status)}">${a.status}</td>
                    <td>${display(a.created_at)}</td>
                    <td>${display(a.updated_at)}</td>
                    <td>${actionButtons(a)}</td>
                </tr>
            `).join('')}
        </table>
    `;
}

// ========================
// SEARCH
// ========================
window.filterAppointments = function () {
    const box = document.getElementById("searchBox");
    if (!box) return;

    const value = box.value.toLowerCase();

    const filtered = allAppointments.filter(a =>
        String(a.id || "").includes(value) ||
        String(a.user_id || "").includes(value) ||
        (a.user_name || "").toLowerCase().includes(value) ||
        (a.staff_name || "").toLowerCase().includes(value) ||
        (a.doctor_specialization || "").toLowerCase().includes(value) ||
        (a.checkup_type || "").toLowerCase().includes(value) ||
        (a.checkup_notes || "").toLowerCase().includes(value) ||
        (a.status || "").toLowerCase().includes(value)
    );

    renderAppointments(filtered);
};

// ========================
// TRANSACTION LOGS
// ========================
function renderTransactions(data) {
    const container = document.getElementById('transaction-list');
    if (!container) return;

    if (!Array.isArray(data)) data = [];
    allTransactions = data;

    container.innerHTML = `
        <table>
            <tr>
                <th>ID</th>
                <th>Time Stamp</th>
                <th>User</th>
                <th>Action</th>
                <th>Entity</th>
                <th>Entity ID</th>
                <th>Details</th>
            </tr>
            ${data.map(t => `
                <tr>
                    <td>${t.id}</td>
                    <td>${display(t.created_at)}</td>
                    <td>${display(t.user_name || t.user_id)}</td>
                    <td>${display(t.action)}</td>
                    <td>${display(t.entity)}</td>
                    <td>${display(t.entity_id)}</td>
                    <td>${display(t.details)}</td>
                </tr>
            `).join('')}
        </table>
    `;
}

async function loadTransactions() {
    const res = await fetchJson('/api/transactions', {
        headers: apiHeaders()
    });

    renderTransactions(res?.transactions || []);
}

// ========================
// DASHBOARD LOADERS
// ========================
async function loadAdminDashboard() {
    const res = await fetchJson(`/api/appointments?role=admin&user_id=${currentUser.id}`, {
        headers: apiHeaders()
    });

    renderAppointments(res?.appointments || []);
    await loadUsers();
    await loadTransactions();

    // Patient record UI
    const patientSelect = document.getElementById('patient-record-patient');
    if (patientSelect) {
        patientSelect.addEventListener('change', async () => {
            const patientId = patientSelect.value;
            const container = document.getElementById('patient-record-list');
            if (!container) return;

            if (!patientId) {
                container.innerHTML = '';
                return;
            }

            const recordRes = await fetchJson(`/api/patient-record?patient_id=${patientId}`, {
                headers: apiHeaders()
            });

            const appointments = recordRes?.appointments || [];

            container.innerHTML = `
                <table>
                    <tr>
                        <th>Appointment ID</th>
                        <th>Date</th>
                        <th>Time</th>
                        <th>Doctor</th>
                        <th>Specialization</th>
                        <th>Check-up</th>
                        <th>Notes</th>
                        <th>Status</th>
                        <th>Created</th>
                        <th>Updated</th>
                    </tr>
                    ${appointments.map(a => `
                        <tr>
                            <td>${a.id}</td>
                            <td>${display(a.appointment_date)}</td>
                            <td>${display(a.appointment_time)}</td>
                            <td>${display(a.staff_name)}</td>
                            <td>${display(a.doctor_specialization)}</td>
                            <td>${display(a.checkup_type)}</td>
                            <td>${display(a.checkup_notes)}</td>
                            <td class="${statusClass(a.status)}">${display(a.status)}</td>
                            <td>${display(a.created_at)}</td>
                            <td>${display(a.updated_at)}</td>
                        </tr>
                    `).join('')}
                </table>
            `;
        });
    }
}


async function loadStaffDashboard() {
    const res = await fetchJson(`/api/appointments?role=staff&user_id=${currentUser.id}`, {
        headers: apiHeaders()
    });

    renderAppointments(res?.appointments || []);
}

async function loadUserDashboard() {
    const res = await fetchJson(`/api/appointments?role=user&user_id=${currentUser.id}`, {
        headers: apiHeaders()
    });

    renderAppointments(res?.appointments || []);
    await loadUsers();
}

// ========================
// INIT
// ========================
function init() {
    const path = window.location.pathname;

    if (path === "/admin") loadAdminDashboard();
    if (path === "/staff") loadStaffDashboard();
    if (path === "/user") loadUserDashboard();
}

init();

// ========================
// GLOBALS
// ========================
window.logout = logout;
window.updateStatus = updateStatus;
