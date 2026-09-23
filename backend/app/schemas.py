from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

# Auth schemas
class UserCreate(BaseModel):
    full_name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserOut(BaseModel):
    id: int
    full_name: str
    email: str
    
    class Config:
        orm_mode = True
        from_attributes = True

# Request schemas
class ProductCreate(BaseModel):
    product_url: str = Field(..., description="Kaspi.kz тауар сілтемесі немесе ID")
    my_shop_name: str = Field(default="MyStore", description="Селлердің Kaspi-дегі дүкен атауы")
    cost_price: Optional[float] = Field(None, description="Тауардың өзіндік құны (маржа есептеу үшін)")
    min_price_threshold: Optional[float] = Field(None, description="Ең төменгі рұқсат етілген баға шегі")
    city_id: str = Field(default="750000000", description="Қала коды (750000000 - Алматы, 710000000 - Астана)")

class CustomProductCreate(BaseModel):
    product_name: str = Field(..., description="Тауар атауы")
    my_price: float = Field(..., description="Селлердің өз сату бағасы")
    cost_price: Optional[float] = Field(None, description="Өзіндік құны")
    min_price_threshold: Optional[float] = Field(None, description="Минималды баға шегі")
    is_auto_repricing: Optional[bool] = Field(False, description="Автоматты демпинг")
    marketplace: Optional[str] = Field(default="kaspi", description="Маркетплейс (kaspi, wb, ozon)")
    my_shop_name: Optional[str] = Field(default="Almaty Mobile", description="Дүкен атауы")

class AddProductRequest(BaseModel):
    """POST /api/v1/products/add_with_url үшін негізгі схема"""
    product_name: str = Field(..., description="Тауар атауы (міндетті)")
    my_price: float = Field(..., gt=0, description="Менің сату бағам (міндетті)")
    marketplace_url: Optional[str] = Field(None, description="Маркетплейс сілтемесі (міндетті емес) — бәсекелес бағасын алу үшін")
    cost_price: Optional[float] = Field(None, description="Өзіндік құны (міндетті емес)")
    min_price_threshold: Optional[float] = Field(None, description="Минималды баға шегі (міндетті емес)")
    is_auto_repricing: Optional[bool] = Field(False, description="Автоматты демпинг қосулы/өшірулі")
    my_shop_name: Optional[str] = Field(None, description="Дүкен атауы (міндетті емес)")

# Response schemas
class CompetitorOffer(BaseModel):
    seller_name: str
    price: float
    is_my_shop: bool
    is_available: bool
    delivery_type: Optional[str] = None
    rating: Optional[float] = None
    reviews_count: Optional[int] = None

class PriceHistoryItem(BaseModel):
    id: int
    seller_name: str
    is_my_shop: bool
    price: float
    is_available: bool
    delivery_type: Optional[str]
    recorded_at: datetime

    class Config:
        from_attributes = True

class AIRecommendationOut(BaseModel):
    alert_type: str
    recommended_price: Optional[float]
    analysis_text: str
    created_at: datetime

    class Config:
        from_attributes = True

class ProductResponse(BaseModel):
    id: int
    product_name: Optional[str]
    sku: Optional[str]
    product_url: str
    marketplace: Optional[str] = None
    cost_price: Optional[float]
    current_price: Optional[float]
    min_price_threshold: Optional[float]
    is_auto_repricing: bool = False
    lowest_competitor_price: Optional[float] = None
    average_competitor_price: Optional[float] = None
    price_diff_percent: Optional[float] = None
    competitor_prices_list: List[float] = []
    competitors_count: int = 0
    latest_offers: List[CompetitorOffer] = []
    latest_recommendation: Optional[AIRecommendationOut] = None
    marketplace_status: Optional[str] = None          # ok | no_data | api_required | manual
    marketplace_status_detail: Optional[str] = None   # Адам ақпарат
    last_checked_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PriceHistorySession(BaseModel):
    session_time: datetime
    my_price: Optional[float]
    min_price: Optional[float]
    avg_price: Optional[float]
    competitor_count: int
    trend: str # 'up', 'down', 'stable', 'none'
    diff_from_previous: Optional[float]

class ProductHistoryDetailedResponse(BaseModel):
    product_id: int
    product_name: Optional[str]
    sessions: List[PriceHistorySession]

class PriceChangeAlert(BaseModel):
    product_id: int
    product_name: str
    product_url: Optional[str]
    old_min_price: float
    new_min_price: float
    trend: str
    changed_at: datetime

# --- Pricing Engine Schemas (Specification Sections 15 & 16) ---
class PricingRecommendRequest(BaseModel):
    product_id: int = Field(..., description="Идентификатор товара")
    cost_price: float = Field(..., description="Себестоимость товара (> 0)")
    minimum_margin_percent: float = Field(default=10.0, description="Минимально допустимая маржа в % (0..90)")
    target: str = Field(default="TOP_1", description="Стратегия: TOP_1, BALANCED, MAX_MARGIN")

class MarketStatsSchema(BaseModel):
    min_price: float
    avg_price: float
    median_price: float
    max_price: float
    competitor_count: int

class PricingStatsSchema(BaseModel):
    recommended_price: float
    minimum_safe_price: float
    profit: float
    margin_percent: float

class PositionStatsSchema(BaseModel):
    current: int
    recommended: int

class PricingRecommendResponse(BaseModel):
    recommendation_id: int
    product_id: int
    current_price: float
    market: MarketStatsSchema
    pricing: PricingStatsSchema
    position: PositionStatsSchema
    target: str
    status: str
    explanation: List[str]

class PricingApplyRequest(BaseModel):
    product_id: int = Field(..., description="Идентификатор товара")
    recommendation_id: int = Field(..., description="Идентификатор сохранённой рекомендации")

class PricingApplyResponse(BaseModel):
    success: bool
    product_id: int
    old_price: float
    new_price: float
    reason: str
    recommendation_id: int
    message: str

# --- Full Product Analyze Schemas ---
class ProductAnalyzeRequest(BaseModel):
    preset_key: Optional[str] = Field(None, description="Пресет кілті (жойылды)")
    product_url: Optional[str] = Field(None, description="Тауар сілтемесі")
    my_shop_name: Optional[str] = Field(default=None, description="Дүкен атауы")
    my_price: Optional[float] = Field(None, description="Сату бағаңыз")
    cost_price: Optional[float] = Field(default=None, description="Өзіндік құны")

class ProductAnalyzeResponse(BaseModel):
    product: dict
    market: dict
    margin_analysis: dict
    recommendation: dict

