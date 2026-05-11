const token = localStorage.getItem('clinicToken');

let currentUser = null;
try {
    currentUser = JSON.parse(localStorage.getItem('clinicUser') || 'null');
} catch (e) {
    currentUser = null;
}

let allAppointments = [];
let allUsers = [];

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

if (!requireLogin()) {
    throw new Error("Not logged in");
}

// ========================
// HEADERS
// ========================
function apiHeaders() {
    return {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`
    };
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

// ========================
// LOAD USERS (FIXED)
// ========================
async function loadUsers() {
    const res = await fetchJson('/api/users', { headers: apiHeaders() });

    // ✅ FIX HERE
    allUsers = res || [];

    const userSelect = document.getElementById("appointment-user");
    const staffSelect = document.getElementById("appointment-staff");

    if (userSelect) {
        userSelect.innerHTML = allUsers
            .filter(u => u.role === "user")
            .map(u => `<option value="${u.id}">${u.name} (${u.email})</option>`)
            .join('');
    }

    if (staffSelect) {
        staffSelect.innerHTML = allUsers
            .filter(u => u.role === "staff")
            .map(u => `<option value="${u.id}">${u.name} (${u.email})</option>`)
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
                <th>Email</th>
                <th>Role</th>
            </tr>
            ${allUsers.map(u => `
                <tr>
                    <td>${u.id}</td>
                    <td>${u.name}</td>
                    <td>${u.email}</td>
                    <td>${u.role}</td>
                </tr>
            `).join('')}
        </table>
    `;
}

// ========================
// LOAD APPOINTMENTS (FIXED)
// ========================
async function loadAppointments() {
    const res = await fetchJson('/api/appointments', {
        headers: apiHeaders()
    });

    // ✅ FIX HERE
    allAppointments = res || [];
    renderAppointments(allAppointments);
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
            const status = "Pending";

            if (!staff_id || !date || !time) {
                showMessage("Please fill all fields.");
                return;
            }

            const res = await fetch("/api/appointments", {
                method: "POST",
                headers: apiHeaders(),
                body: JSON.stringify({
                    user_id: parseInt(user_id),
                    staff_id: parseInt(staff_id),
                    appointment_date: date,
                    appointment_time: time,
                    status
                })
            });

            if (res.ok) {
                showMessage("Appointment created!", "success");
                form.reset();
                loadAppointments();
            } else {
                showMessage("Failed to create appointment");
            }
        });
    }

    const logoutBtn = document.getElementById("logout-button");
    if (logoutBtn) logoutBtn.addEventListener("click", logout);

    // INIT LOAD
    loadAppointments();
    loadUsers();
});

// ========================
// RENDER APPOINTMENTS
// ========================
function renderAppointments(data) {
    const container = document.getElementById('appointment-list');
    if (!container) return;

    container.innerHTML = `
        <table>
            <tr>
                <th>ID</th>
                <th>User</th>
                <th>Staff</th>
                <th>Date</th>
                <th>Time</th>
                <th>Status</th>
            </tr>
            ${data.map(a => `
                <tr>
                    <td>${a.id}</td>
                    <td>${a.user_id}</td>
                    <td>${a.staff_id}</td>
                    <td>${a.appointment_date}</td>
                    <td>${a.appointment_time}</td>
                    <td>${a.status}</td>
                </tr>
            `).join('')}
        </table>
    `;
}

// ========================
// GLOBAL
// ========================
window.logout = logout;