// Landing Page Interactions and Auth Modals

document.addEventListener('DOMContentLoaded', () => {
    initLandingAuth();
    checkSystemStatus();
    initPrototypeUploader();
});

function initLandingAuth() {
    const user = App.getUser();
    const navAuthContainer = document.getElementById('nav-auth-container');
    if (navAuthContainer && user) {
        const dest = user.role === 'teacher' ? '/teacher' : '/student';
        const roleLabel = user.role === 'teacher' ? 'Teacher' : 'Student';
        navAuthContainer.innerHTML = `
            <div class="flex items-center gap-3">
                <span class="text-xs bg-blue-100 text-blue-700 font-semibold px-2.5 py-1 rounded-full">${roleLabel}</span>
                <a href="${dest}" class="bg-blue-600 hover:bg-blue-700 text-white px-5 py-2 rounded-full font-medium transition shadow-md flex items-center gap-2">
                    <i class="fa-solid fa-arrow-right-to-bracket"></i> Dashboard
                </a>
                <button onclick="App.logout()" title="Sign Out" class="text-slate-400 hover:text-slate-700 p-2 text-sm transition">
                    <i class="fa-solid fa-right-from-bracket"></i>
                </button>
            </div>
        `;
    }
}

async function checkSystemStatus() {
    try {
        const statusEl = document.getElementById('system-status-badge');
        if (!statusEl) return;
        const res = await fetch('/api/auth/system-status');
        const data = await res.json();
        if (data.gemini_api_configured) {
            statusEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span> Gemini 2.5 Active`;
            statusEl.classList.remove('bg-blue-100', 'text-blue-700');
            statusEl.classList.add('bg-emerald-100', 'text-emerald-800');
        } else {
            statusEl.innerHTML = `<span class="w-2 h-2 rounded-full bg-blue-500"></span> Multimodal AI Engine Ready`;
        }
    } catch (e) {
        // quiet ignore
    }
}

// Modal handling
function openAuthModal(mode = 'login') {
    const modal = document.getElementById('auth-modal');
    if (!modal) return;
    modal.classList.remove('hidden');
    switchAuthTab(mode);
}

function closeAuthModal() {
    const modal = document.getElementById('auth-modal');
    if (!modal) return;
    modal.classList.add('hidden');
}

function switchAuthTab(tab) {
    const loginForm = document.getElementById('modal-login-form');
    const signupForm = document.getElementById('modal-signup-form');
    const tabLogin = document.getElementById('tab-btn-login');
    const tabSignup = document.getElementById('tab-btn-signup');

    if (tab === 'login') {
        loginForm.classList.remove('hidden');
        signupForm.classList.add('hidden');
        tabLogin.className = "flex-1 py-2 text-center font-semibold text-blue-600 border-b-2 border-blue-600 transition";
        tabSignup.className = "flex-1 py-2 text-center font-medium text-slate-500 hover:text-slate-800 transition";
    } else {
        loginForm.classList.add('hidden');
        signupForm.classList.remove('hidden');
        tabSignup.className = "flex-1 py-2 text-center font-semibold text-blue-600 border-b-2 border-blue-600 transition";
        tabLogin.className = "flex-1 py-2 text-center font-medium text-slate-500 hover:text-slate-800 transition";
    }
}

async function handleLoginSubmit(event) {
    event.preventDefault();
    const email = document.getElementById('login-email').value;
    const password = document.getElementById('login-password').value;

    try {
        const data = await App.apiFetch('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify({ email, password })
        });
        App.setSession(data.access_token, data.user);
        App.showToast(`Welcome back, ${data.user.full_name}!`, 'success');
        closeAuthModal();
        setTimeout(() => {
            window.location.href = data.user.role === 'teacher' ? '/teacher' : '/student';
        }, 500);
    } catch (err) {
        App.showToast(err.message || 'Login failed', 'error');
    }
}

async function handleSignupSubmit(event) {
    event.preventDefault();
    const fullName = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const password = document.getElementById('signup-password').value;
    const role = document.getElementById('signup-role').value;

    try {
        const data = await App.apiFetch('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                full_name: fullName,
                email: email,
                password: password,
                role: role
            })
        });
        App.setSession(data.access_token, data.user);
        App.showToast(`Account created as ${data.user.role}!`, 'success');
        closeAuthModal();
        setTimeout(() => {
            window.location.href = data.user.role === 'teacher' ? '/teacher' : '/student';
        }, 500);
    } catch (err) {
        App.showToast(err.message || 'Registration failed', 'error');
    }
}

// Prototype scanning simulation & actual file reading
function initPrototypeUploader() {
    const studentInput = document.getElementById('student-file');
    const rubricInput = document.getElementById('rubric-file');

    if (studentInput) {
        studentInput.addEventListener('change', () => {
            updateFileName('student-file', 'student-file-name');
        });
    }
    if (rubricInput) {
        rubricInput.addEventListener('change', () => {
            updateFileName('rubric-file', 'rubric-file-name');
        });
    }
}

function updateFileName(inputId, displayId) {
    const input = document.getElementById(inputId);
    const display = document.getElementById(displayId);
    if (input && input.files && input.files[0]) {
        display.textContent = 'Selected: ' + input.files[0].name;
        display.classList.remove('hidden');
        input.parentElement.classList.add('border-blue-500', 'bg-blue-50');
        input.parentElement.classList.remove('border-slate-300');
    }
}

function startScanning() {
    // Stage transition
    document.getElementById('upload-stage').classList.add('hidden');
    const loadingStage = document.getElementById('loading-stage');
    loadingStage.classList.remove('hidden');
    loadingStage.classList.add('flex');

    let progress = 0;
    const bar = document.getElementById('progress-bar');
    const interval = setInterval(() => {
        progress += Math.floor(Math.random() * 25) + 15;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            setTimeout(() => {
                showResults();
            }, 600);
        }
        bar.style.width = progress + '%';
    }, 280);
}

function showResults() {
    const loadingStage = document.getElementById('loading-stage');
    loadingStage.classList.remove('flex');
    loadingStage.classList.add('hidden');

    const resultStage = document.getElementById('result-stage');
    resultStage.classList.remove('hidden');
    resultStage.classList.add('block');
}

function resetPrototype() {
    document.getElementById('result-stage').classList.remove('block');
    document.getElementById('result-stage').classList.add('hidden');
    document.getElementById('upload-stage').classList.remove('hidden');

    ['student-file', 'rubric-file'].forEach(id => {
        const input = document.getElementById(id);
        if (input) {
            input.value = '';
            const display = document.getElementById(id + '-name');
            if (display) {
                display.textContent = '';
                display.classList.add('hidden');
            }
            input.parentElement.classList.remove('border-blue-500', 'bg-blue-50');
            input.parentElement.classList.add('border-slate-300');
        }
    });

    const bar = document.getElementById('progress-bar');
    if (bar) bar.style.width = '0%';
}

