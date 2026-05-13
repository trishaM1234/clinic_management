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
    // TAB SWITCHING
    // ========================
    function switchTab(tab) {
        if (tab === 'login') {
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
            loginForm.classList.add('active');
            registerForm.classList.remove('active');
        } else {
            loginTab.classList.remove('active');
            registerTab.classList.add('active');
            loginForm.classList.remove('active');
            registerForm.classList.add('active');
        }

        clearMessage();
    }

    loginTab.addEventListener('click', () => switchTab('login'));
    registerTab.addEventListener('click', () => switchTab('register'));

    // ========================
    // LOGIN FUNCTION
    // ========================
    async function handleLogin(event) {
        event.preventDefault();
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
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({ email, password })
            });

            const result = await response.json();

            if (!result.success) {
                showMessage(result.message || "Invalid credentials");
                return;
            }

            // STORE AUTH DATA
            localStorage.setItem('clinicToken', result.token);
            localStorage.setItem('clinicUser', JSON.stringify(result.user));

            loginForm.reset();

            showMessage("Login successful!", "success");

            // REDIRECT
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

        } catch (error) {
            console.error(error);
            showMessage("Unable to connect to server.");
        }
    }

    // ========================
    // REGISTER FUNCTION
    // ========================
    async function handleRegister(event) {
        event.preventDefault();
        clearMessage();

        const name = document.getElementById('register-name').value.trim();
        const email = document.getElementById('register-email').value.trim();
        const password = document.getElementById('register-password').value;

        if (!name || !email || !password) {
            showMessage("Please complete all fields.");
            return;
        }

        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },

                body: JSON.stringify({
                    name,
                    email,
                    password
                })

            });

            const result = await response.json();

            if (!result.success) {
                showMessage(result.message || "Registration failed");
                return;
            }

            showMessage("Registration successful! Please login.", "success");

            registerForm.reset();

            setTimeout(() => switchTab('login'), 800);

        } catch (error) {
            console.error(error);
            showMessage("Unable to connect to server.");
        }
    }

    // ========================
    // EVENT LISTENERS
    // ========================
    loginForm.addEventListener('submit', handleLogin);
    registerForm.addEventListener('submit', handleRegister);

    // ========================
    // AUTO LOGIN REDIRECT
    // ========================
    const savedUser = localStorage.getItem("clinicUser");

    if (savedUser && window.location.pathname === "/auth") {
        try {
            const user = JSON.parse(savedUser);

            setTimeout(() => {
                const role = user.role;

                if (role === "admin") {
                    window.location.href = "/admin";
                } else if (role === "staff") {
                    window.location.href = "/staff";
                } else {
                    window.location.href = "/user";
                }
            }, 300);

        } catch (e) {
            console.warn("Invalid stored user, clearing...");
            localStorage.removeItem("clinicUser");
            localStorage.removeItem("clinicToken");
        }
    }

});