document.addEventListener("DOMContentLoaded", function () {

    // ========================
    // ELEMENTS
    // ========================
    const loginTab = document.getElementById('login-tab');
    const registerTab = document.getElementById('register-tab');
    const loginForm = document.getElementById('login-form');
    const registerForm = document.getElementById('register-form');
    const messageContainer = document.getElementById('message');

    if (!loginTab || !registerTab || !loginForm || !registerForm || !messageContainer) {
        console.error("❌ Missing HTML elements. Check IDs in auth.html");
        return;
    }

    // ========================
    // MESSAGE SYSTEM
    // ========================
    function showMessage(text, type = 'error') {
        messageContainer.textContent = text;
        messageContainer.className = `message ${type}`;
    }

    function clearMessage() {
        messageContainer.textContent = '';
        messageContainer.className = 'message';
    }

    // ========================
    // TAB SWITCH
    // ========================
    function switchTab(tab) {
        const isLogin = tab === 'login';

        loginTab.classList.toggle('active', isLogin);
        registerTab.classList.toggle('active', !isLogin);

        loginForm.classList.toggle('active', isLogin);
        registerForm.classList.toggle('active', !isLogin);

        clearMessage();
    }

    loginTab.addEventListener('click', () => switchTab('login'));
    registerTab.addEventListener('click', () => switchTab('register'));

    // ========================
    // LOGIN
    // ========================
    async function handleLogin(e) {
        e.preventDefault();
        clearMessage();

        const email = document.getElementById('login-email').value.trim();
        const password = document.getElementById('login-password').value;

        if (!email || !password) {
            showMessage("Email and password are required.");
            return;
        }

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ email, password })
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                showMessage(result.message || "Invalid credentials");
                return;
            }

            // SAVE SESSION
            localStorage.setItem("clinicToken", result.token);
            localStorage.setItem("clinicUser", JSON.stringify(result.user));

            loginForm.reset();
            showMessage("Login successful!", "success");

            // REDIRECT BASED ON ROLE
            setTimeout(() => {
                const role = result.user.role;

                if (role === "admin") {
                    window.location.href = "/admin";
                } else if (role === "staff") {
                    window.location.href = "/staff";
                } else {
                    window.location.href = "/user";
                }
            }, 500);

        } catch (err) {
            console.error(err);
            showMessage("Server not reachable.");
        }
    }

    // ========================
    // REGISTER
    // ========================
    async function handleRegister(e) {
        e.preventDefault();
        clearMessage();

        const name = document.getElementById('register-name').value.trim();
        const email = document.getElementById('register-email').value.trim();
        const password = document.getElementById('register-password').value;
        const role = document.getElementById('register-role').value;

        if (!name || !email || !password) {
            showMessage("Please fill all fields.");
            return;
        }

        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ name, email, password, role })
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                showMessage(result.message || "Registration failed");
                return;
            }

            showMessage("Account created! You can now log in.", "success");
            registerForm.reset();

            setTimeout(() => switchTab('login'), 800);

        } catch (err) {
            console.error(err);
            showMessage("Server not reachable.");
        }
    }

    // ========================
    // EVENTS
    // ========================
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);

    // ========================
    // AUTO LOGIN REDIRECT
    // ========================
    const savedUser = localStorage.getItem("clinicUser");

    if (savedUser && window.location.pathname.includes("/auth")) {
        try {
            const user = JSON.parse(savedUser);

            setTimeout(() => {
                if (user.role === "admin") {
                    window.location.href = "/admin";
                } else if (user.role === "staff") {
                    window.location.href = "/staff";
                } else {
                    window.location.href = "/user";
                }
            }, 300);

        } catch (err) {
            localStorage.removeItem("clinicUser");
            localStorage.removeItem("clinicToken");
        }
    }

});