// --- My Products Backend API Module (Нақты API) ---
let myProductsStore = [];

// ─── Marketplace status badge ──────────────────────────────────────────────
function _statusBadge(status, detail) {
    const cfg = {
        ok:           { cls: 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-300 border-emerald-100 dark:border-emerald-900/40', label: (translations[currentLang] || translations.kk).badgeOk },
        manual:       { cls: 'bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400 border-slate-200 dark:border-slate-700', label: (translations[currentLang] || translations.kk).badgeManual },
        no_data:      { cls: 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-100 dark:border-amber-900/40', label: (translations[currentLang] || translations.kk).badgeNoData },
        api_required: { cls: 'bg-red-50 dark:bg-red-950/40 text-red-600 dark:text-red-400 border-red-100 dark:border-red-900/40', label: (translations[currentLang] || translations.kk).badgeApiReq },
    };
    const c = cfg[status] || cfg.manual;
    const safeDetail = detail ? detail.replace(/"/g, '&quot;') : '';
    const titleAttr = safeDetail ? ` title="${safeDetail}"` : '';
    return `<span class="text-[10px] font-semibold px-2 py-0.5 rounded border ${c.cls} cursor-help"${titleAttr}>${c.label}</span>`;
}

// ─── Render My Products table ──────────────────────────────────────────────
async function renderMyProducts() {
    const t = translations[currentLang] || translations.kk;
    const tbody = document.getElementById('myProductsTbody');
    if (!tbody) return;

    tbody.innerHTML = `
        <tr>
            <td colspan="9" class="py-8 text-center text-xs text-slate-400 dark:text-slate-500">
                <div class="flex items-center justify-center gap-2">
                    <svg class="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
                    </svg>
                    ${(translations[currentLang] || translations.kk).loadingText}
                </div>
            </td>
        </tr>`;

    try {
        const res = await fetch('/api/v1/products');
        if (res.ok) {
            myProductsStore = await res.json();
        } else {
            console.warn('GET /api/v1/products error:', res.status);
            myProductsStore = [];
        }
    } catch (err) {
        console.warn('Products list API call failed:', err);
        myProductsStore = [];
    }

    tbody.innerHTML = '';

    if (!myProductsStore || myProductsStore.length === 0) {
        const emptyLabel = (t && t.emptyProductsMsg) || 'Бақылаудағы тауарлар жоқ. ➕ Тауар қосу батырмасын басыңыз.';
        tbody.innerHTML = `
            <tr>
                <td colspan="9" class="py-10 text-center">
                    <div class="flex flex-col items-center gap-3 text-slate-400 dark:text-slate-500">
                        <svg class="w-10 h-10 opacity-40" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.5">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5M10 11.25h4M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
                        </svg>
                        <p class="text-sm font-medium">${emptyLabel}</p>
                    </div>
                </td>
            </tr>`;
        return;
    }

    myProductsStore.forEach(p => {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-slate-50 dark:hover:bg-slate-800/40 transition-colors';

        const myPrice    = p.current_price || 0;
        const minPrice   = p.lowest_competitor_price;
        const avgPrice   = p.average_competitor_price;
        const compPrices = p.competitor_prices_list || [];
        const diffPct    = p.price_diff_percent;
        const status     = p.marketplace_status || 'manual';
        const detail     = p.marketplace_status_detail || '';
        const name       = p.product_name || `#${p.id}`;

        // Айырма % бояуы
        let diffHtml = '<span class="text-slate-400 dark:text-slate-500 text-xs">—</span>';
        if (diffPct !== null && diffPct !== undefined && compPrices.length > 0) {
            const sign  = diffPct >= 0 ? '+' : '';
            const color = diffPct > 5
                ? 'bg-rose-50 dark:bg-rose-950/40 text-rose-600 dark:text-rose-400 border-rose-100 dark:border-rose-900/40'
                : diffPct < -2
                    ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-700 dark:text-emerald-400 border-emerald-100 dark:border-emerald-900/40'
                    : 'bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border-amber-100 dark:border-amber-900/40';
            diffHtml = `<span class="text-xs font-semibold px-2 py-0.5 rounded border ${color}">${sign}${diffPct.toFixed(1)}%</span>`;
        }

        // Бәсекелестер бағалары бағаны
        let compHtml = _statusBadge(status, detail);
        if (compPrices.length > 0) {
            const shown = compPrices.slice(0, 3).map(c => Number(c).toLocaleString('ru-RU') + '\u00a0₸').join(', ');
            const more  = compPrices.length > 3 ? ` <span class="text-slate-400 dark:text-slate-500">+${compPrices.length - 3}</span>` : '';
            compHtml = `<span class="text-xs text-slate-600 dark:text-slate-300">${shown}${more}</span>`;
        }

        // Тауар атауы — URL болса сілтеме
        const isCustomUrl = !p.product_url || p.product_url.startsWith('custom://');
        const nameHtml = isCustomUrl
            ? `<span class="font-medium text-slate-900 dark:text-white">${name}</span>`
            : `<a href="${p.product_url}" target="_blank" rel="noopener" class="font-medium text-slate-900 dark:text-white hover:text-indigo-600 dark:hover:text-indigo-400 transition-colors">${name}</a>`;

        tr.innerHTML = `
            <td class="py-3 pr-4">
                <div class="flex flex-col gap-1">
                    ${nameHtml}
                    ${_statusBadge(status, detail)}
                </div>
            </td>
            <td class="py-3 font-semibold text-slate-900 dark:text-white font-outfit whitespace-nowrap">
                ${myPrice ? Number(myPrice).toLocaleString('ru-RU') + '\u00a0₸' : '—'}
            </td>
            <td class="py-3 text-xs">${compHtml}</td>
            <td class="py-3 font-semibold font-outfit whitespace-nowrap ${minPrice ? 'text-emerald-600 dark:text-emerald-400' : 'text-slate-400 dark:text-slate-500'}">
                ${minPrice ? Number(minPrice).toLocaleString('ru-RU') + '\u00a0₸' : '—'}
            </td>
            <td class="py-3 font-semibold font-outfit whitespace-nowrap text-slate-700 dark:text-slate-300">
                ${avgPrice ? Number(avgPrice).toLocaleString('ru-RU') + '\u00a0₸' : '—'}
            </td>
            <td class="py-3">${diffHtml}</td>
            <td class="py-3 text-center">
                <button onclick="analyzeProduct(${p.id}, this)" class="text-[10px] bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 font-semibold px-2 py-1 rounded hover:bg-indigo-200 dark:hover:bg-indigo-800 transition-colors shadow-sm flex items-center justify-center gap-1 mx-auto">
                    <span>🤖</span> ${(t && t.thAIAnalysis) || 'Анализ'}
                </button>
            </td>
            <td class="py-3 text-center">
                <button onclick="viewHistory(${p.id}, this)" class="text-[10px] bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-semibold px-2 py-1 rounded hover:bg-slate-200 dark:hover:bg-slate-700 transition-colors shadow-sm flex items-center justify-center gap-1 mx-auto">
                    <span>🕒</span> ${(t && t.thHistory) || 'Тарих'}
                </button>
            </td>
            <td class="py-3 text-right">
                <button onclick="removeProduct(${p.id})"
                        class="text-xs text-rose-500 hover:text-rose-700 dark:hover:text-rose-400 font-medium transition-colors px-2 py-1 rounded hover:bg-rose-50 dark:hover:bg-rose-950/30">
                    ${t.btnDelete}
                </button>
            </td>`;
        tbody.appendChild(tr);
    });
    
    // Дашбордты да жаңарту
    loadPriceChanges();
}

// ─── Toggle add form ───────────────────────────────────────────────────────
function toggleAddProductForm() {
    const form = document.getElementById('customProductForm');
    if (!form) return;
    form.classList.toggle('hidden');
    form.classList.toggle('grid');
    if (!form.classList.contains('hidden')) {
        setTimeout(() => document.getElementById('customProductName')?.focus(), 50);
    }
}

// ─── Submit new product (нақты API) ───────────────────────────────────────
async function submitCustomProduct() {
    const t = translations[currentLang] || translations.kk;

    const nameInput  = document.getElementById('customProductName');
    const priceInput = document.getElementById('customMyPrice');
    const urlInput   = document.getElementById('customProductUrl');
    const costInput  = document.getElementById('customCostPrice');
    const shopInput  = document.getElementById('customShopName');
    const submitBtn  = document.getElementById('submitProductBtn');

    const name      = nameInput?.value.trim() || '';
    const myPrice   = parseFloat(priceInput?.value) || 0;
    const url       = urlInput?.value.trim() || '';
    const costPrice = costInput?.value ? parseFloat(costInput.value) : null;
    const shopName  = shopInput?.value.trim() || '';

    if (!name) { nameInput?.focus(); return; }
    if (myPrice <= 0) { priceInput?.focus(); return; }

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<svg class="w-3 h-3 animate-spin inline-block mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>Сақталуда...';
    }

    try {
        const res = await fetch('/api/v1/products/add_with_url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_name:    name,
                my_price:        myPrice,
                marketplace_url: url || null,
                cost_price:      costPrice,
                my_shop_name:    shopName || null
            })
        });

        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `API қатесі ${res.status}`);
        }

        const saved = await res.json();

        // Форм тазалау
        if (nameInput)  nameInput.value  = '';
        if (priceInput) priceInput.value = '';
        if (urlInput)   urlInput.value   = '';
        if (costInput)  costInput.value  = '';
        if (shopInput)  shopInput.value  = '';
        toggleAddProductForm();

        await renderMyProducts();

        const msgs = {
            ok:           `✅ «${name}» қосылды! ${saved.competitors_count} бәсекелес бағасы алынды.`,
            no_data:      `✅ «${name}» қосылды. Бәсекелес деректері алынбады — URL-ді тексеріңіз.`,
            api_required: `✅ «${name}» қосылды. Бәсекелес бағалары үшін маркетплейс API токені қажет.`,
            manual:       `✅ «${name}» қосылды. URL берілмеді — тек сіздің бағаңыз сақталды.`,
        };
        alert(msgs[saved.marketplace_status] || `✅ «${name}» сақталды.`);

    } catch (err) {
        console.error('submitCustomProduct error:', err);
        alert('❌ Қате: ' + err.message);
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<span>💾</span> <span>Сақтау</span>';
        }
    }
}

// ─── Delete product (нақты базадан) ───────────────────────────────────────
async function removeProduct(id) {
    const t = translations[currentLang] || translations.kk;
    const product = myProductsStore.find(p => p.id === id);
    const name = product?.product_name || `#${id}`;
    if (!confirm(`«${name}» жоюды растайсыз ба?`)) return;

    try {
        const res = await fetch(`/api/v1/products/${id}`, { method: 'DELETE' });
        if (!res.ok) {
            const errData = await res.json().catch(() => ({}));
            throw new Error(errData.detail || `Өшіру қатесі ${res.status}`);
        }
        myProductsStore = myProductsStore.filter(p => p.id !== id);
        await renderMyProducts();
    } catch (err) {
        console.error('removeProduct error:', err);
        alert('❌ Өшіру қатесі: ' + err.message);
    }
}

// ─── AI Analysis Expandable Row ───────────────────────────────────────────
async function analyzeProduct(id, btn) {
    const tr = btn.closest('tr');
    let nextTr = tr.nextElementSibling;
    
    // Егер панель ашық тұрса - жабу
    if (nextTr && nextTr.classList.contains('ai-analysis-row')) {
        nextTr.remove();
        return;
    }

    // Барлық басқа ашық AI панельдерді жабу
    document.querySelectorAll('.ai-analysis-row').forEach(row => row.remove());

    // Жаңа қатар құру (Loading state)
    const expandedTr = document.createElement('tr');
    expandedTr.className = 'ai-analysis-row bg-indigo-50/50 dark:bg-indigo-950/20 border-b border-indigo-100 dark:border-indigo-900/30';
    expandedTr.innerHTML = `
        <td colspan="8" class="p-4">
            <div class="flex items-center justify-center gap-2 text-xs text-indigo-500 dark:text-indigo-400 py-4">
                <svg class="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
                AI талдау жүргізуде...
            </div>
        </td>
    `;
    tr.after(expandedTr);

    try {
        const res = await fetch(`/api/v1/products/${id}/ai-analysis`);
        if (!res.ok) throw new Error(`API қатесі: ${res.status}`);
        
        const data = await res.json();
        
        let alertColor = "text-slate-700 dark:text-slate-300";
        let alertBg = "bg-white dark:bg-slate-900";
        let icon = "💡";

        if (data.alert_type === 'PRICE_DROP') {
            alertColor = "text-rose-700 dark:text-rose-300";
            alertBg = "bg-rose-50 dark:bg-rose-950/20";
            icon = "📉";
        } else if (data.alert_type === 'OPPORTUNITY' || data.alert_type === 'LEADER') {
            alertColor = "text-emerald-700 dark:text-emerald-300";
            alertBg = "bg-emerald-50 dark:bg-emerald-950/20";
            icon = "👑";
        } else if (data.alert_type === 'DUMPING_DETECTED') {
            alertColor = "text-amber-700 dark:text-amber-300";
            alertBg = "bg-amber-50 dark:bg-amber-950/20";
            icon = "⚠️";
        } else if (data.alert_type === 'NO_DATA') {
            alertColor = "text-slate-500 dark:text-slate-400";
            icon = "ℹ️";
        }

        let priceHtml = "";
        if (data.recommended_price) {
            priceHtml = `
                <div class="mt-3 pt-3 border-t border-slate-200 dark:border-slate-700/50 flex items-center justify-between">
                    <span class="text-xs font-semibold text-slate-500 dark:text-slate-400">Ұсынылатын баға:</span>
                    <span class="text-lg font-bold text-slate-900 dark:text-white font-outfit">${data.recommended_price.toLocaleString('ru-RU')} ₸</span>
                </div>
            `;
        }

        expandedTr.innerHTML = `
            <td colspan="8" class="p-4">
                <div class="flex items-start gap-4 p-4 rounded-xl border border-indigo-100 dark:border-indigo-900/50 ${alertBg} shadow-sm">
                    <div class="text-2xl">${icon}</div>
                    <div class="flex-1">
                        <h4 class="text-sm font-semibold mb-1 ${alertColor}">AI Кеңесі</h4>
                        <p class="text-xs leading-relaxed text-slate-600 dark:text-slate-400">${data.analysis_text}</p>
                        ${priceHtml}
                    </div>
                </div>
            </td>
        `;
    } catch (err) {
        console.error('AI Analysis failed:', err);
        expandedTr.innerHTML = `
            <td colspan="9" class="p-4">
                <div class="p-4 rounded-xl border border-red-100 bg-red-50 text-red-600 text-xs text-center">
                    ❌ Талдау кезінде қате кетті: ${err.message}
                </div>
            </td>
        `;
    }
}

// ─── Price History Expandable Row ─────────────────────────────────────────
async function viewHistory(id, btn) {
    const tr = btn.closest('tr');
    let nextTr = tr.nextElementSibling;
    
    if (nextTr && nextTr.classList.contains('history-row')) {
        nextTr.remove();
        return;
    }

    document.querySelectorAll('.history-row').forEach(row => row.remove());

    const expandedTr = document.createElement('tr');
    expandedTr.className = 'history-row bg-slate-50/50 dark:bg-slate-900/50 border-b border-slate-100 dark:border-slate-800/50';
    expandedTr.innerHTML = `
        <td colspan="9" class="p-4">
            <div class="flex items-center justify-center gap-2 text-xs text-slate-500 dark:text-slate-400 py-4">
                <svg class="w-4 h-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg>
                ${(translations[currentLang] || translations.kk).loadingHistory}
            </div>
        </td>
    `;
    tr.after(expandedTr);

    try {
        const res = await fetch(`/api/v1/products/${id}/history`);
        if (!res.ok) throw new Error(`API қатесі: ${res.status}`);
        
        const data = await res.json();
        
        if (!data.sessions || data.sessions.length === 0) {
            expandedTr.innerHTML = `
                <td colspan="9" class="p-4">
                    <div class="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-500 text-xs text-center">
                        ${(translations[currentLang] || translations.kk).emptyHistory}
                    </div>
                </td>
            `;
            return;
        }

        let rowsHtml = data.sessions.map(s => {
            const date = new Date(s.session_time).toLocaleString('ru-RU', {day:'2-digit', month:'2-digit', hour:'2-digit', minute:'2-digit'});
            
            let trendIcon = '<span class="text-slate-400">—</span>';
            if (s.trend === 'up') trendIcon = '<span class="text-rose-500 font-bold">${(translations[currentLang] || translations.kk).trendUp}</span>';
            if (s.trend === 'down') trendIcon = '<span class="text-emerald-500 font-bold">${(translations[currentLang] || translations.kk).trendDown}</span>';
            if (s.trend === 'stable') trendIcon = '<span class="text-slate-500">${(translations[currentLang] || translations.kk).trendStable}</span>';

            return `
                <tr class="border-b border-slate-100 dark:border-slate-800/50 last:border-0 hover:bg-slate-50 dark:hover:bg-slate-800/30">
                    <td class="py-2 px-3 text-xs text-slate-600 dark:text-slate-400">${date}</td>
                    <td class="py-2 px-3 text-xs font-semibold">${s.my_price ? s.my_price.toLocaleString('ru-RU') + ' ₸' : '—'}</td>
                    <td class="py-2 px-3 text-xs font-semibold text-emerald-600 dark:text-emerald-400">${s.min_price ? s.min_price.toLocaleString('ru-RU') + ' ₸' : '—'}</td>
                    <td class="py-2 px-3 text-xs text-slate-600 dark:text-slate-400">${s.avg_price ? s.avg_price.toLocaleString('ru-RU') + ' ₸' : '—'}</td>
                    <td class="py-2 px-3 text-xs text-center text-slate-500">${s.competitor_count}</td>
                    <td class="py-2 px-3 text-xs text-right">${trendIcon}</td>
                </tr>
            `;
        }).join('');

        expandedTr.innerHTML = `
            <td colspan="9" class="p-4">
                <div class="rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-sm overflow-hidden">
                    <div class="px-4 py-2 bg-slate-50 dark:bg-slate-900 border-b border-slate-200 dark:border-slate-700 font-semibold text-xs text-slate-700 dark:text-slate-300">
                        ${(translations[currentLang] || translations.kk).historyTitle}
                    </div>
                    <div class="overflow-x-auto">
                        <table class="w-full text-left">
                            <thead>
                                <tr class="text-[10px] uppercase tracking-wider text-slate-500 bg-slate-50/50 dark:bg-slate-900/50 border-b border-slate-100 dark:border-slate-800">
                                    <th class="py-2 px-3">${(translations[currentLang] || translations.kk).thTime}</th>
                                    <th class="py-2 px-3">${(translations[currentLang] || translations.kk).thMyPrice}</th>
                                    <th class="py-2 px-3">${(translations[currentLang] || translations.kk).thMinComp}</th>
                                    <th class="py-2 px-3">${(translations[currentLang] || translations.kk).thAvgPrice}</th>
                                    <th class="py-2 px-3 text-center">${(translations[currentLang] || translations.kk).thComps}</th>
                                    <th class="py-2 px-3 text-right">${(translations[currentLang] || translations.kk).thTrend}</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${rowsHtml}
                            </tbody>
                        </table>
                    </div>
                </div>
            </td>
        `;
    } catch (err) {
        expandedTr.innerHTML = `
            <td colspan="9" class="p-4">
                <div class="p-4 rounded-xl border border-red-100 bg-red-50 text-red-600 text-xs text-center">
                    ❌ Тарихты жүктеу қатесі: ${err.message}
                </div>
            </td>
        `;
    }
}

// ─── Refresh All Prices ───────────────────────────────────────────────────
async function refreshAllPrices() {
    const btn = document.getElementById('refreshAllBtn');
    if (!btn) return;
    
    const originalHtml = btn.innerHTML;
    btn.innerHTML = `<span><svg class="w-3 h-3 animate-spin inline" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path></svg></span> <span>${(translations[currentLang] || translations.kk).updatingText}</span>`;
    btn.disabled = true;

    try {
        const res = await fetch('/api/v1/products/refresh-all', { method: 'POST' });
        const data = await res.json();
        
        // Күте тұрып кестені қайта жүктеу
        await renderMyProducts();
        
        alert("✅ " + (data.message || "" + (translations[currentLang] || translations.kk).updatedText + ""));
    } catch (err) {
        console.error('Refresh error:', err);
        alert('❌ Жаңарту қатесі: ' + err.message);
    } finally {
        btn.innerHTML = originalHtml;
        btn.disabled = false;
    }
}

// ─── Load Dashboard Price Changes ─────────────────────────────────────────
async function loadPriceChanges() {
    const block = document.getElementById('priceChangesBlock');
    const list = document.getElementById('priceChangesList');
    if (!block || !list) return;

    try {
        const res = await fetch('/api/v1/dashboard/price-changes');
        if (!res.ok) return;
        const alerts = await res.json();

        if (alerts.length === 0) {
            block.style.display = 'none';
            return;
        }

        block.style.display = 'block';
        list.innerHTML = alerts.map(a => {
            const time = new Date(a.changed_at).toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'});
            if (a.trend === 'down') {
                return `
                    <div class="flex items-center gap-3 p-3 rounded-lg bg-rose-50 dark:bg-rose-950/20 border border-rose-100 dark:border-rose-900/30">
                        <div class="w-8 h-8 rounded-full bg-rose-100 dark:bg-rose-900/50 flex items-center justify-center text-rose-600 dark:text-rose-400 shrink-0">
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" /></svg>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium text-slate-900 dark:text-white truncate">${a.product_name}</p>
                            <p class="text-xs text-rose-600 dark:text-rose-400">${(translations[currentLang] || translations.kk).alertTrendDown.replace('{old}', a.old_min_price.toLocaleString('ru-RU')).replace('{new}', a.new_min_price.toLocaleString('ru-RU'))}</p>
                        </div>
                        <div class="text-xs text-slate-400 whitespace-nowrap">${time}</div>
                    </div>
                `;
            } else {
                return `
                    <div class="flex items-center gap-3 p-3 rounded-lg bg-emerald-50 dark:bg-emerald-950/20 border border-emerald-100 dark:border-emerald-900/30">
                        <div class="w-8 h-8 rounded-full bg-emerald-100 dark:bg-emerald-900/50 flex items-center justify-center text-emerald-600 dark:text-emerald-400 shrink-0">
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" /></svg>
                        </div>
                        <div class="flex-1 min-w-0">
                            <p class="text-sm font-medium text-slate-900 dark:text-white truncate">${a.product_name}</p>
                            <p class="text-xs text-emerald-600 dark:text-emerald-400">${(translations[currentLang] || translations.kk).alertTrendUp.replace('{old}', a.old_min_price.toLocaleString('ru-RU')).replace('{new}', a.new_min_price.toLocaleString('ru-RU'))}</p>
                        </div>
                        <div class="text-xs text-slate-400 whitespace-nowrap">${time}</div>
                    </div>
                `;
            }
        }).join('');
    } catch (e) {
        console.error('Error loading price changes:', e);
    }
}

// ─── Scheduler Status and Toggle ──────────────────────────────────────────
async function loadSchedulerStatus() {
    const textEl = document.getElementById('autoCheckStatusText');
    const toggleEl = document.getElementById('autoCheckToggle');
    const nextCheckEl = document.getElementById('nextCheckTime');
    if (!textEl || !toggleEl) return;

    try {
        const res = await fetch('/api/v1/scheduler/status');
        if (!res.ok) return;
        const data = await res.json();

        toggleEl.checked = data.enabled;
        textEl.textContent = data.enabled ? (translations[currentLang] || translations.kk).statusOn : (translations[currentLang] || translations.kk).statusOff;
        
        if (data.enabled && data.next_run_time) {
            const time = new Date(data.next_run_time).toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'});
            nextCheckEl.textContent = time;
        } else {
            nextCheckEl.textContent = '—';
        }
    } catch (e) {
        console.error('Error loading scheduler status:', e);
    }
}

async function toggleAutoCheck() {
    const toggleEl = document.getElementById('autoCheckToggle');
    const textEl = document.getElementById('autoCheckStatusText');
    const nextCheckEl = document.getElementById('nextCheckTime');
    
    textEl.textContent = (translations[currentLang] || translations.kk).authWait;
    try {
        const res = await fetch('/api/v1/scheduler/toggle', { method: 'POST' });
        const data = await res.json();
        
        toggleEl.checked = data.enabled;
        textEl.textContent = data.enabled ? (translations[currentLang] || translations.kk).statusOn : (translations[currentLang] || translations.kk).statusOff;
        
        if (data.enabled && data.next_run_time) {
            const time = new Date(data.next_run_time).toLocaleTimeString('ru-RU', {hour: '2-digit', minute:'2-digit'});
            nextCheckEl.textContent = time;
        } else {
            nextCheckEl.textContent = '—';
        }
    } catch (e) {
        console.error('Error toggling scheduler:', e);
        // revert
        toggleEl.checked = !toggleEl.checked;
        textEl.textContent = toggleEl.checked ? (translations[currentLang] || translations.kk).statusOn : (translations[currentLang] || translations.kk).statusOff;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadSchedulerStatus();
    // Refresh status every minute to keep nextCheck time updated
    setInterval(loadSchedulerStatus, 60000);
});


