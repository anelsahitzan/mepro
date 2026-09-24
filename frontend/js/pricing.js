// --- Pricing Engine API Presentation Module ---
function updateMargin() {
    const t = (typeof translations !== 'undefined' && translations[currentLang]) ? translations[currentLang] : (typeof translations !== 'undefined' ? translations.kk : null);
    if (!t) return;

    const costPrice = parseFloat(document.getElementById('costPrice')?.value) || 340000;
    const myPrice = window.currentMyPrice || 399000;
    
    let marginPct = 0;
    if (myPrice > 0) {
        marginPct = ((myPrice - costPrice) / myPrice) * 100;
    }
    
    const marginEl = document.getElementById('kpiMargin');
    const statusEl = document.getElementById('kpiMarginStatus');
    if (marginEl && statusEl) {
        marginEl.innerText = marginPct.toFixed(1) + '%';
        if (marginPct >= 20) {
            statusEl.innerText = t.efficiencyVeryHigh;
            marginEl.className = "text-2xl font-bold text-emerald-600 dark:text-emerald-400 font-outfit";
            statusEl.className = "text-xs text-emerald-700 dark:text-emerald-300 font-medium mt-2 inline-block bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-md border border-emerald-100 dark:border-emerald-900/40";
        } else if (marginPct >= 10) {
            statusEl.innerText = t.efficiencyGood;
            marginEl.className = "text-2xl font-bold text-emerald-600 dark:text-emerald-400 font-outfit";
            statusEl.className = "text-xs text-emerald-700 dark:text-emerald-300 font-medium mt-2 inline-block bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-md border border-emerald-100 dark:border-emerald-900/40";
        } else if (marginPct >= 0) {
            statusEl.innerText = t.efficiencyLow;
            marginEl.className = "text-2xl font-bold text-amber-600 dark:text-amber-400 font-outfit";
            statusEl.className = "text-xs text-amber-700 dark:text-amber-300 font-medium mt-2 inline-block bg-amber-50 dark:bg-amber-950/40 px-2 py-0.5 rounded-md border border-amber-100 dark:border-amber-900/40";
        } else {
            statusEl.innerText = t.efficiencyLoss;
            marginEl.className = "text-2xl font-bold text-rose-600 dark:text-rose-400 font-outfit";
            statusEl.className = "text-xs text-rose-700 dark:text-rose-300 font-medium mt-2 inline-block bg-rose-50 dark:bg-rose-950/40 px-2 py-0.5 rounded-md border border-rose-100 dark:border-rose-900/40";
        }
    }
}

async function runPricingEngine() {
    const costPrice = parseFloat(document.getElementById('pricingCostPrice').value) || 0;
    const minMargin = parseFloat(document.getElementById('pricingMinMargin').value) || 0;
    const target = document.getElementById('pricingTarget').value || "TOP_1";
    const productId = window.currentProductId || 123;

    const btn = document.getElementById('calcPricingBtn');
    const originalBtnText = btn.innerHTML;
    btn.innerHTML = `<svg class="w-3.5 h-3.5 animate-spin text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> <span>Есептелуде...</span>`;
    btn.disabled = true;

    try {
        const res = await fetch('/api/v1/pricing/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: productId,
                cost_price: costPrice,
                minimum_margin_percent: minMargin,
                target: target
            })
        });

        if (!res.ok) throw new Error("API status " + res.status);
        const data = await res.json();
        
        window.lastRecommendationId = data.recommendation_id;
        window.lastRecommendedPrice = data.pricing.recommended_price;

        const statusBadge = document.getElementById('pricingStatusBadge');
        if (statusBadge) {
            statusBadge.innerText = data.status;
            if (data.status === 'RECOMMENDED') {
                statusBadge.className = "text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30";
            } else if (data.status === 'TOP_1_UNAVAILABLE') {
                statusBadge.className = "text-[10px] font-bold px-2 py-0.5 rounded bg-amber-500/20 text-amber-300 border border-amber-500/30";
            } else {
                statusBadge.className = "text-[10px] font-bold px-2 py-0.5 rounded bg-slate-500/20 text-slate-300 border border-slate-500/30";
            }
        }

        document.getElementById('aiRecommendedPriceDisplay').innerText = data.pricing.recommended_price.toLocaleString() + ' ₸';
        document.getElementById('pricingMinSafeDisplay').innerText = `Мин. безопасная: ${data.pricing.minimum_safe_price.toLocaleString()} ₸`;
        document.getElementById('pricingPosDisplay').innerText = `Позиция: #${data.position.current} → #${data.position.recommended}`;
        
        const expList = document.getElementById('pricingExplanationList');
        if (expList && data.explanation) {
            expList.innerHTML = data.explanation.map(e => `<p>• ${e}</p>`).join('');
        }
    } catch (err) {
        console.warn("PricingEngine API error:", err);
    } finally {
        btn.innerHTML = originalBtnText;
        btn.disabled = false;
    }
}

async function applyPricingEngineRecommendation() {
    const productId = window.currentProductId || 123;
    const recId = window.lastRecommendationId || 1;

    try {
        const res = await fetch('/api/v1/pricing/apply', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product_id: productId,
                recommendation_id: recId
            })
        });

        if (!res.ok) {
            const errData = await res.json();
            alert("❌ Ошибка применения цены: " + (errData.detail || "Неизвестная ошибка"));
            return;
        }

        const data = await res.json();
        
        window.currentMyPrice = data.new_price;
        document.getElementById('kpiMyPrice').innerText = data.new_price.toLocaleString() + ' ₸';

        const myShop = (window.currentCompetitors || []).find(c => c.is_mine);
        if (myShop) {
            myShop.price = data.new_price;
        }

        const t = translations[currentLang] || translations.kk;
        const badge = document.getElementById('aiBadge');
        if (badge) {
            badge.className = 'px-3.5 py-1.5 text-xs font-semibold rounded-full bg-emerald-50 dark:bg-emerald-950/50 text-emerald-700 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800 flex items-center gap-1.5 shadow-sm transition-all';
            document.getElementById('aiBadgeText').innerText = t.systemPriceApplied;
        }

        const trendEl = document.getElementById('kpiMyPriceTrend');
        if (trendEl) {
            trendEl.innerText = t.trendTop1;
            trendEl.className = 'text-xs text-emerald-600 dark:text-emerald-400 font-medium mt-2 inline-block bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-md border border-emerald-100 dark:border-emerald-900/40';
        }

        if (typeof renderCompetitorTable === 'function') renderCompetitorTable();
        if (typeof renderChart === 'function') renderChart(window.currentCompetitors, window.currentMyPrice);

        alert(data.message || t.alertPriceApplied.replace('{price}', data.new_price.toLocaleString()));
    } catch (err) {
        console.error("Apply Price API failed:", err);
    }
}

function simulateTelegramAlert() {
    const t = translations[currentLang] || translations.kk;
    alert(t.alertTgMsg);
}
