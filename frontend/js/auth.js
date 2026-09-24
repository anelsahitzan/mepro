// ===== AUTH MODULE — Official Supabase JS SDK v2 =====

const SUPABASE_URL = 'https://ugroczcfufwmmjeahppf.supabase.co';
const SUPABASE_KEY = 'sb_publishable_1EmQxbsbdN-Ved1n9JKw3A_r3SizqUq';

// Initialize official Supabase client
const _supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY, {
    auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: false,
        storageKey: 'sellerai_session'
    }
});

window.supabaseClient = _supabase;

const loginTranslations = {
    kk: {
        subtitle:     'Маркетплейс аналитика жүйесі',
        labelUser:    'ЭЛЕКТРОНДЫҚ ПОШТА',
        labelPass:    'ҚҰПИЯ СӨЗ',
        placeholderU: 'Email енгізіңіз',
        placeholderP: 'Пароль енгізіңіз',
        btnLogin:     'Кіру',
        btnLoading:   'Тексеруде...',
        errorInvalid: 'Email немесе пароль қате!',
        errorNetwork: 'Желі қатесі. Қайталап көріңіз.',
        footer:       'SellerAI Platform 2026'
    },
    ru: {
        subtitle:     'Система аналитики маркетплейсов',
        labelUser:    'ЭЛЕКТРОННАЯ ПОЧТА',
        labelPass:    'ПАРОЛЬ',
        placeholderU: 'Введите email',
        placeholderP: 'Введите пароль',
        btnLogin:     'Войти',
        btnLoading:   'Проверка...',
        errorInvalid: 'Неверный email или пароль!',
        errorNetwork: 'Ошибка сети. Попробуйте снова.',
        footer:       'SellerAI Platform 2026'
    },
    en: {
        subtitle:     'Marketplace Analytics System',
        labelUser:    'EMAIL ADDRESS',
        labelPass:    'PASSWORD',
        placeholderU: 'Enter your email',
        placeholderP: 'Enter your password',
        btnLogin:     'Sign In',
        btnLoading:   'Signing in...',
        errorInvalid: 'Invalid email or password!',
        errorNetwork: 'Network error. Please try again.',
        footer:       'SellerAI Platform 2026'
    }
};

let loginLang = localStorage.getItem('lang') || 'kk';

function applyLoginLang(lang) {
    loginLang = lang;
    const t = loginTranslations[lang] || loginTranslations.kk;
    const set = (id, prop, val) => {
        const el = document.getElementById(id);
        if (!el) return;
        if (prop === 'text') el.textContent = val;
        else if (prop === 'placeholder') el.placeholder = val;
    };
    set('loginSubtitle',  'text',        t.subtitle);
    set('loginLabelUser', 'text',        t.labelUser);
    set('loginLabelPass', 'text',        t.labelPass);
    set('loginUsername',  'placeholder', t.placeholderU);
    set('loginPassword',  'placeholder', t.placeholderP);
    set('loginBtn',       'text',        t.btnLogin);
    set('loginFooter',    'text',        t.footer);
    const e = document.getElementById('loginError');
    if (e) e.style.display = 'none';
    ['loginLangKK','loginLangRU','loginLangEN'].forEach(id => {
        const btn = document.getElementById(id);
        if (!btn) return;
        const active = btn.dataset.lang === lang;
        btn.style.background  = active ? 'rgba(99,102,241,0.3)'  : 'rgba(255,255,255,0.06)';
        btn.style.color       = active ? '#a5b4fc'               : 'rgba(255,255,255,0.4)';
        btn.style.borderColor = active ? 'rgba(99,102,241,0.5)'  : 'rgba(255,255,255,0.08)';
        btn.style.fontWeight  = active ? '700'                   : '500';
    });
}

function _showOverlay() {
    const ov = document.getElementById('loginOverlay');
    if (!ov) return;
    ov.classList.remove('hidden-overlay');
    applyLoginLang(loginLang);
    ['loginUsername','loginPassword'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = '';
    });
    const e = document.getElementById('loginError');
    if (e) e.style.display = 'none';
    setTimeout(() => { const u = document.getElementById('loginUsername'); if (u) u.focus(); }, 300);
}

function _hideOverlay() {
    const ov = document.getElementById('loginOverlay');
    if (ov) ov.classList.add('hidden-overlay');
}

function showLoginError(msg) {
    const el = document.getElementById('loginError');
    if (!el) return;
    el.textContent = msg;
    el.style.display = 'block';
    el.style.animation = 'none';
    requestAnimationFrame(() => { el.style.animation = 'shake 0.4s ease'; });
}

// Supabase auth state listener — автоматты сессия бақылауы
_supabase.auth.onAuthStateChange((event, session) => {
    if (session && (event === 'SIGNED_IN' || event === 'TOKEN_REFRESHED')) {
        window.currentUser = session.user;
        _hideOverlay();
    } else if (event === 'SIGNED_OUT') {
        window.currentUser = null;
        _showOverlay();
    }
});

// Page load — existing session тексеру
(async function initAuth() {
    applyLoginLang(loginLang);
    const { data: { session } } = await _supabase.auth.getSession();
    if (session) {
        window.currentUser = session.user;
        _hideOverlay();
    } else {
        _showOverlay();
    }
})();

async function doLogin() {
    const email    = (document.getElementById('loginUsername')?.value || '').trim();
    const password = (document.getElementById('loginPassword')?.value || '');
    const btn      = document.getElementById('loginBtn');
    const t        = loginTranslations[loginLang] || loginTranslations.kk;

    if (!email || !password) { showLoginError(t.errorInvalid); return; }

    if (btn) { btn.textContent = t.btnLoading; btn.disabled = true; btn.style.opacity = '0.8'; }
    const errEl = document.getElementById('loginError');
    if (errEl) errEl.style.display = 'none';

    const { error } = await _supabase.auth.signInWithPassword({ email, password });

    if (error) {
        const msg = (error.message || '').toLowerCase().includes('network')
            ? t.errorNetwork : t.errorInvalid;
        showLoginError(msg);
        if (btn) { btn.textContent = t.btnLogin; btn.disabled = false; btn.style.opacity = '1'; }
        const pw = document.getElementById('loginPassword');
        if (pw) { pw.value = ''; pw.focus(); }
        return;
    }

    // Success — onAuthStateChange handles overlay hide
    if (btn) {
        btn.textContent = 'Кіруде...';
        btn.style.background = 'linear-gradient(135deg,#10b981,#059669)';
        btn.style.opacity = '1';
    }
    setTimeout(() => {
        if (btn) { btn.textContent = t.btnLogin; btn.style.background = ''; btn.disabled = false; }
    }, 800);
}

async function doLogout() {
    await _supabase.auth.signOut();
    // onAuthStateChange handles _showOverlay() automatically
}

function togglePasswordVisibility() {
    const pw  = document.getElementById('loginPassword');
    const eye = document.getElementById('eyeIcon');
    if (!pw) return;
    if (pw.type === 'password') {
        pw.type = 'text';
        if (eye) eye.innerHTML = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>';
    } else {
        pw.type = 'password';
        if (eye) eye.innerHTML = '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/>';
    }
}

async function getAuthToken() {
    const { data: { session } } = await _supabase.auth.getSession();
    return session?.access_token || null;
}
window.getAuthToken = getAuthToken;
