// --- Multilingual i18n & Language Switcher Module ---
let currentLang = localStorage.getItem('lang') || 'kk';

const translations = {
    kk: {
        systemActive: "● Жүйе белсенді",
        systemPriceApplied: "● Жаңа баға қолданылды",
        mainTitle: "Тауарды бақылау және бәсекелестерді талдау",
        mainSub: "Kaspi немесе басқа маркетплейс сілтемесін енгізіп, бәсекелес бағасын лезде бақылаңыз.",
        mpKaspi: "⚡ Маркетплейс: Kaspi.kz",
        mpWB: "🟣 Маркетплейс: Wildberries",
        mpOzon: "🔵 Маркетплейс: Ozon",
        mpYandex: "🟡 Маркетплейс: Yandex Market",
        placeholderUrl: "https://kaspi.kz/shop/p/iphone-15-128gb...",
        placeholderShop: "Дүкен аты",
        btnStartAnalysis: "Талдауды бастау",
        btnParsing: "Парсер тексеруде...",
        quickTest: "Жылдам сынақ (Маркетплейстер):",
        kpiMyPrice: "Сіздің бағаңыз",
        kpiAvgPrice: "Орташа нарық бағасы",
        kpiCostPrice: "Өз өзіндік құныңыз",
        kpiMargin: "Болжалды маржа",
        competitorsBased: "бәсекелес негізінде",
        clickToEdit: "Басу арқылы өңдеуге болады",
        efficiencyVeryHigh: "Тиімділік деңгейі: Өте жоғары",
        efficiencyGood: "Тиімділік деңгейі: Жақсы",
        efficiencyLow: "Тиімділік деңгейі: Төмен",
        efficiencyLoss: "⚠️ Тікелей шығын (Залал)",
        enterCostPrice: "Өзіндік құнды енгізіңіз",
        aiTitle: "Бағаны оңтайландыру кеңесі",
        aiAdviceText: "«Бәсекелестер соңғы 3 күнде бағаны 10 000 ₸ түсірді. Сатылымды жоғалтпас үшін ұсынылатын баға диапазонына өтуге кеңес беріледі.»",
        aiLastUpdate: "Жаңа ұсыныс",
        aiRecommendedLabel: "Ұсынылатын оңтайлы баға:",
        
        // Pricing Engine
        pricingTitle: "Баға бойынша ақылды кеңес",
        lblMinMargin: "Мин. маржа (%)",
        lblStrategy: "Баға белгілеу стратегиясы",
        stratTop1: "👑 TOP-1 (1-орынды алу)",
        stratBalanced: "⚖️ BALANCED (Теңгерімді)",
        stratMaxMargin: "💰 MAX_MARGIN (Максималды пайда)",
        btnCalculate: "Бағаны есептеу",
        minSafePriceLabel: "Мин. қауіпсіз баға:",
        positionLabel: "Позиция:",
        btnApplyRec: "Ұсынылған бағаны қабылдау",
        btnTelegram: "Telegram ескертуін алу",
        
        compListTitle: "Бәсекелестер тізімі",
        compListSub: "Нарықтағы белсенді сатушылардың бағалары",
        liveStream: "● Тікелей эфир",
        thSeller: "Сатушы (Конкурент)",
        thPrice: "Бағасы",
        thDiff: "Динамика / Айырма",
        thAction: "Әрекет",
        chartTitle: "📈 Баға динамикасы мен бәсекелестер қозғалысы",
        chartSub: "Соңғы 24 сағаттағы баға өзгеру тарихы",
        chartLegendMine: "Сіздің бағаңыз ( Almaty Mobile )",
        chartLegendLowest: "Ең төмен баға (Нарық көшбасшысы)",
        btnRefresh: "Жаңарту",
        
        myProductsTitle: "📦 Менің тауарларым",
        myProductsSub: "Бақылаудағы тауарлар тізімі, бәсекелестердің орташа бағасы мен айырмашылық %",
        btnAddProduct: "Тауар қосу",
        lblProductName: "Тауар атауы",
        lblMyPrice: "Сату бағаңыз (₸)",
        lblCostPrice: "Өзіндік құны (₸)",
        btnSave: "Сақтау",
        btnCancel: "Бас тарту",
        
        thProductName: "Тауар атауы",
        thSellerPrice: "Селлер бағасы",
        thCompPrices: "Бәсекелестер бағалары",
        thMinPrice: "Минималды баға",
        thAvgPrice: "Орташа баға",
        thDiffPct: "Айырма %",
        thActions: "Әрекет",
        thAIAnalysis: "AI Анализ",
        thHistory: "Тарих",
        btnDelete: "Жою",
        emptyProductsMsg: "Бақылаудағы тауарлар жоқ. ➕ Тауар қосу батырмасын басыңыз.",
        footerText: "SellerAI Platform © 2026 — Kaspi.kz, Wildberries, Ozon & Yandex Market Аналитика Жүйесі",
        tagLeader: "👑 Лидер",
        tagRow: "Қатарда",
        tagExpensive: "Қымбат",
        tagMyStore: "СІЗДІҢ ДҮКЕН",
        diffStable: "— Тұрақты",
        trendExpensive: "↑ Нарықтан {pct}% қымбат",
        trendCheap: "↓ Нарықтан {pct}% арзан",
        trendEqual: "~ Нарық деңгейінде",
        trendTop1: "👑 1-Орынға өтті (Оңтайлы)",
        alertAnalysisDone: "✅ Бәсекелестер дерегі жаңартылды! Ең оңтайлы баға мен маржа қайта есептелді.",
        alertPriceApplied: "✅ Жаңа баға ({price} ₸) сәтті қабылданды! Маржа мен көрсеткіштер автоматты түрде қайта есептелді.",
        alertProductAdded: "✅ Тауар \"{name}\" сәтті қосылды!",
        alertTgMsg: "📱 Telegram Bot хабарламасы жолданды:\n\n\"⚠️ SellerAI Alert: Бәсекелес бағаны 389,000 ₸-ге түсірді. 1-орынды алу үшін ұсынылатын баға: 389,000 ₸\"",
        
        // Auth UI
        btnLogout: "Шығу",
        adminPanel: "Админ панель",
        authTitleLogin: "Кіру",
        authTitleRegister: "Тіркелу",
        authSubtitle: "SellerAI жүйесіне қош келдіңіз",
        authFullName: "Аты-жөніңіз",
        authFullNamePlaceholder: "Атыңыз",
        authPassword: "Құпия сөз",
        authSubmitBtn: "Кіру",
        authSubmitBtnRegister: "Тіркелу",
        authWait: "Күтіңіз...",
        authNoAccount: "Аккаунтыңыз жоқ па?",
        authHasAccount: "Аккаунтыңыз бар ма?",
        authActionRegister: "Тіркелу",
        authActionLogin: "Кіру",
        
        // Auto update UI & Price Changes
        autoUpdateTitle: "Авто-жаңарту",
        autoUpdateSub: "Бағаларды әр 30 минут сайын тексеру",
        statusOn: "Қосулы",
        statusOff: "Өшірулі",
        badgeOk: "✅ Нақты деректер",
        badgeManual: "✏️ Қолмен",
        badgeNoData: "⚠️ Деректер жоқ",
        badgeApiReq: "🔑 API қажет",
        loadingText: "Жүктелуде...",
        loadingHistory: "Тарих жүктелуде...",
        emptyHistory: "Бұл тауардың баға тарихы әлі жоқ.",
        historyTitle: "Тарих (соңғы тексерістер)",
        thTime: "Уақыты",
        thMyPrice: "Менің бағам",
        thMinComp: "Мин. бәсекелес",
        thComps: "Конкуренттер",
        thTrend: "Тренд",
        trendUp: "↑ Өсті",
        trendDown: "↓ Түсті",
        trendStable: "= Өзгеріссіз",
        updatingText: "Жаңартылуда...",
        updatedText: "Бағалар жаңартылды!",
        nextUpdateText: "Келесі тексеру:",
        lastUpdate: "Соңғы:",
        btnCheckNow: "Қазір тексеру",
        
        priceChangesTitle: "📊 Баға өзгерістері",
        priceChangesSub: "Соңғы тексерістен бері бәсекелестердің бағалары қалай өзгерді",
        alertTrendDown: "Минималды баға <b>{old} ₸</b>-нан <b>{new} ₸</b>-ға түсті.",
        alertTrendUp: "Минималды баға <b>{old} ₸</b>-нан <b>{new} ₸</b>-ға өсті."
    },
    ru: {
        systemActive: "● Система активна",
        systemPriceApplied: "● Новая цена применена",
        mainTitle: "Мониторинг товаров и анализ конкурентов",
        mainSub: "Введите ссылку Kaspi или другого маркетплейса и мгновенно отслеживайте цены конкурентов.",
        mpKaspi: "⚡ Маркетплейс: Kaspi.kz",
        mpWB: "🟣 Маркетплейс: Wildberries",
        mpOzon: "🔵 Маркетплейс: Ozon",
        mpYandex: "🟡 Маркетплейс: Yandex Market",
        placeholderUrl: "https://kaspi.kz/shop/p/iphone-15-128gb...",
        placeholderShop: "Имя магазина",
        btnStartAnalysis: "Начать анализ",
        btnParsing: "Парсер проверяет...",
        quickTest: "Быстрый тест (Маркетплейсы):",
        kpiMyPrice: "Ваша цена",
        kpiAvgPrice: "Средняя цена рынка",
        kpiCostPrice: "Ваша себестоимость",
        kpiMargin: "Прогнозируемая маржа",
        competitorsBased: "конкурентов в базе",
        clickToEdit: "Нажмите для редактирования",
        efficiencyVeryHigh: "Уровень эффективности: Очень высокий",
        efficiencyGood: "Уровень эффективности: Хороший",
        efficiencyLow: "Уровень эффективности: Низкий",
        efficiencyLoss: "⚠️ Прямой убыток",
        enterCostPrice: "Введите себестоимость",
        aiTitle: "Совет по оптимизации цены",
        aiAdviceText: "«Конкуренты снизили цену на 10 000 ₸ за последние 3 дня. Чтобы не терять продажи, рекомендуется перейти на оптимальный диапазон цен.»",
        aiLastUpdate: "Новая рекомендация",
        aiRecommendedLabel: "Рекомендуемая оптимальная цена:",
        
        // Pricing Engine
        pricingTitle: "Умная рекомендация цены",
        lblMinMargin: "Мин. маржа (%)",
        lblStrategy: "Стратегия ценообразования",
        stratTop1: "👑 TOP-1 (Занять 1-е место)",
        stratBalanced: "⚖️ BALANCED (Сбалансированная)",
        stratMaxMargin: "💰 MAX_MARGIN (Макс. прибыль)",
        btnCalculate: "Рассчитать цену",
        minSafePriceLabel: "Мин. безопасная:",
        positionLabel: "Позиция:",
        btnApplyRec: "Принять рекомендуемую цену",
        btnTelegram: "Получить уведомление в Telegram",
        
        compListTitle: "Список конкурентов",
        compListSub: "Цены активных продавцов на рынке",
        liveStream: "● Прямой эфир",
        thSeller: "Продавец (Конкурент)",
        thPrice: "Цена",
        thDiff: "Динамика / Разница",
        thAction: "Статус",
        chartTitle: "📈 Динамика цен и движение конкурентов",
        chartSub: "История изменений цен за последние 24 часа",
        chartLegendMine: "Ваша цена ( Almaty Mobile )",
        chartLegendLowest: "Минимальная цена (Лидер рынка)",
        btnRefresh: "Обновить",
        
        myProductsTitle: "📦 Мои товары",
        myProductsSub: "Список отслеживаемых товаров, средняя цена конкурентов и разница %",
        btnAddProduct: "Добавить товар",
        lblProductName: "Название товара",
        lblMyPrice: "Ваша цена продажи (₸)",
        lblCostPrice: "Себестоимость (₸)",
        btnSave: "Сохранить",
        btnCancel: "Отмена",
        
        thProductName: "Название товара",
        thSellerPrice: "Цена продавца",
        thCompPrices: "Цены конкурентов",
        thMinPrice: "Мин. цена",
        thAvgPrice: "Средняя цена",
        thDiffPct: "Разница %",
        thActions: "Действие",
        thAIAnalysis: "AI Анализ",
        thHistory: "История",
        btnDelete: "Удалить",
        emptyProductsMsg: "Нет товаров под наблюдением. Нажмите ➕ Добавить товар.",
        footerText: "SellerAI Platform © 2026 — Аналитическая система Kaspi.kz, Wildberries, Ozon & Yandex Market",
        tagLeader: "👑 Лидер",
        tagRow: "В ряду",
        tagExpensive: "Дорого",
        tagMyStore: "ВАШ МАГАЗИН",
        diffStable: "— Стабильно",
        trendExpensive: "↑ Дороже рынка на {pct}%",
        trendCheap: "↓ Дешевле рынка на {pct}%",
        trendEqual: "~ На уровне рынка",
        trendTop1: "👑 Занял 1-е место (Оптимально)",
        alertAnalysisDone: "✅ Данные конкурентов обновлены! Оптимальная цена и маржа пересчитаны.",
        alertPriceApplied: "✅ Новая цена ({price} ₸) успешно принята! Маржа и показатели пересчитаны.",
        alertProductAdded: "✅ Товар \"{name}\" успешно добавлен!",
        alertTgMsg: "📱 Уведомление Telegram Bot отправлено:\n\n\"⚠️ SellerAI Alert: Конкурент снизил цену до 389 000 ₸. Для 1-го места рекомендуемая цена: 389 000 ₸\"",
        
        // Auth UI
        btnLogout: "Выйти",
        adminPanel: "Админ-панель",
        authTitleLogin: "Войти",
        authTitleRegister: "Регистрация",
        authSubtitle: "Добро пожаловать в SellerAI",
        authFullName: "ФИО",
        authFullNamePlaceholder: "Ваше имя",
        authPassword: "Пароль",
        authSubmitBtn: "Войти",
        authSubmitBtnRegister: "Зарегистрироваться",
        authWait: "Подождите...",
        authNoAccount: "Нет аккаунта?",
        authHasAccount: "Есть аккаунт?",
        authActionRegister: "Зарегистрироваться",
        authActionLogin: "Войти",
        
        // Auto update UI & Price Changes
        autoUpdateTitle: "Авто-обновление",
        autoUpdateSub: "Проверять цены каждые 30 минут",
        statusOn: "Включено",
        statusOff: "Выключено",
        badgeOk: "✅ Реальные данные",
        badgeManual: "✏️ Вручную",
        badgeNoData: "⚠️ Нет данных",
        badgeApiReq: "🔑 Нужен API",
        loadingText: "Загрузка...",
        loadingHistory: "Загрузка истории...",
        emptyHistory: "У этого товара еще нет истории цен.",
        historyTitle: "История (последние проверки)",
        thTime: "Время",
        thMyPrice: "Моя цена",
        thMinComp: "Мин. конкурент",
        thComps: "Конкуренты",
        thTrend: "Тренд",
        trendUp: "↑ Выросла",
        trendDown: "↓ Упала",
        trendStable: "= Без изменений",
        updatingText: "Обновление...",
        updatedText: "Цены обновлены!",
        nextUpdateText: "Следующая проверка:",
        lastUpdate: "Последняя:",
        btnCheckNow: "Проверить сейчас",
        
        priceChangesTitle: "📊 Изменения цен",
        priceChangesSub: "Как изменились цены конкурентов с последней проверки",
        alertTrendDown: "Минимальная цена упала с <b>{old} ₸</b> до <b>{new} ₸</b>.",
        alertTrendUp: "Минимальная цена выросла с <b>{old} ₸</b> до <b>{new} ₸</b>."
    },
    en: {
        systemActive: "● System Active",
        systemPriceApplied: "● New Price Applied",
        mainTitle: "Product Tracking & Competitor Analysis",
        mainSub: "Enter a Kaspi or marketplace link to track competitor pricing instantly.",
        mpKaspi: "⚡ Marketplace: Kaspi.kz",
        mpWB: "🟣 Marketplace: Wildberries",
        mpOzon: "🔵 Marketplace: Ozon",
        mpYandex: "🟡 Marketplace: Yandex Market",
        placeholderUrl: "https://kaspi.kz/shop/p/iphone-15-128gb...",
        placeholderShop: "Shop Name",
        btnStartAnalysis: "Start Analysis",
        btnParsing: "Parser checking...",
        quickTest: "Quick Test (Marketplaces):",
        kpiMyPrice: "Your Price",
        kpiAvgPrice: "Average Market Price",
        kpiCostPrice: "Cost Price",
        kpiMargin: "Estimated Margin",
        competitorsBased: "competitors in base",
        clickToEdit: "Click to edit",
        efficiencyVeryHigh: "Efficiency Level: Excellent",
        efficiencyGood: "Efficiency Level: Good",
        efficiencyLow: "Efficiency Level: Low",
        efficiencyLoss: "⚠️ Direct Loss",
        enterCostPrice: "Enter cost price",
        aiTitle: "Price Optimization Advice",
        aiAdviceText: "«Competitors dropped prices by 10,000 ₸ over the last 3 days. To maintain sales volume, moving to the recommended optimal price is advised.»",
        aiLastUpdate: "New recommendation",
        aiRecommendedLabel: "Recommended Optimal Price:",
        
        // Pricing Engine
        pricingTitle: "Smart Price Recommendation",
        lblMinMargin: "Min Margin (%)",
        lblStrategy: "Pricing Strategy",
        stratTop1: "👑 TOP-1 (Rank #1)",
        stratBalanced: "⚖️ BALANCED (Balanced)",
        stratMaxMargin: "💰 MAX_MARGIN (Max Profit)",
        btnCalculate: "Calculate Price",
        minSafePriceLabel: "Min safe price:",
        positionLabel: "Position:",
        btnApplyRec: "Accept Recommended Price",
        btnTelegram: "Get Telegram Alert",
        
        compListTitle: "Competitors List",
        compListSub: "Active seller prices in the market",
        liveStream: "● Live Feed",
        thSeller: "Seller (Competitor)",
        thPrice: "Price",
        thDiff: "Trend / Difference",
        thAction: "Status",
        chartTitle: "📈 Price Dynamics & Competitor Movement",
        chartSub: "Price change history over the last 24 hours",
        chartLegendMine: "Your Price ( Almaty Mobile )",
        chartLegendLowest: "Lowest Price (Market Leader)",
        btnRefresh: "Refresh",
        
        myProductsTitle: "📦 My Products",
        myProductsSub: "Tracked products list, competitor average prices, and difference %",
        btnAddProduct: "Add Product",
        lblProductName: "Product Name",
        lblMyPrice: "Your Selling Price (₸)",
        lblCostPrice: "Cost Price (₸)",
        btnSave: "Save",
        btnCancel: "Cancel",
        
        thProductName: "Product Name",
        thSellerPrice: "Seller Price",
        thCompPrices: "Competitor Prices",
        thMinPrice: "Min Price",
        thAvgPrice: "Avg Price",
        thDiffPct: "Diff %",
        thActions: "Actions",
        thAIAnalysis: "AI Analysis",
        thHistory: "History",
        btnDelete: "Delete",
        emptyProductsMsg: "No tracked products. Click ➕ Add Product.",
        footerText: "SellerAI Platform © 2026 — Kaspi.kz, Wildberries, Ozon & Yandex Market Analytics Platform",
        tagLeader: "👑 Leader",
        tagRow: "In Line",
        tagExpensive: "High",
        tagMyStore: "YOUR SHOP",
        diffStable: "— Stable",
        trendExpensive: "↑ {pct}% above market",
        trendCheap: "↓ {pct}% below market",
        trendEqual: "~ Market Average",
        trendTop1: "👑 Ranked #1 (Optimal)",
        alertAnalysisDone: "✅ Competitor data updated! Optimal price and margins recalculated.",
        alertPriceApplied: "✅ New price ({price} ₸) successfully applied! Margins updated.",
        alertProductAdded: "✅ Product \"{name}\" successfully added!",
        alertTgMsg: "📱 Telegram Bot alert sent:\n\n\"⚠️ SellerAI Alert: Competitor dropped price to 389,000 ₸. Recommended #1 price: 389,000 ₸\"",
        
        // Auth UI
        btnLogout: "Logout",
        adminPanel: "Admin Panel",
        authTitleLogin: "Login",
        authTitleRegister: "Register",
        authSubtitle: "Welcome to SellerAI",
        authFullName: "Full Name",
        authFullNamePlaceholder: "Your Name",
        authPassword: "Password",
        authSubmitBtn: "Login",
        authSubmitBtnRegister: "Register",
        authWait: "Please wait...",
        authNoAccount: "Don't have an account?",
        authHasAccount: "Already have an account?",
        authActionRegister: "Register",
        authActionLogin: "Login",
        
        // Auto update UI & Price Changes
        autoUpdateTitle: "Auto-Update",
        autoUpdateSub: "Check prices every 30 minutes",
        statusOn: "Enabled",
        statusOff: "Disabled",
        badgeOk: "✅ Real Data",
        badgeManual: "✏️ Manual",
        badgeNoData: "⚠️ No Data",
        badgeApiReq: "🔑 API Required",
        loadingText: "Loading...",
        loadingHistory: "Loading history...",
        emptyHistory: "No price history for this product yet.",
        historyTitle: "History (latest checks)",
        thTime: "Time",
        thMyPrice: "My Price",
        thMinComp: "Min Comp",
        thComps: "Competitors",
        thTrend: "Trend",
        trendUp: "↑ Up",
        trendDown: "↓ Down",
        trendStable: "= Stable",
        updatingText: "Updating...",
        updatedText: "Prices updated!",
        nextUpdateText: "Next check:",
        lastUpdate: "Last:",
        btnCheckNow: "Check Now",
        
        priceChangesTitle: "📊 Price Changes",
        priceChangesSub: "How competitor prices changed since last check",
        alertTrendDown: "Minimum price dropped from <b>{old} ₸</b> to <b>{new} ₸</b>.",
        alertTrendUp: "Minimum price increased from <b>{old} ₸</b> to <b>{new} ₸</b>."
    }
};

function toggleLangDropdown() {
    const menu = document.getElementById('langDropdownMenu');
    const arrow = document.getElementById('langArrow');
    if (menu) menu.classList.toggle('hidden');
    if (arrow) arrow.classList.toggle('rotate-180');
}

function closeLangDropdown() {
    const menu = document.getElementById('langDropdownMenu');
    const arrow = document.getElementById('langArrow');
    if (menu) menu.classList.add('hidden');
    if (arrow) arrow.classList.remove('rotate-180');
}

function selectLanguage(lang) {
    setLanguage(lang);
    closeLangDropdown();
}

function updateDynamicKPIs() {
    const t = translations[currentLang] || translations.kk;
    
    // 1. My Price Trend
    const myPrice = window.currentMyPrice || 399000;
    const avgPrice = window.currentAvgPrice || 388500;
    const trendEl = document.getElementById('kpiMyPriceTrend');
    if (trendEl && myPrice && avgPrice) {
        const diffPct = ((myPrice - avgPrice) / avgPrice) * 100;
        if (diffPct > 0.1) {
            trendEl.innerText = t.trendExpensive.replace('{pct}', Math.abs(diffPct).toFixed(1));
            trendEl.className = 'text-xs text-rose-600 dark:text-rose-400 font-medium mt-2 inline-block bg-rose-50 dark:bg-rose-950/40 px-2 py-0.5 rounded-md border border-rose-100 dark:border-rose-900/40';
        } else if (diffPct < -0.1) {
            trendEl.innerText = t.trendCheap.replace('{pct}', Math.abs(diffPct).toFixed(1));
            trendEl.className = 'text-xs text-emerald-600 dark:text-emerald-400 font-medium mt-2 inline-block bg-emerald-50 dark:bg-emerald-950/40 px-2 py-0.5 rounded-md border border-emerald-100 dark:border-emerald-900/40';
        } else {
            trendEl.innerText = t.trendEqual;
            trendEl.className = 'text-xs text-indigo-600 dark:text-indigo-400 font-medium mt-2 inline-block bg-indigo-50 dark:bg-indigo-950/40 px-2 py-0.5 rounded-md border border-indigo-100 dark:border-indigo-900/40';
        }
    }
    
    // 2. Competitor Count
    const compCount = (window.currentCompetitors && window.currentCompetitors.length) ? window.currentCompetitors.length : 5;
    const countEl = document.getElementById('kpiCompetitorCount');
    if (countEl) {
        countEl.innerText = `${compCount} ${t.competitorsBased}`;
    }
    
    // 3. Margin & Status
    if (typeof updateMargin === 'function') {
        updateMargin();
    }
    
    // 4. Recommendation Labels
    const minSafeEl = document.getElementById('pricingMinSafeDisplay');
    if (minSafeEl) {
        const safePrice = window.lastMinSafePrice || 377778;
        minSafeEl.innerText = `${t.minSafePriceLabel} ${safePrice.toLocaleString('ru-RU')} ₸`;
    }
    const posEl = document.getElementById('pricingPosDisplay');
    if (posEl) {
        const curPos = window.lastCurPos || 2;
        const recPos = window.lastRecPos || 1;
        posEl.innerText = `${t.positionLabel} #${curPos} → #${recPos}`;
    }
    
    // 5. System Active Badge
    const aiBadgeText = document.getElementById('aiBadgeText');
    if (aiBadgeText) {
        aiBadgeText.innerText = t.systemActive;
    }
    
    // 6. Marketplace detected badge
    if (typeof updateMpBadgeUI === 'function') {
        updateMpBadgeUI();
    }
}

function setLanguage(lang) {
    if (!translations[lang]) return;
    currentLang = lang;
    localStorage.setItem('lang', lang);

    const flags = { kk: '🇰🇿', ru: '🇷🇺', en: '🇬🇧' };
    const labels = { kk: 'Қазақша', ru: 'Русский', en: 'English' };

    const flagEl = document.getElementById('currentLangFlag');
    const labelEl = document.getElementById('currentLangLabel');
    if (flagEl) flagEl.innerText = flags[lang] || '🇰🇿';
    if (labelEl) labelEl.innerText = labels[lang] || 'Қазақша';

    const t = translations[lang];

    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (t[key]) {
            el.innerHTML = t[key];
        }
    });

    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (t[key]) {
            el.placeholder = t[key];
        }
    });

    // Update select options with data-i18n
    document.querySelectorAll('option[data-i18n]').forEach(opt => {
        const key = opt.getAttribute('data-i18n');
        if (t[key]) {
            opt.textContent = t[key];
        }
    });

    const urlInput = document.getElementById('productUrl');
    if (urlInput && typeof handleUrlInput === 'function') {
        handleUrlInput(urlInput.value);
    }

    updateDynamicKPIs();
    
    if (window.currentCompetitors && window.currentCompetitors.length > 0) {
        if (typeof renderCompetitorTable === 'function') renderCompetitorTable();
        if (typeof renderChart === 'function') renderChart(window.currentCompetitors, window.currentMyPrice);
    }
    if (typeof renderMyProducts === 'function') renderMyProducts();
    if (typeof applyLoginLang === 'function') applyLoginLang(lang);

    const autoCheckToggle = document.getElementById('autoCheckToggle');
    const autoCheckStatus = document.getElementById('autoCheckStatus');
    if (autoCheckStatus && autoCheckToggle) {
        autoCheckStatus.innerText = autoCheckToggle.checked ? t.statusOn : t.statusOff;
    }
}

// Global click to close dropdowns
document.addEventListener('click', function(e) {
    const langContainer = document.getElementById('langDropdownContainer');
    if (langContainer && !langContainer.contains(e.target)) {
        closeLangDropdown();
    }
});

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    setLanguage(currentLang);
});

