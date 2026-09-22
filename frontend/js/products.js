// --- My Products Backend API Presentation Module ---
let myProductsStore = [];

async function renderMyProducts() {
    const t = translations[currentLang] || translations.kk;
    const tbody = document.getElementById('myProductsTbody');
    if (!tbody) return;

    try {
        const res = await fetch('/api/v1/products');
        if (res.ok) {
            const data = await res.json();
            myProductsStore = data;
        }
    } catch (err) {
        console.warn("Products list API call failed:", err);
    }

    if (!myProductsStore || myProductsStore.length === 0) {
        myProductsStore = [
            { id: 1, product_name: 'Apple iPhone 15 128Gb Black', current_price: 399000, competitor_prices_list: [389000, 395000, 410000], lowest_competitor_price: 389000, average_competitor_price: 398000, price_diff_percent: 2.57 },
            { id: 2, product_name: 'Beauty Fox Сыворотка (WB)', current_price: 11990, competitor_prices_list: [9435, 12500, 13200], lowest_competitor_price: 9435, average_competitor_price: 11711, price_diff_percent: 27.08 },
            { id: 3, product_name: 'Samsung Galaxy S24 Ultra', current_price: 519990, competitor_prices_list: [494990, 529990], lowest_competitor_price: 494990, average_competitor_price: 512490, price_diff_percent: 5.05 }
        ];
    }

    tbody.innerHTML = '';
    myProductsStore.forEach(p => {
        const tr = document.createElement('tr');
        const myPrice = p.current_price || p.myPrice || 0;
        const minPrice = p.lowest_competitor_price || p.minPrice || myPrice;
        const avgPrice = p.average_competitor_price || p.avgPrice || myPrice;
        const compPrices = p.competitor_prices_list || p.compPrices || [minPrice, avgPrice];
        const diffPct = p.price_diff_percent !== undefined ? (p.price_diff_percent >= 0 ? `+${p.price_diff_percent}%` : `${p.price_diff_percent}%`) : (p.diffPct || "+0.0%");

        tr.innerHTML = `
            <td class="py-3 font-medium text-slate-900 dark:text-white">${p.product_name || p.name}</td>
            <td class="py-3 font-semibold text-slate-900 dark:text-white font-outfit">${myPrice.toLocaleString()} ₸</td>
            <td class="py-3 text-xs text-slate-500 dark:text-slate-400">${compPrices.map(c => c.toLocaleString() + ' ₸').join(', ')}</td>
            <td class="py-3 font-semibold text-emerald-600 dark:text-emerald-400 font-outfit">${minPrice.toLocaleString()} ₸</td>
            <td class="py-3 font-semibold text-slate-700 dark:text-slate-300 font-outfit">${avgPrice.toLocaleString()} ₸</td>
            <td class="py-3"><span class="text-xs font-semibold px-2 py-0.5 rounded bg-amber-50 dark:bg-amber-950/40 text-amber-700 dark:text-amber-300 border border-amber-100 dark:border-amber-900/40">${diffPct}</span></td>
            <td class="py-3 text-right">
                <button onclick="removeProduct(${p.id})" class="text-xs text-rose-500 hover:text-rose-700 dark:hover:text-rose-400 font-medium">${t.btnDelete}</button>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

function toggleAddProductForm() {
    const form = document.getElementById('customProductForm');
    if (!form) return;
    form.classList.toggle('hidden');
    form.classList.toggle('grid');
}

async function submitCustomProduct() {
    const t = translations[currentLang] || translations.kk;
    const nameInput = document.getElementById('customProductName');
    const myPriceInput = document.getElementById('customMyPrice');
    const costPriceInput = document.getElementById('customCostPrice');

    const name = nameInput.value.trim();
    const myPrice = parseFloat(myPriceInput.value) || 0;
    const costPrice = parseFloat(costPriceInput.value) || 0;

    if (name && myPrice > 0) {
        try {
            const res = await fetch('/api/v1/products/create_custom', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product_name: name,
                    my_price: myPrice,
                    cost_price: costPrice,
                    my_shop_name: "Almaty Mobile"
                })
            });

            if (res.ok) {
                const newProduct = await res.json();
                myProductsStore.unshift(newProduct);
            }
        } catch (err) {
            console.warn("Create custom product API failed:", err);
        }

        renderMyProducts();
        
        nameInput.value = '';
        myPriceInput.value = '';
        costPriceInput.value = '';

        toggleAddProductForm();
        alert(t.alertProductAdded.replace('{name}', name));
    }
}

function removeProduct(id) {
    myProductsStore = myProductsStore.filter(p => p.id !== id);
    renderMyProducts();
}
