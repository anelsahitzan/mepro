from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Numeric, Boolean, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_id = Column(BigInteger, unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=True)
    full_name = Column(String(255), nullable=True)
    tariff_plan = Column(String(50), default="free", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    products = relationship("Product", back_populates="user", cascade="all, delete-orphan")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_url = Column(Text, nullable=False)
    marketplace = Column(String(50), default="kaspi", nullable=False)
    sku = Column(String(100), index=True, nullable=True)
    product_name = Column(String(255), nullable=True)
    cost_price = Column(Numeric(10, 2), nullable=True)
    current_price = Column(Numeric(10, 2), nullable=True)
    min_price_threshold = Column(Numeric(10, 2), nullable=True)
    monitoring_interval_hours = Column(Integer, default=6, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_checked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="products")
    price_history = relationship("PriceHistory", back_populates="product", cascade="all, delete-orphan", order_by="desc(PriceHistory.recorded_at)")
    ai_recommendations = relationship("AIRecommendation", back_populates="product", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_name = Column(String(255), nullable=False)
    is_my_shop = Column(Boolean, default=False, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    is_available = Column(Boolean, default=True, nullable=False)
    delivery_type = Column(String(100), nullable=True)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)

    product = relationship("Product", back_populates="price_history")


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    recommended_price = Column(Numeric(10, 2), nullable=True)
    alert_type = Column(String(50), nullable=False)  # 'DUMPING_DETECTED', 'PRICE_DROP', 'OPPORTUNITY'
    analysis_text = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="ai_recommendations")


class Offer(Base):
    __tablename__ = "offers"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    seller_id = Column(String(100), nullable=True)
    seller_name = Column(String(255), nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    available = Column(Boolean, default=True, nullable=False)
    is_mine = Column(Boolean, default=False, nullable=False)
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)

    product = relationship("Product", backref="offers")


class PricingRecommendationDB(Base):
    __tablename__ = "pricing_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    cost_price = Column(Numeric(10, 2), nullable=False)
    minimum_margin_percent = Column(Numeric(5, 2), nullable=False)
    target = Column(String(50), nullable=False)  # 'TOP_1', 'BALANCED', 'MAX_MARGIN'
    recommended_price = Column(Numeric(10, 2), nullable=False)
    minimum_safe_price = Column(Numeric(10, 2), nullable=False)
    profit = Column(Numeric(10, 2), nullable=False)
    margin_percent = Column(Numeric(5, 2), nullable=False)
    status = Column(String(50), nullable=False)
    explanation = Column(Text, nullable=False)  # JSON formatted string
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", backref="recommendations_history")


class PriceChange(Base):
    __tablename__ = "price_changes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, index=True)
    old_price = Column(Numeric(10, 2), nullable=True)
    new_price = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(255), nullable=True)
    recommendation_id = Column(Integer, ForeignKey("pricing_recommendations.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", backref="price_change_logs")

