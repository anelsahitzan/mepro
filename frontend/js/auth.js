let authToken = localStorage.getItem('sellerai_token');
let isLoginMode = true;

// Override fetch to include Authorization header and handle 401
const originalFetch = window.fetch;
window.fetch = async function() {
    let [resource, config] = arguments;
    if (!config) config = {};
    if (!config.headers) config.headers = {};
    
    if (authToken && !config.headers.Authorization) {
        config.headers.Authorization = `Bearer ${authToken}`;
    }
    
    try {
        const response = await originalFetch(resource, config);
        if (response.status === 401) {
            showAuthModal();
        }
        return response;
    } catch (e) {
        throw e;
    }
};

document.addEventListener("DOMContentLoaded", () => {
    if (!authToken) {
        showAuthModal();
    } else {
        checkAuth();
    }
});

async function checkAuth() {
    try {
        const res = await fetch('/api/v1/auth/me');
        if (res.ok) {
            const user = await res.json();
            document.getElementById('userNameDisplay').textContent = user.full_name;
            document.getElementById('userProfileArea').classList.remove('hidden');
            document.getElementById('authModal').classList.add('hidden');
            
            // Re-render dashboard things if they depend on user
            if (typeof renderMyProducts === 'function') renderMyProducts();
        } else {
            showAuthModal();
        }
    } catch (e) {
        showAuthModal();
    }
}

function showAuthModal() {
    document.getElementById('authModal').classList.remove('hidden');
    document.getElementById('userProfileArea').classList.add('hidden');
}

function toggleAuthMode(e) {
    e.preventDefault();
    isLoginMode = !isLoginMode;
    document.getElementById('fullNameGroup').classList.toggle('hidden', isLoginMode);
    document.getElementById('authFullName').required = !isLoginMode;
    
    document.getElementById('authTitle').textContent = isLoginMode ? 'Кіру' : 'Тіркелу';
    document.getElementById('authSubmitBtn').textContent = isLoginMode ? 'Кіру' : 'Тіркелу';
    
    document.getElementById('authToggleText').innerHTML = isLoginMode 
        ? 'Аккаунтыңыз жоқ па? <a href="#" onclick="toggleAuthMode(event)" class="text-indigo-600 dark:text-indigo-400 font-semibold hover:underline">Тіркелу</a>'
        : 'Аккаунтыңыз бар ма? <a href="#" onclick="toggleAuthMode(event)" class="text-indigo-600 dark:text-indigo-400 font-semibold hover:underline">Кіру</a>';
}

async function handleAuthSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('authEmail').value;
    const password = document.getElementById('authPassword').value;
    const errorMsg = document.getElementById('authErrorMsg');
    const submitBtn = document.getElementById('authSubmitBtn');
    
    errorMsg.classList.add('hidden');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Күтіңіз...';
    
    try {
        if (isLoginMode) {
            const res = await originalFetch('/api/v1/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });
            
            const data = await res.json();
            if (res.ok) {
                authToken = data.access_token;
                localStorage.setItem('sellerai_token', authToken);
                await checkAuth();
            } else {
                errorMsg.textContent = data.detail || 'Қате пайда болды';
                errorMsg.classList.remove('hidden');
            }
        } else {
            const fullName = document.getElementById('authFullName').value;
            const res = await originalFetch('/api/v1/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ full_name: fullName, email, password })
            });
            
            const data = await res.json();
            if (res.ok) {
                // Auto login after register
                isLoginMode = true;
                await handleAuthSubmit(e);
            } else {
                errorMsg.textContent = data.detail || 'Қате пайда болды';
                errorMsg.classList.remove('hidden');
            }
        }
    } catch (err) {
        errorMsg.textContent = 'Желі қатесі';
        errorMsg.classList.remove('hidden');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = isLoginMode ? 'Кіру' : 'Тіркелу';
    }
}

function logout() {
    authToken = null;
    localStorage.removeItem('sellerai_token');
    showAuthModal();
}

function togglePasswordVisibility() {
    const passwordInput = document.getElementById('authPassword');
    const eyeOpen = document.getElementById('eyeIconOpen');
    const eyeClosed = document.getElementById('eyeIconClosed');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        eyeOpen.classList.remove('hidden');
        eyeClosed.classList.add('hidden');
    } else {
        passwordInput.type = 'password';
        eyeOpen.classList.add('hidden');
        eyeClosed.classList.remove('hidden');
    }
}
