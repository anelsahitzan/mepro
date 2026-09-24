// --- Analytics & Backend API Presentation Module ---
let priceChartInstance = null;
window.currentProductId = null;      // Тек API жауабынан толтырылады
window.lastRecommendationId = null;
window.currentMyPrice = 0;           // Тек API жауабынан толтырылады
window.currentCompetitors = [];

const MARKETPLACE_PRESET_URLS = {
    iphone: "https://kaspi.kz/shop/p/apple-iphone-15-128gb-chernyi-113137790/",
    wildberries: "https://www.wildberries.ru/catalog/150000000/detail.aspx",
    ozon: "https://www.ozon.ru/product/smartfon-apple-iphone-15-128gb-123456789/",
    samsung: "https://kaspi.kz/shop/p/samsung-galaxy-s24-ultra-12-256gb-seryi-116044354/",
    airpods: "https://kaspi.kz/shop/p/apple-airpods-pro-2-with-type-c-belyi-113677582/"
};

async function loadPreset(key) {
    const url = MARKETPLACE_PRESET_URLS[key] || MARKETPLACE_PRESET_URLS.iphone;
    const urlInput = document.getElementById('productUrl');
    if (urlInput) {
        urlInput.value = url;
        if (typeof handleUrlInput === 'function') {
            handleUrlInput(url);
        }
    }
    await runAnalysis(false);
}


async function runAnalysis(showSuccessAlert = true) {
    const t = (typeof translations !== 'undefined' && translations[currentLang]) ? translations[currentLang] : (typeof translations !== 'undefined' ? translations.kk : null);
    const btn = document.getElementById('submitBtn');
    if (btn) {
        btn.innerHTML = `<svg class="w-4 h-4 animate-spin text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> <span>${t ? t.btnParsing : 'Талдауда...'}</span>`;
        btn.disabled = true;
    }

    const url = document.getElementById('productUrl')?.value || "https://kaspi.kz/shop/p/apple-iphone-15-128gb-chernyi-113137790/";
    const shopName = document.getElementById('myShop')?.value || "Almaty Mobile";
    const costPrice = parseFloat(document.getElementById('costPrice')?.value) || 340000;

    let presetKey = "iphone";
    if (url.includes('wildberries')) presetKey = 'wildberries';
    else if (url.includes('ozon')) presetKey = 'ozon';
    else if (url.includes('samsung')) presetKey = 'samsung';
    else if (url.includes('airpods')) presetKey = 'airpods';

    try {
        const token = (typeof getAuthToken === 'function') ? await getAuthToken() : null;
        const headers = { 'Content-Type': 'application/json' };
        if (token) headers['Authorization'] = `Bearer ${token}`;

        const res = await fetch('/api/v1/products/analyze', {
            method: 'POST',
            headers: headers,
            body: JSON.stringify({
                preset_key: presetKey,
                product_url: url,
                my_shop_name: shopName,
                cost_price: costPrice
            })
        });

        if (res.ok) {
            const data = await res.json();
            renderAnalysisData(data);
            if (showSuccessAlert && t) {
                alert(t.alertAnalysisDone);
            }
        } else {
            const errData = await res.json().catch(() => ({}));
            console.warn("Analysis API returned error:", res.status, errData);
        }
    } catch (err) {
        console.warn("Analysis API failed:", err);
    } finally {
        if (btn) {
            btn.innerHTML = `<svg class="w-4 h-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" /></svg> <span data-i18n="btnStartAnalysis">${t ? t.btnStartAnalysis : 'Талдауды бастау'}</span>`;
            btn.disabled = false;
        }
    }
}

window.currentMarketplace = 'kaspi';

function toggleMpDropdown() {
    const menu = document.getElementById('mpDropdownMenu');
    const arrow = document.getElementById('mpArrow');
    if (!menu) return;
    const isHidden = menu.classList.contains('hidden');
    if (isHidden) {
        menu.classList.remove('hidden');
        if (arrow) arrow.classList.add('rotate-180');
    } else {
        closeMpDropdown();
    }
}

function closeMpDropdown() {
    const menu = document.getElementById('mpDropdownMenu');
    const arrow = document.getElementById('mpArrow');
    if (menu) menu.classList.add('hidden');
    if (arrow) arrow.classList.remove('rotate-180');
}

function updateMpBadgeUI(mpKey) {
    if (mpKey) window.currentMarketplace = mpKey;
    const key = window.currentMarketplace || 'kaspi';
    const btn = document.getElementById('mpDetectedBadgeBtn');
    const dot = document.getElementById('mpBadgeDot');
    const label = document.getElementById('mpBadgeText');
    if (!btn || !label || !dot) return;

    const mpTextMap = {
        kk: { kaspi: "Маркетплейс: Kaspi.kz", wildberries: "Маркетплейс: Wildberries", ozon: "Маркетплейс: Ozon", yandex: "Маркетплейс: Yandex Market" },
        ru: { kaspi: "Маркетплейс: Kaspi.kz", wildberries: "Маркетплейс: Wildberries", ozon: "Маркетплейс: Ozon", yandex: "Маркетплейс: Яндекс Маркет" },
        en: { kaspi: "Marketplace: Kaspi.kz", wildberries: "Marketplace: Wildberries", ozon: "Marketplace: Ozon", yandex: "Marketplace: Yandex Market" }
    };

    const langObj = mpTextMap[typeof currentLang !== 'undefined' ? currentLang : 'kk'] || mpTextMap.kk;
    label.innerText = langObj[key] || langObj.kaspi;

    if (key === 'wildberries') {
        dot.className = "w-2 h-2 rounded-full bg-fuchsia-500";
        btn.className = "self-start md:self-center text-xs font-semibold px-3 py-1.5 rounded-xl bg-fuchsia-50 dark:bg-fuchsia-950/60 text-fuchsia-700 dark:text-fuchsia-300 border border-fuchsia-200 dark:border-fuchsia-800 transition-all flex items-center gap-1.5 shadow-xs hover:bg-fuchsia-100 dark:hover:bg-fuchsia-900/80 cursor-pointer";
    } else if (key === 'ozon') {
        dot.className = "w-2 h-2 rounded-full bg-sky-500";
        btn.className = "self-start md:self-center text-xs font-semibold px-3 py-1.5 rounded-xl bg-cyan-50 dark:bg-cyan-950/60 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-800 transition-all flex items-center gap-1.5 shadow-xs hover:bg-cyan-100 dark:hover:bg-cyan-900/80 cursor-pointer";
    } else if (key === 'yandex') {
        dot.className = "w-2 h-2 rounded-full bg-amber-500";
        btn.className = "self-start md:self-center text-xs font-semibold px-3 py-1.5 rounded-xl bg-amber-50 dark:bg-amber-950/60 text-amber-700 dark:text-amber-300 border border-amber-200 dark:border-amber-800 transition-all flex items-center gap-1.5 shadow-xs hover:bg-amber-100 dark:hover:bg-amber-900/80 cursor-pointer";
    } else {
        dot.className = "w-2 h-2 rounded-full bg-red-500";
        btn.className = "self-start md:self-center text-xs font-semibold px-3 py-1.5 rounded-xl bg-indigo-50 dark:bg-indigo-950/60 text-indigo-700 dark:text-indigo-300 border border-indigo-200 dark:border-indigo-800 transition-all flex items-center gap-1.5 shadow-xs hover:bg-indigo-100 dark:hover:bg-indigo-900/80 cursor-pointer";
    }
}

function selectMarketplace(mpKey) {
    closeMpDropdown();
    updateMpBadgeUI(mpKey);
    if (typeof loadPreset === 'function') {
        if (mpKey === 'wildberries') loadPreset('wildberries');
        else if (mpKey === 'ozon') loadPreset('ozon');
        else if (mpKey === 'yandex') loadPreset('samsung');
        else loadPreset('iphone');
    }
}

function handleUrlInput(url) {
    const val = (url || '').toLowerCase();
    if (val.includes('wildberries') || val.includes('wb.ru') || val.includes('wb.kz')) {
        updateMpBadgeUI('wildberries');
    } else if (val.includes('ozon')) {
        updateMpBadgeUI('ozon');
    } else if (val.includes('yandex')) {
        updateMpBadgeUI('yandex');
    } else {
        updateMpBadgeUI('kaspi');
    }
}

function renderAnalysisData(data) {
    const t = translations[currentLang] || translations.kk;
    
    window.currentProductId = data.product.id;
    window.currentMyPrice = data.product.current_price;
    window.currentAvgPrice = data.market.avg_price;
    window.currentCompetitors = data.market.competitors;
    window.lastRecommendationId = data.recommendation.recommendation_id;
    window.lastRecommendedPrice = data.recommendation.recommended_price;
    window.lastMinSafePrice = data.recommendation.minimum_safe_price;
    window.lastCurPos = data.recommendation.current_position;
    window.lastRecPos = data.recommendation.recommended_position;

    const urlInput = document.getElementById('productUrl');
    if (urlInput) {
        urlInput.value = data.product.product_url;
        handleUrlInput(data.product.product_url);
    }

    const costInput = document.getElementById('costPrice');
    if (costInput) costInput.value = data.product.cost_price;

    const pricingCostInput = document.getElementById('pricingCostPrice');
    if (pricingCostInput) pricingCostInput.value = data.product.cost_price;

    document.getElementById('kpiMyPrice').innerText = data.product.current_price.toLocaleString() + ' ₸';
    document.getElementById('kpiAvgPrice').innerText = data.market.avg_price.toLocaleString() + ' ₸';

    if (typeof updateDynamicKPIs === 'function') {
        updateDynamicKPIs();
    }

    document.getElementById('aiRecommendedPriceDisplay').innerText = data.recommendation.recommended_price.toLocaleString() + ' ₸';

    const expList = document.getElementById('pricingExplanationList');
    if (expList && data.recommendation.explanation) {
        expList.innerHTML = data.recommendation.explanation.map(e => `<p>• ${e}</p>`).join('');
    }

    const badge = document.getElementById('pricingStatusBadge');
    if (badge) {
        badge.innerText = data.recommendation.status;
        badge.className = data.recommendation.status === 'RECOMMENDED' 
            ? "text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30"
            : "text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30";
    }

    renderCompetitorTable();
    renderChart(window.currentCompetitors, window.currentMyPrice);
}

function renderCompetitorTable() {
    const t = translations[currentLang] || translations.kk;
    const tbody = document.getElementById('competitorTbody');
    if (!tbody) return;
    tbody.innerHTML = '';
    (window.currentCompetitors || []).forEach(item => {
        const tr = document.createElement('tr');
        const diffStr = item.diff === 0 ? t.diffStable : (item.diff < 0 ? `↓ ${Math.abs(item.diff).toLocaleString()} ₸` : `↑ ${item.diff.toLocaleString()} ₸`);
        const diffClass = item.diff < 0 ? 'text-rose-500 dark:text-rose-400 bg-rose-50 dark:bg-rose-950/40' : (item.diff > 0 ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40' : 'text-slate-500 dark:text-slate-400');

        let tagText = item.tag;
        if (item.tag === 'leader' || item.tag?.includes('Лидер')) tagText = t.tagLeader;
        else if (item.tag === 'row' || item.tag?.includes('Қатарда')) tagText = t.tagRow;
        else if (item.tag === 'expensive' || item.tag?.includes('Қымбат')) tagText = t.tagExpensive;

        const myStoreLabel = item.is_mine ? `<span class="text-[10px] bg-indigo-100 dark:bg-indigo-950 text-indigo-700 dark:text-indigo-300 px-2 py-0.5 rounded font-semibold">${t.tagMyStore}</span>` : '';

        tr.innerHTML = `
            <td class="py-3 font-medium text-slate-900 dark:text-white flex items-center gap-2">
                ${item.name}
                ${myStoreLabel}
            </td>
            <td class="py-3 font-semibold text-slate-900 dark:text-white font-outfit">${item.price.toLocaleString()} ₸</td>
            <td class="py-3"><span class="text-xs font-semibold px-2 py-0.5 rounded ${diffClass}">${diffStr}</span></td>
            <td class="py-3 text-right"><span class="text-xs bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 px-2.5 py-1 rounded-full">${tagText}</span></td>
        `;
        tbody.appendChild(tr);
    });
}

function renderChart(competitors, myPrice) {
    const t = translations[currentLang] || translations.kk;
    const canvas = document.getElementById('priceChart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (priceChartInstance) {
        priceChartInstance.destroy();
    }

    const isDark = document.documentElement.classList.contains('dark');
    const textColor = isDark ? '#94a3b8' : '#64748b';
    const gridColor = isDark ? 'rgba(255,255,255,0.06)' : 'rgba(0,0,0,0.04)';

    const lowest = Math.min(...competitors.map(c => c.price));

    priceChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['00:00', '04:00', '08:00', '12:00', '16:00', 'Қазір'],
            datasets: [
                {
                    label: t.chartLegendMine,
                    data: [myPrice + 6000, myPrice + 6000, myPrice + 4000, myPrice, myPrice, myPrice],
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.08)',
                    borderWidth: 3,
                    tension: 0.3,
                    fill: true
                },
                {
                    label: t.chartLegendLowest,
                    data: [lowest + 5000, lowest + 3000, lowest + 1000, lowest, lowest, lowest],
                    borderColor: '#10b981',
                    borderDash: [5, 5],
                    borderWidth: 2,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    labels: { font: { family: 'Inter', size: 12 }, color: textColor }
                }
            },
            scales: {
                x: { grid: { color: gridColor }, ticks: { color: textColor } },
                y: {
                    grid: { color: gridColor },
                    ticks: { color: textColor, callback: v => v.toLocaleString() + ' ₸' }
                }
            }
        }
    });
}
