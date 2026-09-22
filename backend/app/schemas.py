from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

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
    marketplace: Optional[str] = Field(default="kaspi", description="Маркетплейс (kaspi, wb, ozon)")
    my_shop_name: Optional[str] = Field(default="Almaty Mobile", description="Дүкен атауы")

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
    cost_price: Optional[float]
    current_price: Optional[float]
    min_price_threshold: Optional[float]
    lowest_competitor_price: Optional[float] = None
    average_competitor_price: Optional[float] = None
    price_diff_percent: Optional[float] = None
    competitor_prices_list: List[float] = []
    competitors_count: int = 0
    latest_offers: List[CompetitorOffer] = []
    latest_recommendation: Optional[AIRecommendationOut] = None
    last_checked_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ProductHistoryResponse(BaseModel):
    product_id: int
    product_name: Optional[str]
    sku: Optional[str]
    history: List[PriceHistoryItem]


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
    preset_key: Optional[str] = Field(None, description="Пресет кілті (iphone, wildberries, ozon, samsung, airpods)")
    product_url: Optional[str] = Field(None, description="Тауар сілтемесі")
    my_shop_name: Optional[str] = Field(default="Almaty Mobile", description="Дүкен атауы")
    my_price: Optional[float] = Field(None, description="Сату бағаңыз")
    cost_price: Optional[float] = Field(default=340000.0, description="Өзіндік құны")

class ProductAnalyzeResponse(BaseModel):
    product: dict
    market: dict
    margin_analysis: dict
    recommendation: dict

