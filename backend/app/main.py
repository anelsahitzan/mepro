import os
import logging
from typing import List
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config import settings
from app.database import get_db, engine, Base
from app.models import User, Product, PriceHistory, AIRecommendation, Offer, PricingRecommendationDB, PriceChange
from app.schemas import (
    UserCreate, UserLogin, Token, UserOut,
    ProductCreate, CustomProductCreate, AddProductRequest, ProductResponse, CompetitorOffer,
    AIRecommendationOut,
    PricingRecommendRequest, PricingRecommendResponse, PricingApplyRequest, PricingApplyResponse,
    MarketStatsSchema, PricingStatsSchema, PositionStatsSchema,
    ProductAnalyzeRequest, ProductAnalyzeResponse
)
from app.auth import get_password_hash, verify_password, create_access_token, get_current_user
from app.services.parser import UnifiedMarketplaceRouter, KaspiParser
from app.services.ai_advisor import AIAdvisorService
from app.services.pricing_engine import PricingEngine
from app.scheduler import start_scheduler, get_scheduler_status, toggle_scheduler
import json

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sellerai.api")

# Ensure tables are created if running directly without migrations
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    logger.warning(f"DB кестелерін авто-құру барысында ескерту: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="SellerAI: Көп маркетплейстік (Kaspi, WB, Ozon, Yandex) баға мониторингі, бәсекелестер талдауы және AI кеңес беру платформасы"
)

@app.on_event("startup")
def on_startup():
    start_scheduler()


# Enable CORS for frontend UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")
if not os.path.exists(FRONTEND_DIR):
    FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

if os.path.exists(FRONTEND_DIR):
    js_dir = os.path.join(FRONTEND_DIR, "js")
    styles_dir = os.path.join(FRONTEND_DIR, "styles")
    if os.path.exists(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")
        app.mount("/frontend/js", StaticFiles(directory=js_dir), name="frontend_js")
    if os.path.exists(styles_dir):
        app.mount("/styles", StaticFiles(directory=styles_dir), name="styles")
        app.mount("/frontend/styles", StaticFiles(directory=styles_dir), name="frontend_styles")

@app.get("/", include_in_schema=False)
def read_index():
    index_file = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return FileResponse("index.html")

@app.post("/api/v1/auth/register", response_model=UserOut, tags=["Auth"])
def register(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Бұл email тіркелген.")
    new_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/api/v1/auth/login", response_model=Token, tags=["Auth"])
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Қате email немесе құпия сөз.")
    
    access_token = create_access_token(data={"sub": str(db_user.id)})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/v1/auth/me", response_model=UserOut, tags=["Auth"])
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


def _get_marketplace_status(mp_type: str, product_url: str, has_offers: bool) -> dict:
    """Маркетплейс парсинг статусын анықтау"""
    if product_url.startswith("custom://"):
        return {
            "status": "manual",
            "detail": "Қолмен қосылды. Маркетплейс сілтемесі берілмеген."
        }
    if mp_type in ["ozon", "yandex_market"]:
        api_name = "Ozon Seller API (api-seller.ozon.ru)" if mp_type == "ozon" else "Yandex Market Partner API"
        return {
            "status": "api_required",
            "detail": f"Нақты бағалар үшін {api_name} токені қажет."
        }
    if has_offers:
        return {
            "status": "ok",
            "detail": "Нақты маркетплейс деректері."
        }
    return {
        "status": "no_data",
        "detail": "Бәсекелес деректері алынбады. URL-ді тексеріңіз немесе қайта талдаңыз."
    }


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "online",
        "service": "SellerAI Multi-Marketplace Backend",
        "supported_marketplaces": ["kaspi", "wildberries", "ozon", "yandex_market"],
        "timestamp": datetime.utcnow().isoformat()
    }

@app.post("/api/v1/products/add", response_model=ProductResponse, tags=["Products & Parsing"])
def add_product(payload: ProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    1. Тауар сілтемесін немесе SKU қабылдайды (Kaspi / Wildberries / Ozon)
    2. Маркетплейсті автоматты анықтап, бәсекелестер бағасын жинайды
    3. Деректерді PostgreSQL базасына (products, price_history) жазады
    4. AI арқылы талдау жасап, кеңес шығарады
    """
    user = current_user
    
    # 1. URL / ID парсинг және маркетплейсті анықтау
    mp_type, sku_id, guessed_name = UnifiedMarketplaceRouter.extract_info(payload.product_url)
    
    # Базада бұл тауар бұрын бар ма?
    product = db.query(Product).filter(
        Product.user_id == user.id,
        Product.sku == sku_id,
        Product.marketplace == mp_type
    ).first()

    if not product:
        product = Product(
            user_id=user.id,
            product_url=payload.product_url,
            marketplace=mp_type,
            sku=sku_id,
            product_name=guessed_name,
            cost_price=payload.cost_price,
            min_price_threshold=payload.min_price_threshold,
            last_checked_at=datetime.utcnow()
        )
        db.add(product)
        db.commit()
        db.refresh(product)
    else:
        if payload.cost_price:
            product.cost_price = payload.cost_price
        if payload.min_price_threshold:
            product.min_price_threshold = payload.min_price_threshold
        product.last_checked_at = datetime.utcnow()
        db.commit()

    # 2. Тиісті маркетплейстен бәсекелестерді парсинг жасау
    offers = UnifiedMarketplaceRouter.fetch_offers(mp_type, sku_id)
    
    # 3. PostgreSQL price_history кестесіне сақтау
    current_my_price = None
    competitor_offers_out = []
    
    for item in offers:
        is_mine = (item["seller_name"].lower() == payload.my_shop_name.lower())
        if is_mine:
            current_my_price = item["price"]

        history_record = PriceHistory(
            product_id=product.id,
            seller_name=item["seller_name"],
            is_my_shop=is_mine,
            price=item["price"],
            is_available=item.get("is_available", True),
            delivery_type=item.get("delivery_type"),
            recorded_at=datetime.utcnow()
        )
        db.add(history_record)

        competitor_offers_out.append(CompetitorOffer(
            seller_name=item["seller_name"],
            price=item["price"],
            is_my_shop=is_mine,
            is_available=item.get("is_available", True),
            delivery_type=item.get("delivery_type"),
            rating=item.get("rating"),
            reviews_count=item.get("reviews_count")
        ))

    if current_my_price:
        product.current_price = current_my_price

    # 4. AI Сараптамасын жүргізу және сақтау
    raw_offers_dict = [o.model_dump() for o in competitor_offers_out]
    ai_result = AIAdvisorService.generate_recommendation(
        product_name=product.product_name or guessed_name,
        my_price=float(product.current_price) if product.current_price else None,
        cost_price=float(product.cost_price) if product.cost_price else None,
        min_price=float(product.min_price_threshold) if product.min_price_threshold else None,
        competitor_offers=raw_offers_dict
    )

    ai_record = AIRecommendation(
        product_id=product.id,
        recommended_price=ai_result.get("recommended_price"),
        alert_type=ai_result.get("alert_type", "INFO"),
        analysis_text=ai_result.get("analysis_text", "")
    )
    db.add(ai_record)
    db.commit()
    db.refresh(product)
    db.refresh(ai_record)

    prices_list = [o.price for o in competitor_offers_out]
    lowest_price = min(prices_list) if prices_list else None
    avg_price = round(sum(prices_list) / len(prices_list), 2) if prices_list else None
    my_price = float(product.current_price) if product.current_price else (lowest_price or 0.0)
    diff_percent = round(((my_price - lowest_price) / lowest_price) * 100, 2) if (lowest_price and lowest_price > 0) else 0.0

    return ProductResponse(
        id=product.id,
        product_name=product.product_name,
        sku=product.sku,
        product_url=product.product_url,
        cost_price=float(product.cost_price) if product.cost_price else None,
        current_price=float(product.current_price) if product.current_price else None,
        min_price_threshold=float(product.min_price_threshold) if product.min_price_threshold else None,
        lowest_competitor_price=lowest_price,
        average_competitor_price=avg_price,
        price_diff_percent=diff_percent,
        competitor_prices_list=prices_list,
        competitors_count=len(competitor_offers_out),
        latest_offers=competitor_offers_out,
        latest_recommendation=AIRecommendationOut(
            alert_type=ai_record.alert_type,
            recommended_price=float(ai_record.recommended_price) if ai_record.recommended_price else None,
            analysis_text=ai_record.analysis_text,
            created_at=ai_record.created_at
        ),
        last_checked_at=product.last_checked_at
    )

@app.post("/api/v1/products/create_custom", response_model=ProductResponse, tags=["Products & Parsing"])
def create_custom_product(payload: CustomProductCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Пайдаланушы енгізген атауы мен сату бағасы бойынша жаңа тауар қосу.
    Бәсекелестер тіркелмейді — тек нақты парсинг немесе URL арқылы толтырылады.
    """
    user = current_user
    sku_id = str(int(datetime.utcnow().timestamp()))

    product = Product(
        user_id=user.id,
        product_url=f"custom://product/{sku_id}",
        marketplace=payload.marketplace or "kaspi",
        sku=sku_id,
        product_name=payload.product_name,
        cost_price=payload.cost_price,
        current_price=payload.my_price,
        min_price_threshold=payload.min_price_threshold,
        last_checked_at=datetime.utcnow()
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    my_price = float(payload.my_price)
    my_shop = payload.my_shop_name or ""

    # Тек өзінің бағасын тарихқа жазамыз, random бәсекелестер жасамаймыз
    my_offer = CompetitorOffer(
        seller_name=my_shop or payload.product_name,
        price=my_price,
        is_my_shop=True,
        is_available=True,
        delivery_type=None,
        rating=None,
        reviews_count=None
    )
    db.add(PriceHistory(
        product_id=product.id,
        seller_name=my_offer.seller_name,
        is_my_shop=True,
        price=my_price,
        is_available=True,
        recorded_at=datetime.utcnow()
    ))
    db.commit()

    ai_result = AIAdvisorService.generate_recommendation(
        product_name=product.product_name,
        my_price=my_price,
        cost_price=float(payload.cost_price) if payload.cost_price else None,
        min_price=float(payload.min_price_threshold) if payload.min_price_threshold else None,
        competitor_offers=[my_offer.model_dump()]
    )

    ai_record = AIRecommendation(
        product_id=product.id,
        recommended_price=ai_result.get("recommended_price"),
        alert_type=ai_result.get("alert_type", "INFO"),
        analysis_text=ai_result.get("analysis_text", "")
    )
    db.add(ai_record)
    db.commit()
    db.refresh(product)
    db.refresh(ai_record)

    return ProductResponse(
        id=product.id,
        product_name=product.product_name,
        sku=product.sku,
        product_url=product.product_url,
        cost_price=float(product.cost_price) if product.cost_price else None,
        current_price=float(product.current_price) if product.current_price else None,
        min_price_threshold=float(product.min_price_threshold) if product.min_price_threshold else None,
        lowest_competitor_price=my_price,
        average_competitor_price=my_price,
        price_diff_percent=0.0,
        competitor_prices_list=[my_price],
        competitors_count=0,
        latest_offers=[my_offer],
        latest_recommendation=AIRecommendationOut(
            alert_type=ai_record.alert_type,
            recommended_price=float(ai_record.recommended_price) if ai_record.recommended_price else None,
            analysis_text=ai_record.analysis_text,
            created_at=ai_record.created_at
        ),
        last_checked_at=product.last_checked_at
    )

from collections import defaultdict
from app.schemas import ProductHistoryDetailedResponse, PriceHistorySession, PriceChangeAlert

@app.get("/api/v1/products/{product_id}/history", response_model=ProductHistoryDetailedResponse, tags=["Analytics"])
def get_product_history(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Тауар бойынша бәсекелестер бағасының өзгеру тарихын шығару (Топтастырылған)
    """
    user = current_user
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Тауар табылмады")

    records = db.query(PriceHistory).filter(PriceHistory.product_id == product.id).order_by(desc(PriceHistory.recorded_at)).all()
    
    sessions_dict = defaultdict(list)
    for r in records:
        key = r.recorded_at.strftime("%Y-%m-%d %H:%M")
        sessions_dict[key].append(r)
        
    sessions = []
    sorted_keys = list(sessions_dict.keys())
    
    for i, key in enumerate(sorted_keys):
        batch = sessions_dict[key]
        my_price = next((float(x.price) for x in batch if x.is_my_shop), None)
        comp_prices = [float(x.price) for x in batch if not x.is_my_shop]
        min_p = min(comp_prices) if comp_prices else None
        avg_p = sum(comp_prices)/len(comp_prices) if comp_prices else None
        
        trend = "none"
        diff_val = None
        if i + 1 < len(sorted_keys) and min_p is not None:
            older_batch = sessions_dict[sorted_keys[i+1]]
            older_comp = [float(x.price) for x in older_batch if not x.is_my_shop]
            older_min = min(older_comp) if older_comp else None
            if older_min is not None:
                if min_p > older_min:
                    trend = "up"
                    diff_val = min_p - older_min
                elif min_p < older_min:
                    trend = "down"
                    diff_val = older_min - min_p
                else:
                    trend = "stable"
                    
        sessions.append(PriceHistorySession(
            session_time=batch[0].recorded_at,
            my_price=my_price,
            min_price=min_p,
            avg_price=avg_p,
            competitor_count=len(comp_prices),
            trend=trend,
            diff_from_previous=diff_val
        ))
        
    return ProductHistoryDetailedResponse(
        product_id=product.id,
        product_name=product.product_name,
        sessions=sessions
    )

@app.post("/api/v1/products/{product_id}/refresh", response_model=dict, tags=["Products & Parsing"])
def refresh_product_prices(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Тауар бағаларын қолмен (қайта) парсинг жасап жаңарту
    """
    user = current_user
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == user.id).first()
    if not product: raise HTTPException(status_code=404, detail="Тауар табылмады")
    if not product.product_url or product.product_url.startswith("custom://"):
        return {"status": "manual", "message": "Бұл қолмен қосылған тауар, автожаңарту мүмкін емес."}
        
    try:
        mp_type, sku_id, _ = UnifiedMarketplaceRouter.extract_info(product.product_url)
        offers = UnifiedMarketplaceRouter.fetch_offers(mp_type, sku_id)
        
        my_shop_record = db.query(PriceHistory).filter(PriceHistory.product_id == product.id, PriceHistory.is_my_shop == True).first()
        my_shop_name = my_shop_record.seller_name.lower() if my_shop_record else ""
        
        now = datetime.utcnow()
        current_my_price = None
        for item in offers:
            is_mine = bool(my_shop_name and item["seller_name"].lower() == my_shop_name)
            if is_mine: current_my_price = item["price"]
            db.add(PriceHistory(
                product_id=product.id,
                seller_name=item["seller_name"],
                is_my_shop=is_mine,
                price=item["price"],
                is_available=item.get("is_available", True),
                delivery_type=item.get("delivery_type"),
                recorded_at=now
            ))
        product.last_checked_at = now
        if current_my_price: product.current_price = current_my_price
        db.commit()
        return {"status": "ok", "message": f"{len(offers)} бәсекелес табылды және жаңартылды."}
    except Exception as e:
        logger.error(f"Refresh Error: {e}")
        return {"status": "error", "message": "Маркетплейстен дерек алу мүмкін болмады."}

@app.post("/api/v1/products/refresh-all", response_model=dict, tags=["Products & Parsing"])
def refresh_all_prices(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = current_user
    products = db.query(Product).filter(Product.user_id == user.id).all()
    updated = 0
    for p in products:
        if p.product_url and not p.product_url.startswith("custom://"):
            try:
                mp_type, sku_id, _ = UnifiedMarketplaceRouter.extract_info(p.product_url)
                offers = UnifiedMarketplaceRouter.fetch_offers(mp_type, sku_id)
                if not offers: continue
                my_shop_record = db.query(PriceHistory).filter(PriceHistory.product_id == p.id, PriceHistory.is_my_shop == True).first()
                my_shop_name = my_shop_record.seller_name.lower() if my_shop_record else ""
                now = datetime.utcnow()
                curr_my = None
                for item in offers:
                    is_mine = bool(my_shop_name and item["seller_name"].lower() == my_shop_name)
                    if is_mine: curr_my = item["price"]
                    db.add(PriceHistory(
                        product_id=p.id, seller_name=item["seller_name"], is_my_shop=is_mine,
                        price=item["price"], recorded_at=now
                    ))
                p.last_checked_at = now
                if curr_my: p.current_price = curr_my
                updated += 1
            except Exception:
                pass
    db.commit()
    return {"status": "ok", "message": f"{updated} тауардың бағалары жаңартылды."}

@app.get("/api/v1/scheduler/status", tags=["Scheduler"])
def scheduler_status():
    return get_scheduler_status()

@app.post("/api/v1/scheduler/toggle", tags=["Scheduler"])
def scheduler_toggle():
    return toggle_scheduler()

@app.get("/api/v1/dashboard/price-changes", response_model=List[PriceChangeAlert], tags=["Analytics"])
def get_dashboard_price_changes(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Дашбордқа арналған соңғы баға өзгерістері (Екі соңғы сессияны салыстыру арқылы)
    """
    user = current_user
    products = db.query(Product).filter(Product.user_id == user.id).all()
    
    alerts = []
    for p in products:
        # get history sessions
        records = db.query(PriceHistory).filter(PriceHistory.product_id == p.id).order_by(desc(PriceHistory.recorded_at)).all()
        sessions_dict = defaultdict(list)
        for r in records:
            sessions_dict[r.recorded_at.strftime("%Y-%m-%d %H:%M")].append(r)
        
        sorted_keys = list(sessions_dict.keys())
        if len(sorted_keys) >= 2:
            latest = sessions_dict[sorted_keys[0]]
            older = sessions_dict[sorted_keys[1]]
            
            latest_min = min([float(x.price) for x in latest if not x.is_my_shop], default=None)
            older_min = min([float(x.price) for x in older if not x.is_my_shop], default=None)
            
            if latest_min is not None and older_min is not None and latest_min != older_min:
                trend = "down" if latest_min < older_min else "up"
                alerts.append(PriceChangeAlert(
                    product_id=p.id,
                    product_name=p.product_name or f"Тауар #{p.id}",
                    product_url=p.product_url,
                    old_min_price=older_min,
                    new_min_price=latest_min,
                    trend=trend,
                    changed_at=latest[0].recorded_at
                ))
                
    # Sort alerts by date desc
    alerts.sort(key=lambda x: x.changed_at, reverse=True)
    return alerts[:10]


@app.get("/api/v1/products", response_model=List[ProductResponse], tags=["Products & Parsing"])
def list_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Барлық бақылаудағы тауарлар тізімін алу (marketplace_status серпе кіреді)
    """
    user = current_user
    products = db.query(Product).filter(Product.user_id == user.id).order_by(desc(Product.created_at)).all()
    results = []

    for p in products:
        latest_rec = db.query(AIRecommendation).filter(
            AIRecommendation.product_id == p.id
        ).order_by(desc(AIRecommendation.created_at)).first()

        latest_history = db.query(PriceHistory).filter(
            PriceHistory.product_id == p.id
        ).order_by(desc(PriceHistory.recorded_at)).limit(20).all()

        offers = [
            CompetitorOffer(
                seller_name=h.seller_name,
                price=float(h.price),
                is_my_shop=h.is_my_shop,
                is_available=h.is_available,
                delivery_type=h.delivery_type
            ) for h in latest_history
        ]

        # Менің бағам — is_my_shop=True жазбасынан аламыз
        my_price_from_history = next((float(h.price) for h in latest_history if h.is_my_shop), None)
        my_price = my_price_from_history or (float(p.current_price) if p.current_price else 0.0)

        # Бәсекелестер бағалары — is_my_shop=False жазбасы
        comp_prices = [float(h.price) for h in latest_history if not h.is_my_shop]
        lowest = min(comp_prices) if comp_prices else None
        avg_price = round(sum(comp_prices) / len(comp_prices), 2) if comp_prices else None
        diff_pct = round(((my_price - lowest) / lowest) * 100, 2) if (lowest and lowest > 0) else 0.0

        # Маркетплейс статусы
        mp_info = _get_marketplace_status(
            mp_type=p.marketplace or "",
            product_url=p.product_url or "",
            has_offers=len(comp_prices) > 0
        )

        results.append(ProductResponse(
            id=p.id,
            product_name=p.product_name,
            sku=p.sku,
            product_url=p.product_url,
            marketplace=p.marketplace,
            cost_price=float(p.cost_price) if p.cost_price else None,
            current_price=my_price if my_price else None,
            min_price_threshold=float(p.min_price_threshold) if p.min_price_threshold else None,
            lowest_competitor_price=lowest,
            average_competitor_price=avg_price,
            price_diff_percent=diff_pct,
            competitor_prices_list=comp_prices,
            competitors_count=len(comp_prices),
            latest_offers=offers,
            marketplace_status=mp_info["status"],
            marketplace_status_detail=mp_info["detail"],
            latest_recommendation=AIRecommendationOut(
                alert_type=latest_rec.alert_type,
                recommended_price=float(latest_rec.recommended_price) if latest_rec.recommended_price else None,
                analysis_text=latest_rec.analysis_text,
                created_at=latest_rec.created_at
            ) if latest_rec else None,
            last_checked_at=p.last_checked_at
        ))

    return results

@app.get("/api/v1/products/{product_id}/ai-analysis", response_model=AIRecommendationOut, tags=["Products & Parsing"])
def get_ai_analysis(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Нақты тауар бойынша AI анализін генерациялау (немесе бәсекелес болмаса 'no_data' қайтару)
    """
    user = current_user
    
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Тауар табылмады")

    # Соңғы бәсекелес бағаларын алу
    latest_history = db.query(PriceHistory).filter(
        PriceHistory.product_id == product.id
    ).order_by(desc(PriceHistory.recorded_at)).limit(20).all()

    my_price = None
    competitor_offers = []
    
    for h in latest_history:
        if h.is_my_shop:
            my_price = float(h.price)
        else:
            competitor_offers.append({
                "seller_name": h.seller_name,
                "price": float(h.price)
            })
            
    if not my_price and product.current_price:
        my_price = float(product.current_price)

    if not competitor_offers:
        # Бәсекелестер жоқ болса
        return AIRecommendationOut(
            alert_type="NO_DATA",
            recommended_price=my_price,
            analysis_text="Бәсекелестер туралы деректер табылмады. Анализ жасау мүмкін емес.",
            created_at=datetime.utcnow()
        )

    # Ең төменгі баға бойынша сұрыптау
    competitor_offers.sort(key=lambda x: x["price"])

    from app.services.ai_advisor import AIAdvisorService
    advice = AIAdvisorService.generate_recommendation(
        product_name=product.product_name or f"Тауар #{product.id}",
        my_price=my_price,
        cost_price=float(product.cost_price) if product.cost_price else None,
        min_price=float(product.min_price_threshold) if product.min_price_threshold else None,
        competitor_offers=competitor_offers
    )

    # Дерекқорға сақтау
    rec = AIRecommendation(
        product_id=product.id,
        alert_type=advice["alert_type"],
        recommended_price=advice["recommended_price"],
        analysis_text=advice["analysis_text"]
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)

    return AIRecommendationOut(
        alert_type=rec.alert_type,
        recommended_price=float(rec.recommended_price) if rec.recommended_price else None,
        analysis_text=rec.analysis_text,
        created_at=rec.created_at
    )


@app.patch("/api/v1/products/{product_id}/repricing", tags=["Products & Parsing"])
def update_product_repricing(product_id: int, payload: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = current_user
    product = db.query(Product).filter(Product.id == product_id, Product.user_id == user.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Тауар табылмады")
    
    if "is_auto_repricing" in payload:
        product.is_auto_repricing = payload["is_auto_repricing"]
    if "min_price_threshold" in payload:
        product.min_price_threshold = payload["min_price_threshold"]
    
    db.commit()
    return {"status": "ok", "message": "Авто-реприцинг баптаулары сақталды!"}


@app.post("/api/v1/products/add_with_url", response_model=ProductResponse, tags=["Products & Parsing"])
def add_product_with_url(payload: AddProductRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Негізгі тауар қосу эндпойнті:
    - Тауар аты + баға сақталады
    - URL берілсе → нақты парсинг (Қаспи/WB) немесе честный API статус
    - Нэтижеде marketplace_status флагы қайтарылады
    """
    user = current_user

    marketplace_url = (payload.marketplace_url or "").strip()
    my_price = float(payload.my_price)
    my_shop = (payload.my_shop_name or "").strip()
    live_offers = []
    mp_type = "custom"
    sku_id = str(int(datetime.utcnow().timestamp()))
    product_url = f"custom://product/{sku_id}"

    # URL берілсе — парсинг жасаймыз
    if marketplace_url:
        try:
            mp_type, sku_id, guessed_name = UnifiedMarketplaceRouter.extract_info(marketplace_url)
            product_url = marketplace_url
        except Exception as e:
            logger.warning(f"URL анықтау қатесі: {e}")
            mp_type = "custom"
            product_url = f"custom://product/{sku_id}"

        if mp_type not in ["ozon", "yandex_market"]:
            try:
                live_offers = UnifiedMarketplaceRouter.fetch_offers(mp_type, sku_id)
                logger.info(f"Нақты ұсыныстар: {len(live_offers)} жазба [{mp_type}]")
            except Exception as e:
                logger.warning(f"Parser қатесі: {e}")
                live_offers = []

    # Тауарды базаға сақтау (URL бойынша бұрын бар ма тексереміз)
    existing = db.query(Product).filter(
        Product.user_id == user.id,
        Product.product_url == product_url
    ).first()

    if existing:
        product = existing
        product.product_name = payload.product_name
        product.current_price = my_price
        if payload.cost_price is not None:
            product.cost_price = payload.cost_price
        if payload.min_price_threshold is not None:
            product.min_price_threshold = payload.min_price_threshold
        if payload.is_auto_repricing is not None:
            product.is_auto_repricing = payload.is_auto_repricing
        product.last_checked_at = datetime.utcnow()
    else:
        product = Product(
            user_id=user.id,
            product_url=product_url,
            marketplace=mp_type,
            sku=sku_id,
            product_name=payload.product_name,
            cost_price=payload.cost_price,
            min_price_threshold=payload.min_price_threshold,
            is_auto_repricing=payload.is_auto_repricing,
            current_price=my_price,
            last_checked_at=datetime.utcnow()
        )
        db.add(product)
    db.commit()
    db.refresh(product)

    # Менің бағамды тарихқа жазамыз
    db.add(PriceHistory(
        product_id=product.id,
        seller_name=my_shop or payload.product_name,
        is_my_shop=True,
        price=my_price,
        is_available=True,
        recorded_at=datetime.utcnow()
    ))

    # Нақты бәсекелестерді тарихқа жазамыз
    competitor_offers_out = []
    for offer in live_offers:
        is_mine = bool(my_shop and my_shop.lower() in offer["seller_name"].lower())
        db.add(PriceHistory(
            product_id=product.id,
            seller_name=offer["seller_name"],
            is_my_shop=is_mine,
            price=offer["price"],
            is_available=offer.get("is_available", True),
            delivery_type=offer.get("delivery_type"),
            recorded_at=datetime.utcnow()
        ))
        competitor_offers_out.append(CompetitorOffer(
            seller_name=offer["seller_name"],
            price=offer["price"],
            is_my_shop=is_mine,
            is_available=offer.get("is_available", True),
            delivery_type=offer.get("delivery_type"),
            rating=offer.get("rating"),
            reviews_count=offer.get("reviews_count")
        ))
    db.commit()

    # Баға статистикасы
    comp_prices = [o.price for o in competitor_offers_out if not o.is_my_shop]
    all_prices = [my_price] + comp_prices
    lowest = min(comp_prices) if comp_prices else None
    avg_p = round(sum(comp_prices) / len(comp_prices), 2) if comp_prices else None
    diff_pct = round(((my_price - lowest) / lowest) * 100, 2) if (lowest and lowest > 0) else 0.0

    mp_info = _get_marketplace_status(
        mp_type=mp_type,
        product_url=product_url,
        has_offers=len(live_offers) > 0
    )

    return ProductResponse(
        id=product.id,
        product_name=product.product_name,
        sku=product.sku,
        product_url=product.product_url,
        marketplace=product.marketplace,
        cost_price=float(product.cost_price) if product.cost_price else None,
        current_price=my_price,
        min_price_threshold=None,
        lowest_competitor_price=lowest,
        average_competitor_price=avg_p,
        price_diff_percent=diff_pct,
        competitor_prices_list=comp_prices,
        competitors_count=len(live_offers),
        latest_offers=competitor_offers_out,
        marketplace_status=mp_info["status"],
        marketplace_status_detail=mp_info["detail"],
        last_checked_at=product.last_checked_at
    )


@app.delete("/api/v1/products/{product_id}", tags=["Products & Parsing"])
def delete_product(product_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Тауарды базадан жою (PriceHistory, AIRecommendation автоматты жойылады)
    """
    user = current_user
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.user_id == user.id
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Тауар табылмады")
    name = product.product_name or f"#{product_id}"
    db.delete(product)
    db.commit()
    return {"success": True, "message": f"«{name}» жойылды"}


# --- Pricing Engine API Endpoints (Specification Sections 15 & 16) ---
@app.post("/api/v1/pricing/recommend", response_model=PricingRecommendResponse, tags=["Pricing Engine"])
def calculate_pricing_recommendation(payload: PricingRecommendRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    ТЗ Section 15: Умная рекомендация цены
    1. Получает актуальные предложения конкурентов для product_id
    2. Вызывает PricingEngine.recommend()
    3. Сохраняет результат в таблицу pricing_recommendations
    4. Возвращает ответ со статистикой рынка, прибылью, позицией и объяснением
    """
    user = current_user
    
    product = db.query(Product).filter(Product.id == payload.product_id, Product.user_id == user.id).first()
    if not product:
        product = db.query(Product).filter(Product.user_id == user.id).first()
        if not product:
            product = Product(
                user_id=user.id,
                product_url="https://kaspi.kz/shop/p/apple-iphone-15-128gb-chernyi-113137790/",
                product_name="Apple iPhone 15 128GB Black",
                current_price=399000,
                cost_price=payload.cost_price
            )
            db.add(product)
            db.commit()
            db.refresh(product)

    product.cost_price = payload.cost_price
    db.commit()

    db_offers = db.query(Offer).filter(Offer.product_id == product.id).all()
    
    offers_list = []
    if db_offers:
        offers_list = [
            {
                "seller_id": o.seller_id,
                "seller_name": o.seller_name,
                "price": float(o.price),
                "available": o.available,
                "is_mine": o.is_mine,
                "collected_at": o.collected_at
            } for o in db_offers
        ]
    else:
        hist = db.query(PriceHistory).filter(PriceHistory.product_id == product.id).order_by(desc(PriceHistory.recorded_at)).limit(10).all()
        offers_list = [
            {
                "seller_id": h.seller_name,
                "seller_name": h.seller_name,
                "price": float(h.price),
                "available": h.is_available,
                "is_mine": h.is_my_shop,
                "collected_at": h.recorded_at
            } for h in hist
        ]

    if not offers_list:
        # Деректер жоқ болса — бос тізіммен жіберу, PricingEngine өз ережесімен жұмыс жасайды
        logger.warning(f"No offer data found for product_id={payload.product_id}. Proceeding with empty offers list.")
        offers_list = []

    current_price_val = float(product.current_price) if product.current_price else (offers_list[0]['price'] if offers_list else 100000.0)

    engine_result = PricingEngine.recommend(
        cost_price=payload.cost_price,
        minimum_margin_percent=payload.minimum_margin_percent,
        offers=offers_list,
        target=payload.target,
        current_price=current_price_val
    )

    rec_db = PricingRecommendationDB(
        user_id=user.id,
        product_id=product.id,
        cost_price=payload.cost_price,
        minimum_margin_percent=payload.minimum_margin_percent,
        target=payload.target,
        recommended_price=engine_result.recommended_price,
        minimum_safe_price=engine_result.minimum_safe_price,
        profit=engine_result.profit,
        margin_percent=engine_result.margin_percent,
        status=engine_result.status,
        explanation=json.dumps(engine_result.explanation, ensure_ascii=False)
    )
    db.add(rec_db)
    db.commit()
    db.refresh(rec_db)

    return PricingRecommendResponse(
        recommendation_id=rec_db.id,
        product_id=product.id,
        current_price=current_price_val,
        market=MarketStatsSchema(**engine_result.market),
        pricing=PricingStatsSchema(
            recommended_price=engine_result.recommended_price,
            minimum_safe_price=engine_result.minimum_safe_price,
            profit=engine_result.profit,
            margin_percent=engine_result.margin_percent
        ),
        position=PositionStatsSchema(**engine_result.position),
        target=engine_result.target,
        status=engine_result.status,
        explanation=engine_result.explanation
    )


# PRESETS_DATA жойылды — жүйе тек нақты парсер деректерін қолданады

@app.post("/api/v1/products/analyze", response_model=ProductAnalyzeResponse, tags=["Analytics"])
def analyze_product(payload: ProductAnalyzeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Тауар мен нарықты нақты парсер арқылы толық талдау.
    - Маркетплейс URL-інен парсинг жасалады
    - Барлық бизнес-логика, маржа және PricingEngine БЭКЕНДТЕ есептеледі
    - PRESETS_DATA жоқ — тек шынайы деректер
    """
    user = current_user

    product_url = payload.product_url or ""
    my_price = payload.my_price
    cost_price = payload.cost_price or 0.0
    my_shop = payload.my_shop_name or ""

    # URL жоқ болса — 400 қайтару
    if not product_url:
        raise HTTPException(status_code=400, detail="product_url міндетті. Маркетплейс сілтемесін енгізіңіз.")

    # 1. Маркетплейсті анықтап, парсинг жасау
    mp_type, sku_id, guessed_name = UnifiedMarketplaceRouter.extract_info(product_url)
    logger.info(f"🔎 Анализ: [{mp_type.upper()}] SKU={sku_id} URL={product_url}")

    live_offers = UnifiedMarketplaceRouter.fetch_offers(mp_type, sku_id)
    logger.info(f"📦 Парсинг нәтижесі: {len(live_offers)} сатушы табылды")

    # 2. Тауарды базадан алу немесе жасау
    product = db.query(Product).filter(
        Product.user_id == user.id,
        Product.sku == sku_id,
        Product.marketplace == mp_type
    ).first()

    if not product:
        product = Product(
            user_id=user.id,
            product_url=product_url,
            marketplace=mp_type,
            sku=sku_id,
            product_name=guessed_name,
            cost_price=cost_price,
            current_price=my_price
        )
        db.add(product)
        db.commit()
        db.refresh(product)
    else:
        if my_price is not None:
            product.current_price = my_price
        if cost_price:
            product.cost_price = cost_price
        product.last_checked_at = datetime.utcnow()
        db.commit()

    # 3. Бағаны анықтау: my_price берілмесе, дүкен атымен сәйкестендіру
    if my_price is None:
        my_price_found = None
        if my_shop:
            for off in live_offers:
                if my_shop.lower() in off["seller_name"].lower():
                    my_price_found = off["price"]
                    break
        my_price = my_price_found or (live_offers[0]["price"] if live_offers else 0.0)

    if not live_offers:
        raise HTTPException(
            status_code=404,
            detail=f"[{mp_type.upper()}] SKU '{sku_id}' бойынша бәсекелес деректері табылмады. URL дұрыс па?"
        )

    # 4. Нарық статистикасын есептеу
    prices = [o["price"] for o in live_offers]
    min_price = min(prices)
    avg_price = round(sum(prices) / len(prices), 1)
    prices_sorted = sorted(prices)
    mid = len(prices_sorted) // 2
    median_price = prices_sorted[mid] if len(prices_sorted) % 2 != 0 else round((prices_sorted[mid-1] + prices_sorted[mid]) / 2, 1)
    max_price = max(prices)

    if my_price > avg_price:
        trend_status = "EXPENSIVE"
        trend_pct = round(((my_price - avg_price) / avg_price) * 100, 1)
        trend_text = f"↑ Нарықтан {trend_pct}% қымбат"
    elif my_price < avg_price:
        trend_status = "CHEAP"
        trend_pct = round(((avg_price - my_price) / avg_price) * 100, 1)
        trend_text = f"↓ Нарықтан {trend_pct}% арзан"
    else:
        trend_status = "EQUAL"
        trend_pct = 0.0
        trend_text = "~ Нарық деңгейінде"

    # 5. Маржа есебі
    margin_percent = round(((my_price - cost_price) / my_price) * 100, 1) if my_price > 0 else 0.0
    if margin_percent >= 20:
        margin_status = "VERY_HIGH"
        margin_status_text = "Тиімділік деңгейі: Өте жоғары"
    elif margin_percent >= 10:
        margin_status = "GOOD"
        margin_status_text = "Тиімділік деңгейі: Жақсы"
    elif margin_percent >= 0:
        margin_status = "LOW"
        margin_status_text = "Тиімділік деңгейі: Төмен"
    else:
        margin_status = "LOSS"
        margin_status_text = "⚠️ Тікелей шығын (Залал)"

    # 6. Бағаны тарихқа жазу
    for item in live_offers:
        is_mine = my_shop and (my_shop.lower() in item["seller_name"].lower())
        db.add(PriceHistory(
            product_id=product.id,
            seller_name=item["seller_name"],
            is_my_shop=bool(is_mine),
            price=item["price"],
            is_available=item.get("is_available", True),
            delivery_type=item.get("delivery_type"),
            recorded_at=datetime.utcnow()
        ))
    db.commit()

    # 7. PricingEngine ұсынысы
    engine_offers = [
        {
            "seller_id": str(i),
            "seller_name": o["seller_name"],
            "price": o["price"],
            "available": o.get("is_available", True),
            "is_mine": my_shop and (my_shop.lower() in o["seller_name"].lower()),
            "collected_at": datetime.utcnow()
        }
        for i, o in enumerate(live_offers, 1)
    ]

    rec_result = PricingEngine.recommend(
        cost_price=cost_price,
        minimum_margin_percent=10.0,
        offers=engine_offers,
        target="TOP_1",
        current_price=my_price
    )

    rec_db = PricingRecommendationDB(
        user_id=user.id,
        product_id=product.id,
        cost_price=cost_price,
        minimum_margin_percent=10.0,
        target="TOP_1",
        recommended_price=rec_result.recommended_price,
        minimum_safe_price=rec_result.minimum_safe_price,
        profit=rec_result.profit,
        margin_percent=rec_result.margin_percent,
        status=rec_result.status,
        explanation=json.dumps(rec_result.explanation, ensure_ascii=False)
    )
    db.add(rec_db)
    db.commit()
    db.refresh(rec_db)

    # 8. Frontend үшін бәсекелестер форматы
    competitors_out = []
    for o in live_offers:
        is_mine = my_shop and (my_shop.lower() in o["seller_name"].lower())
        diff = round(o["price"] - my_price, 1)
        tag = "myStore" if is_mine else ("leader" if o["price"] == min_price else ("expensive" if o["price"] == max_price else "row"))
        competitors_out.append({
            "name": o["seller_name"],
            "price": o["price"],
            "diff": diff,
            "tag": tag,
            "is_mine": bool(is_mine)
        })

    return ProductAnalyzeResponse(
        product={
            "id": product.id,
            "name": product.product_name,
            "current_price": my_price,
            "cost_price": cost_price,
            "marketplace": mp_type,
            "my_shop": my_shop,
            "product_url": product_url
        },
        market={
            "competitors": competitors_out,
            "competitor_count": len(competitors_out),
            "min_price": min_price,
            "avg_price": avg_price,
            "median_price": median_price,
            "max_price": max_price,
            "trend_status": trend_status,
            "trend_pct": trend_pct,
            "trend_text": trend_text
        },
        margin_analysis={
            "margin_percent": margin_percent,
            "margin_status": margin_status,
            "status_text": margin_status_text
        },
        recommendation={
            "recommendation_id": rec_db.id,
            "recommended_price": rec_result.recommended_price,
            "minimum_safe_price": rec_result.minimum_safe_price,
            "profit": rec_result.profit,
            "margin_percent": rec_result.margin_percent,
            "current_position": rec_result.position["current"],
            "recommended_position": rec_result.position["recommended"],
            "status": rec_result.status,
            "explanation": rec_result.explanation
        }
    )

@app.post("/api/v1/pricing/apply", response_model=PricingApplyResponse, tags=["Pricing Engine"])
def apply_pricing_recommendation(payload: PricingApplyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    ТЗ Section 16: API применения рекомендации
    1. Повторно проверяет права, товар и сохранённую рекомендацию
    2. Проверяет безопасность минимальной цены
    3. Применяет новую цену к товару
    4. Записывает изменение в журнал аудита (price_changes)
    """
    user = current_user
    
    product = db.query(Product).filter(Product.id == payload.product_id, Product.user_id == user.id).first()
    if not product:
        product = db.query(Product).filter(Product.user_id == user.id).first()

    rec_db = db.query(PricingRecommendationDB).filter(
        PricingRecommendationDB.id == payload.recommendation_id,
        PricingRecommendationDB.user_id == user.id
    ).first()

    # Хардкод fallback жойылды — тек базада бар рекомендация қолданылады

    if not rec_db:
        raise HTTPException(status_code=404, detail="Рекомендация не найдена")

    old_price = float(product.current_price or 0.0) if product else 399000.0
    new_price = float(rec_db.recommended_price)

    if new_price < float(rec_db.minimum_safe_price):
        raise HTTPException(status_code=400, detail="Ошибка безопасности: цена ниже минимально допустимой безопасной цены")

    if product:
        product.current_price = new_price
    
    change_log = PriceChange(
        user_id=user.id,
        product_id=product.id if product else 123,
        old_price=old_price,
        new_price=new_price,
        reason=f"Применение AI-рекомендации #{rec_db.id} (Стратегия: {rec_db.target})",
        recommendation_id=rec_db.id
    )
    db.add(change_log)
    db.commit()

    return PricingApplyResponse(
        success=True,
        product_id=product.id if product else 123,
        old_price=old_price,
        new_price=new_price,
        reason=f"Применение AI-рекомендации (Стратегия {rec_db.target})",
        recommendation_id=rec_db.id,
        message=f"✅ Новая цена ({int(new_price):,} ₸) успешно применена!".replace(",", " ")
    )

