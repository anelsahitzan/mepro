import math
import statistics
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class PricingEngineResult:
    def __init__(
        self,
        status: str,
        target: str,
        cost_price: float,
        minimum_margin_percent: float,
        recommended_price: float,
        minimum_safe_price: float,
        profit: float,
        margin_percent: float,
        market: Dict[str, Any],
        position: Dict[str, Any],
        explanation: List[str]
    ):
        self.status = status
        self.target = target
        self.cost_price = cost_price
        self.minimum_margin_percent = minimum_margin_percent
        self.recommended_price = recommended_price
        self.minimum_safe_price = minimum_safe_price
        self.profit = profit
        self.margin_percent = margin_percent
        self.market = market
        self.position = position
        self.explanation = explanation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "target": self.target,
            "pricing": {
                "cost_price": self.cost_price,
                "minimum_margin_percent": self.minimum_margin_percent,
                "recommended_price": self.recommended_price,
                "minimum_safe_price": self.minimum_safe_price,
                "profit": self.profit,
                "margin_percent": self.margin_percent
            },
            "market": self.market,
            "position": self.position,
            "explanation": self.explanation
        }


class PricingEngine:
    """
    Чистый независимый доменный сервис расчёта рекомендаций цены (SellerAI Pricing Engine).
    Не имеет зависимостей от HTTP, FastAPI или прямых запросов к БД.
    """
    TTL_MINUTES = 30

    @classmethod
    def calculate_minimum_safe_price(cls, cost_price: float, minimum_margin_percent: float) -> float:
        """
        Формула: minimum_price = cost_price / (1 - minimum_margin / 100)
        Округление вверх до целого числа (₸).
        """
        if minimum_margin_percent >= 100.0:
            return float('inf')
        denom = 1.0 - (minimum_margin_percent / 100.0)
        if denom <= 0:
            return float('inf')
        val = cost_price / denom
        return float(math.ceil(val))

    @classmethod
    def filter_offers(cls, offers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Фильтрация предложений конкурентов:
        1. Исключение собственного магазина (is_mine == True)
        2. Исключение предложений без цены или с невалидной ценой <= 0
        3. Исключение предложений не в наличии (available == False)
        4. Дедупликация по продавцу (seller_name / seller_id)
        """
        valid_offers = []
        seen_sellers = set()

        for offer in offers:
            if offer.get("is_mine", False):
                continue
            if not offer.get("available", True):
                continue
            price = offer.get("price")
            if price is None or float(price) <= 0:
                continue

            seller_key = offer.get("seller_id") or offer.get("seller_name")
            if seller_key and seller_key in seen_sellers:
                continue
            if seller_key:
                seen_sellers.add(seller_key)

            valid_offers.append(offer)

        return valid_offers

    @classmethod
    def calculate_rank(cls, test_price: float, competitor_prices: List[float]) -> int:
        """Рассчитывает предполагаемое место (ранг) по цене на рынке"""
        all_prices = sorted([test_price] + competitor_prices)
        # 1-indexed position
        return all_prices.index(test_price) + 1

    @classmethod
    def recommend(
        cls,
        cost_price: float,
        minimum_margin_percent: float,
        offers: List[Dict[str, Any]],
        target: str = "TOP_1",
        current_price: Optional[float] = None
    ) -> PricingEngineResult:

        explanation: List[str] = []

        # 1. Валидация входных данных
        if cost_price <= 0 or minimum_margin_percent < 0 or minimum_margin_percent > 90 or target not in ["TOP_1", "BALANCED", "MAX_MARGIN"]:
            explanation.append("Некорректные входные параметры: себестоимость должна быть > 0, маржа от 0% до 90%.")
            return PricingEngineResult(
                status="INVALID_INPUT",
                target=target,
                cost_price=cost_price,
                minimum_margin_percent=minimum_margin_percent,
                recommended_price=current_price or cost_price,
                minimum_safe_price=cost_price,
                profit=0,
                margin_percent=0,
                market={"min_price": 0, "avg_price": 0, "median_price": 0, "max_price": 0, "competitor_count": 0},
                position={"current": 0, "recommended": 0},
                explanation=explanation
            )

        # 2. Формула минимальной безопасной цены
        minimum_safe_price = cls.calculate_minimum_safe_price(cost_price, minimum_margin_percent)

        # 3. Фильтрация бәсекелестер
        valid_offers = cls.filter_offers(offers)

        if not valid_offers:
            explanation.append("Конкуренты отсутствуют или нет активных предложений в наличии.")
            rec_price = max(current_price or minimum_safe_price, minimum_safe_price)
            profit = round(rec_price - cost_price, 2)
            margin_pct = round(((rec_price - cost_price) / rec_price) * 100.0, 2) if rec_price > 0 else 0
            return PricingEngineResult(
                status="NO_COMPETITORS",
                target=target,
                cost_price=cost_price,
                minimum_margin_percent=minimum_margin_percent,
                recommended_price=rec_price,
                minimum_safe_price=minimum_safe_price,
                profit=profit,
                margin_percent=margin_pct,
                market={"min_price": 0, "avg_price": 0, "median_price": 0, "max_price": 0, "competitor_count": 0},
                position={"current": 1, "recommended": 1},
                explanation=explanation
            )

        # 4. Проверка актуальности данных (TTL = 30 мин)
        now = datetime.utcnow()
        is_stale = False
        for o in valid_offers:
            col_at = o.get("collected_at")
            if isinstance(col_at, str):
                try:
                    col_at = datetime.fromisoformat(col_at.replace("Z", ""))
                except Exception:
                    col_at = None
            if col_at and (now - col_at) > timedelta(minutes=cls.TTL_MINUTES):
                is_stale = True
                break

        if is_stale:
            explanation.append("Данные о ценах конкурентов устарели (старше 30 минут). Обновите данные перед расчётом.")

        # 5. Анализ рынка
        comp_prices = sorted([float(o["price"]) for o in valid_offers])
        min_price = min(comp_prices)
        max_price = max(comp_prices)
        avg_price = round(sum(comp_prices) / len(comp_prices))
        median_price = float(statistics.median(comp_prices))
        competitor_count = len(comp_prices)

        market_stats = {
            "min_price": min_price,
            "avg_price": avg_price,
            "median_price": median_price,
            "max_price": max_price,
            "competitor_count": competitor_count
        }

        # 6. Стратегия ценообразования
        recommended_price = current_price or avg_price
        status = "RECOMMENDED"

        if target == "TOP_1":
            target_price = min_price - 1.0  # Шаг 1 ₸
            if target_price < minimum_safe_price:
                status = "TOP_1_UNAVAILABLE"
                recommended_price = minimum_safe_price
                explanation.append(f"Цена самого дешёвого конкурента — {int(min_price):,} ₸.".replace(",", " "))
                explanation.append(f"Минимальная безопасная цена с маржой {minimum_margin_percent}% составляет {int(minimum_safe_price):,} ₸.".replace(",", " "))
                explanation.append("Занять 1-е место невозможно без снижения маржи ниже установленного порога.")
            else:
                status = "RECOMMENDED"
                recommended_price = target_price
                explanation.append(f"Цена самого дешёвого конкурента — {int(min_price):,} ₸.".replace(",", " "))
                explanation.append(f"Рекомендуемая цена ({int(recommended_price):,} ₸) позволяет занять 1-ю позицию на рынке.".replace(",", " "))
                explanation.append("Минимально допустимый уровень прибыльности полностью соблюдён.")

        elif target == "BALANCED":
            balanced_target = round((min_price + avg_price) / 2.0)
            recommended_price = max(balanced_target, minimum_safe_price)
            explanation.append(f"Средняя цена рынка — {int(avg_price):,} ₸, минимальная — {int(min_price):,} ₸.".replace(",", " "))
            explanation.append(f"Сбалансированная стратегия предлагает цену {int(recommended_price):,} ₸ для оптимума спроса и маржи.".replace(",", " "))

        elif target == "MAX_MARGIN":
            recommended_price = max(median_price, minimum_safe_price)
            explanation.append(f"Медианная цена конкурентов — {int(median_price):,} ₸.".replace(",", " "))
            explanation.append(f"Стратегия MAX_MARGIN обеспечивает максимальную прибыль ({int(recommended_price):,} ₸) при сохранении конкурентности.".replace(",", " "))

        if is_stale and status == "RECOMMENDED":
            status = "STALE_DATA"

        if current_price and abs(current_price - recommended_price) < 1.0:
            status = "CURRENT_PRICE_OPTIMAL"
            explanation.append("Текущая цена продавца уже является оптимальной по выбранной стратегии.")

        # 7. Расчет прибыли и маржи
        profit = round(recommended_price - cost_price, 2)
        margin_percent = round(((recommended_price - cost_price) / recommended_price) * 100.0, 2) if recommended_price > 0 else 0.0

        curr_pos = cls.calculate_rank(current_price, comp_prices) if current_price else 1
        rec_pos = cls.calculate_rank(recommended_price, comp_prices)

        position_stats = {
            "current": curr_pos,
            "recommended": rec_pos
        }

        return PricingEngineResult(
            status=status,
            target=target,
            cost_price=cost_price,
            minimum_margin_percent=minimum_margin_percent,
            recommended_price=recommended_price,
            minimum_safe_price=minimum_safe_price,
            profit=profit,
            margin_percent=margin_percent,
            market=market_stats,
            position=position_stats,
            explanation=explanation
        )
