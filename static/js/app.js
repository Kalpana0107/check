// Central Application Utilities & Authentication
const App = {
    TOKEN_KEY: 'autograde_token',
    USER_KEY: 'autograde_user',

    getToken() {
        return localStorage.getItem(this.TOKEN_KEY);
    },

    getUser() {
        const u = localStorage.getItem(this.USER_KEY);
        try {
            return u ? JSON.parse(u) : null;
        } catch (e) {
            return null;
        }
    },

    setSession(token, user) {
        localStorage.setItem(this.TOKEN_KEY, token);
        localStorage.setItem(this.USER_KEY, JSON.stringify(user));
    },

    logout() {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        window.location.href = '/';
    },

    authHeaders() {
        const token = this.getToken();
        return token ? { 'Authorization': `Bearer ${token}` } : {};
    },

    async apiFetch(endpoint, options = {}) {
        const url = endpoint.startsWith('http') ? endpoint : endpoint;
        const headers = {
            ...this.authHeaders(),
            ...(options.headers || {})
        };

        // Don't set Content-Type if FormData is used
        if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
        }

        try {
            const resp = await fetch(url, { ...options, headers });
            if (resp.status === 401) {
                // If unauthorized and on protected page, redirect
                if (window.location.pathname.startsWith('/teacher') || window.location.pathname.startsWith('/student')) {
                    this.logout();
                }
            }
            const data = await resp.json().catch(() => null);
            if (!resp.ok) {
                const errDetail = data?.detail || `Request failed with status ${resp.status}`;
                throw new Error(errDetail);
            }
            return data;
        } catch (err) {
            console.error('API Error:', err);
            throw err;
        }
    },

    showToast(message, type = 'info') {
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            document.body.appendChild(container);
        }

        const icons = {
            success: 'fa-solid fa-circle-check',
            error: 'fa-solid fa-circle-xmark',
            info: 'fa-solid fa-circle-info'
        };

        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <i class="${icons[type] || icons.info} text-lg"></i>
            <span class="flex-1">${message}</span>
            <button onclick="this.parentElement.remove()" class="text-slate-400 hover:text-slate-600 transition ml-2">
                <i class="fa-solid fa-xmark"></i>
            </button>
        `;
        container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(10px)';
            setTimeout(() => toast.remove(), 250);
        }, 4000);
    },

    async switchRoleDemo(role) {
        try {
            const data = await this.apiFetch(`/api/auth/demo-login/${role}`, { method: 'POST' });
            this.setSession(data.access_token, data.user);
            this.showToast(`Switched to demo ${data.user.role}: ${data.user.full_name}`, 'success');
            setTimeout(() => {
                if (role === 'teacher') {
                    window.location.href = '/teacher';
                } else {
                    window.location.href = '/student';
                }
            }, 600);
        } catch (err) {
            this.showToast(err.message || 'Demo login failed', 'error');
        }
    }
};

window.App = App;

