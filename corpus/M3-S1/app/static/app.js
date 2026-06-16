const API_URL = "http://127.0.0.1:8000/api";

// --- Utilitaires ---
function showMessage(msg, isError = false) {
    const box = document.getElementById("messageBox");
    if (!box) return;
    box.textContent = msg;
    box.className = `msg ${isError ? 'msg-error' : 'msg-success'}`;
    setTimeout(() => box.className = "hidden", 5000);
}

function getAuthHeaders() {
    const token = localStorage.getItem("token");
    return {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${token}`
    };
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "/";
}

// --- Auth (Index) ---
const loginForm = document.getElementById("loginForm");
if (loginForm) {
    loginForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const params = new URLSearchParams();
        params.append('username', document.getElementById("loginUsername").value);
        params.append('password', document.getElementById("loginPassword").value);

        try {
            const res = await fetch(`${API_URL}/auth/token`, {
                method: "POST",
                headers: { "Content-Type": "application/x-www-form-urlencoded" },
                body: params
            });
            const data = await res.json();
            if (res.ok) {
                localStorage.setItem("token", data.access_token);
                window.location.href = "/dashboard";
            } else {
                showMessage(data.detail || "Erreur de connexion", true);
            }
        } catch (err) {
            showMessage("Erreur serveur", true);
        }
    });
}

const registerForm = document.getElementById("registerForm");
if (registerForm) {
    registerForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            username: document.getElementById("regUsername").value,
            email: document.getElementById("regEmail").value,
            password: document.getElementById("regPassword").value
        };

        try {
            const res = await fetch(`${API_URL}/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (res.ok) {
                showMessage("Inscription réussie ! Vous pouvez vous connecter.");
                registerForm.reset();
            } else {
                showMessage(data.detail || "Erreur d'inscription", true);
            }
        } catch (err) {
            showMessage("Erreur serveur", true);
        }
    });
}

// --- Dashboard ---
let currentUser = null;

async function loadMyProfile() {
    try {
        const res = await fetch(`${API_URL}/users/me`, { headers: getAuthHeaders() });
        if (res.status === 401) return logout();
        
        currentUser = await res.json();
        document.getElementById("navUsername").textContent = currentUser.username;
        document.getElementById("profUsername").value = currentUser.username;
        document.getElementById("profEmail").value = currentUser.email;

        if (currentUser.is_admin) {
            document.getElementById("adminActionHeader").style.display = "table-cell";
        }
    } catch (err) {
        console.error(err);
    }
}

async function loadUsers() {
    try {
        const res = await fetch(`${API_URL}/users/`, { headers: getAuthHeaders() });
        const users = await res.json();
        const tbody = document.getElementById("usersTableBody");
        tbody.innerHTML = "";

        users.forEach(u => {
            let tr = document.createElement("tr");
            let adminCol = currentUser && currentUser.is_admin 
                ? `<td>${u.id !== currentUser.id ? `<button class="danger-btn" style="margin:0; padding:5px 10px;" onclick="deleteUserByAdmin(${u.id})">Supprimer</button>` : ''}</td>` 
                : '';

            tr.innerHTML = `
                <td>${u.id}</td>
                <td>${u.username}</td>
                <td>${u.email}</td>
                <td>${u.is_admin ? 'Oui' : 'Non'}</td>
                ${adminCol}
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        console.error(err);
    }
}

const profileForm = document.getElementById("profileForm");
if (profileForm) {
    profileForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const payload = {
            username: document.getElementById("profUsername").value,
            email: document.getElementById("profEmail").value
        };
        const pwd = document.getElementById("profPassword").value;
        if (pwd) payload.password = pwd;

        try {
            const res = await fetch(`${API_URL}/users/me`, {
                method: "PUT",
                headers: getAuthHeaders(),
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            if (res.ok) {
                showMessage("Profil mis à jour !");
                document.getElementById("profPassword").value = "";
                loadMyProfile();
                loadUsers();
            } else {
                showMessage(data.detail || "Erreur de mise à jour", true);
            }
        } catch (err) {
            showMessage("Erreur serveur", true);
        }
    });
}

async function deleteMyAccount() {
    if (!confirm("Voulez-vous vraiment supprimer votre compte ? Cette action est irréversible.")) return;
    try {
        const res = await fetch(`${API_URL}/users/me`, {
            method: "DELETE",
            headers: getAuthHeaders()
        });
        if (res.ok) logout();
    } catch (err) {
        showMessage("Erreur serveur", true);
    }
}

async function deleteUserByAdmin(id) {
    if (!confirm("Admin : Supprimer cet utilisateur ?")) return;
    try {
        const res = await fetch(`${API_URL}/users/${id}`, {
            method: "DELETE",
            headers: getAuthHeaders()
        });
        if (res.ok) {
            showMessage("Utilisateur supprimé.");
            loadUsers();
        } else {
            const data = await res.json();
            showMessage(data.detail || "Erreur lors de la suppression", true);
        }
    } catch (err) {
        showMessage("Erreur serveur", true);
    }
}