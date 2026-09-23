import re
import time
import json
import random
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import requests
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.database import SessionLocal
from app.models import Product, PriceHistory, AIRecommendation
from app.services.ai_advisor import AIAdvisorService

# Logging configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("sellerai.parser")

COMMON_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
]


class KaspiParser:
    """
    1. Kaspi.kz Маркетплейс парсері
    """
    @classmethod
    def extract_product_id(cls, url_or_id: str) -> Tuple[str, str]:
        url_or_id = url_or_id.strip()
        if url_or_id.isdigit():
            return url_or_id, f"Kaspi Тауар #{url_or_id}"

        match = re.search(r"/shop/p/([a-zA-Z0-9_-]+)-(\d+)", url_or_id)
        if match:
            slug = match.group(1).replace("-", " ").title()
            product_id = match.group(2)
            return product_id, slug

        digit_match = re.search(r"(\d{6,15})", url_or_id)
        if digit_match:
            pid = digit_match.group(1)
            return pid, f"Kaspi Тауар #{pid}"

        return "113137790", "Apple iPhone 15 128Gb"

    @classmethod
    def fetch_offers(cls, product_id: str, city_id: str = "750000000") -> List[Dict]:
        """Kaspi.kz өнімі бойынша бағалар мен бәсекелестерді алу"""
        # 1. Тікелей Kaspi.kz Offers API арқылы реалды сатушылар мен бағаларды алу
        offers = []
        try:
            api_url = f"https://kaspi.kz/yml/offer-view/offers/{product_id}"
            headers = {
                "User-Agent": random.choice(COMMON_USER_AGENTS),
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json;charset=UTF-8",
                "Referer": f"https://kaspi.kz/shop/p/-{product_id}/",
                "X-KS-City": city_id
            }
            payload = {"cityId": city_id, "id": str(product_id), "limit": 10, "page": 0, "sort": True}
            res = requests.post(api_url, json=payload, headers=headers, timeout=6)
            if res.status_code == 200:
                raw_offers = res.json().get("offers", [])
                for off in raw_offers:
                    s_name = off.get("merchantName") or "Kaspi Seller"
                    s_price = float(off.get("price", 0))
                    if s_price > 0:
                        s_rating = float(off.get("merchantRating", 4.8))
                        s_reviews = int(off.get("merchantReviewsQuantity", 50))
                        del_info = "Kaspi Доставка"
                        if off.get("deliveryMovedBySlot"):
                            del_info = "Экспресс 3 сағ"
                        elif off.get("delivery"):
                            del_info = "Бүгін жеткізу"
                        offers.append({
                            "seller_name": s_name,
                            "price": s_price,
                            "is_available": True,
                            "delivery_type": del_info,
                            "rating": s_rating,
                            "reviews_count": s_reviews,
                            "marketplace": "kaspi"
                        })
                if offers:
                    logger.info(f"✅ Kaspi.kz API сәтті парсинг жасалды: {len(offers)} сатушы табылды")
                    offers.sort(key=lambda x: x["price"])
                    return offers
        except Exception as e:
            logger.warning(f"Kaspi API live offers scraping exception: {e}")

        # 2. Тікелей HTML JSON-LD арқылы нақты бағаны тексеру (резервтік режим)
        real_price = None
        real_name = None
        try:
            url = f"https://kaspi.kz/shop/p/-{product_id}/"
            headers = {
                "User-Agent": random.choice(COMMON_USER_AGENTS),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
            res = requests.get(url, headers=headers, timeout=6)
            if res.status_code == 200:
                json_match = re.search(r'<script type="application/ld\+json">(\s*\{[^{]*"@type":\s*"Product".*?\})\s*</script>', res.text, re.DOTALL)
                if json_match:
                    p_data = json.loads(json_match.group(1))
                    real_name = p_data.get("name")
                    offers_field = p_data.get("offers", [])
                    if isinstance(offers_field, list):
                        for off in offers_field:
                            p_val = off.get("price")
                            if p_val and str(p_val) != "undefined":
                                real_price = float(p_val)
                                break
                    elif isinstance(offers_field, dict):
                        p_val = offers_field.get("price")
                        if p_val and str(p_val) != "undefined":
                            real_price = float(p_val)
        except Exception as e:
            logger.debug(f"Kaspi HTML scraping exception: {e}")

        # Нақты баға табылса — тек соны қайтарамыз. Кездейсоқ бәсекелестер жасамаймыз.
        if real_price:
            logger.info(f"✅ Kaspi HTML-ден нақты баға табылды: {real_price} ₸. Бір жазба қайтарылады.")
            return [{
                "seller_name": real_name or f"Kaspi Seller #{product_id}",
                "price": real_price,
                "is_available": True,
                "delivery_type": "Kaspi Доставка",
                "rating": None,
                "reviews_count": None,
                "marketplace": "kaspi"
            }]

        # Ешқанда да табылмаса — бос тізім қайтарамыз
        logger.warning(f"Kaspi: SKU {product_id} бойынша баға табылмады, бос тізім қайтарылады.")
        return []


class WildberriesParser:
    """
    2. Wildberries (WB.ru / WB.kz) Маркетплейс парсері
    """
    @classmethod
    def extract_product_id(cls, url_or_id: str) -> Tuple[str, str]:
        """
        WB сілтемесінен немесе артикулынан NM-ID бөліп алу
        Мысалы: 'https://www.wildberries.ru/catalog/211694533/detail.aspx' -> ('211694533', 'WB Товар #211694533')
        """
        url_or_id = url_or_id.strip()
        if url_or_id.isdigit():
            return url_or_id, f"WB Артикул #{url_or_id}"

        match = re.search(r"catalog/(\d+)/detail", url_or_id)
        if match:
            nm_id = match.group(1)
            return nm_id, f"WB Товар #{nm_id}"

        digit_match = re.search(r"(\d{7,12})", url_or_id)
        if digit_match:
            pid = digit_match.group(1)
            return pid, f"WB Товар #{pid}"

        return "211694533", "Wildberries Тауары"

    @classmethod
    def fetch_offers(cls, nm_id: str) -> List[Dict]:
        """
        Wildberries CDN себетінен (вббаскет.ru) өнім картасын тартып алу
        Нақты нәтиже табылмаса — бос тізім қайтарылады
        """
        product_title = None
        brand_name = "Wildberries Seller"
        price_rub = None

        try:
            art = int(nm_id)
            vol = art // 100000
            part = art // 1000

            for i in range(1, 20):
                basket_str = f"0{i}" if i < 10 else f"{i}"
                url = f"https://basket-{basket_str}.wbbasket.ru/vol{vol}/part{part}/{art}/info/ru/card.json"
                try:
                    r = requests.get(url, timeout=2.5)
                    if r.status_code == 200:
                        data = r.json()
                        product_title = data.get("imt_name") or data.get("subj_name")
                        selling = data.get("selling", {})
                        if selling:
                            brand_name = selling.get("brand_name", brand_name)
                        # Бағаны WB API-ден алу (salePriceU = қапаларда)
                        salePriceU = data.get("salePriceU")
                        priceU = data.get("priceU")
                        if salePriceU:
                            price_rub = float(salePriceU) / 100.0
                        elif priceU:
                            price_rub = float(priceU) / 100.0
                        logger.info(f"WB табылды (basket-{basket_str}): {product_title} [{brand_name}] баға={price_rub} ₽")
                        break
                except Exception:
                    continue
        except Exception as e:
            logger.warning(f"WB парсинг барысында қате: {e}")

        if not price_rub:
            logger.warning(f"WB: nm_id={nm_id} бойынша баға табылмады, бос тізім қайтарылады.")
            return []

        # Қазақстан үшін KZT валютасына конвертациялау (~5.1 ₸)
        price_kzt = round(price_rub * 5.1, -1)

        return [{
            "seller_name": f"{brand_name} (WB)",
            "price": float(price_kzt),
            "is_available": True,
            "delivery_type": "WB Доставка",
            "rating": None,
            "reviews_count": None,
            "marketplace": "wildberries"
        }]


class OzonParser:
    """
    3. Ozon (Ozon.ru / Ozon.kz) Маркетплейс парсері
    """
    @classmethod
    def extract_product_id(cls, url_or_id: str) -> Tuple[str, str]:
        """
        Ozon сілтемесінен немесе ID-ден SKU бөліп алу
        Мысалы: 'https://www.ozon.ru/product/smartfon-apple-iphone-15-128-gb-chernyi-128456123/' -> ('128456123', 'Smartfon Apple Iphone 15')
        """
        url_or_id = url_or_id.strip()
        if url_or_id.isdigit():
            return url_or_id, f"Ozon SKU #{url_or_id}"

        match = re.search(r"ozon\.(?:ru|kz)/product/(?:([a-zA-Z0-9_-]+)-)?(\d+)", url_or_id)
        if match:
            slug = match.group(1).replace("-", " ").title() if match.group(1) else "Ozon Товар"
            pid = match.group(2)
            return pid, slug

        digit_match = re.search(r"(\d{8,12})", url_or_id)
        if digit_match:
            pid = digit_match.group(1)
            return pid, f"Ozon Товар #{pid}"

        return "128456123", "Ozon Товар"

    @classmethod
    def fetch_offers(cls, product_id: str) -> List[Dict]:
        """
        Ozon тауары бойынша нақты деректер алу ерекешеті.
        Ozon API икемді авторизация талап етеді, бүгінде бос тізім қайтарамыз.
        """
        logger.warning(f"Ozon: SKU {product_id} — Ozon API толық іске асырылмаған. Бос тізім қайтарылады.")
        return []


class YandexMarketParser:
    """
    4. Yandex Market (Market.yandex.ru / kz) Маркетплейс парсері
    """
    @classmethod
    def extract_product_id(cls, url_or_id: str) -> Tuple[str, str]:
        url_or_id = url_or_id.strip()
        match = re.search(r"market\.yandex\.(?:ru|kz)/product(?:--[a-zA-Z0-9_-]+)?/(\d+)", url_or_id)
        if match:
            return match.group(1), f"Yandex Товар #{match.group(1)}"

        digit_match = re.search(r"(\d{7,12})", url_or_id)
        if digit_match:
            return digit_match.group(1), f"Yandex Товар #{digit_match.group(1)}"

        return "10234567", "Yandex Market Товар"

    @classmethod
    def fetch_offers(cls, product_id: str) -> List[Dict]:
        """
        Yandex Market API толық іске асырылмаған.
        Бос тізім қайтарылады.
        """
        logger.warning(f"YandexMarket: SKU {product_id} — API толық іске асырылмаған. Бос тізім қайтарылады.")
        return []


class UnifiedMarketplaceRouter:
    """
    Барлық маркетплейстерді (Kaspi, WB, Ozon, Yandex) біріктіретін басты диспетчер
    """
    @classmethod
    def detect_marketplace(cls, url_or_id: str) -> str:
        url_lower = url_or_id.lower()
        if "wildberries" in url_lower or "wb.ru" in url_lower or "wb.kz" in url_lower:
            return "wildberries"
        elif "ozon.ru" in url_lower or "ozon.kz" in url_lower:
            return "ozon"
        elif "yandex" in url_lower:
            return "yandex_market"
        else:
            return "kaspi"

    @classmethod
    def extract_info(cls, url_or_id: str) -> Tuple[str, str, str]:
        """Маркетплейс түрін, ID және атын автоматты анықтау"""
        mp = cls.detect_marketplace(url_or_id)
        if mp == "wildberries":
            sku, name = WildberriesParser.extract_product_id(url_or_id)
        elif mp == "ozon":
            sku, name = OzonParser.extract_product_id(url_or_id)
        elif mp == "yandex_market":
            sku, name = YandexMarketParser.extract_product_id(url_or_id)
        else:
            sku, name = KaspiParser.extract_product_id(url_or_id)

        return mp, sku, name

    @classmethod
    def fetch_offers(cls, marketplace: str, product_id: str) -> List[Dict]:
        """Керекті маркетплейс парсеріне сұраныс бағыттау"""
        if marketplace == "wildberries":
            return WildberriesParser.fetch_offers(product_id)
        elif marketplace == "ozon":
            return OzonParser.fetch_offers(product_id)
        elif marketplace == "yandex_market":
            return YandexMarketParser.fetch_offers(product_id)
        else:
            return KaspiParser.fetch_offers(product_id)


class PriceMonitorEngine:
    """
    Көп маркетплейстік бақылау және Diff-checking қозғалтқышы
    """
    @classmethod
    def check_price_diff(cls, db: Session, product_id: int, new_lowest_price: float, lowest_seller: str) -> Optional[Dict]:
        last_lowest_record = db.query(PriceHistory).filter(
            PriceHistory.product_id == product_id
        ).order_by(desc(PriceHistory.recorded_at)).first()

        if not last_lowest_record:
            return None

        old_price = float(last_lowest_record.price)
        diff = new_lowest_price - old_price

        if abs(diff) > 50:
            return {
                "old_price": old_price,
                "new_price": new_lowest_price,
                "diff": diff,
                "seller": lowest_seller,
                "is_drop": diff < 0
            }
        return None

    @classmethod
    def run_monitoring_cycle(cls, my_shop_name: str = "Almaty Mobile") -> int:
        db = SessionLocal()
        try:
            active_products = db.query(Product).filter(Product.is_active == True).all()
            logger.info(f"🔄 Көп маркетплейстік цикл басталды. Белсенді тауарлар: {len(active_products)}")

            processed_count = 0
            for product in active_products:
                mp = product.marketplace or "kaspi"
                logger.info(f"🔎 [{mp.upper()}] Тауар өңделуде: [{product.sku}] {product.product_name}")

                offers = UnifiedMarketplaceRouter.fetch_offers(mp, product.sku)
                if not offers:
                    continue

                lowest_offer = offers[0]
                lowest_price = lowest_offer["price"]
                lowest_seller = lowest_offer["seller_name"]

                price_diff = cls.check_price_diff(db, product.id, lowest_price, lowest_seller)
                if price_diff:
                    action = "ТҮСТІ 📉" if price_diff["is_drop"] else "ӨСТІ 📈"
                    logger.warning(
                        f"⚡ [{mp.upper()}] БАҒА ӨЗГЕРІСІ! {product.product_name}: "
                        f"{price_diff['old_price']:,.0f} ₸ -> {price_diff['new_price']:,.0f} ₸ ({action}) "
                        f"Дүкен: {price_diff['seller']}"
                    )

                now = datetime.utcnow()
                my_current_price = None

                for item in offers:
                    is_mine = (my_shop_name.lower() in item["seller_name"].lower())
                    if is_mine:
                        my_current_price = item["price"]

                    history_record = PriceHistory(
                        product_id=product.id,
                        seller_name=item["seller_name"],
                        is_my_shop=is_mine,
                        price=item["price"],
                        is_available=item.get("is_available", True),
                        delivery_type=item.get("delivery_type"),
                        recorded_at=now
                    )
                    db.add(history_record)

                if my_current_price:
                    product.current_price = my_current_price
                product.last_checked_at = now

                ai_result = AIAdvisorService.generate_recommendation(
                    product_name=f"[{mp.upper()}] {product.product_name}",
                    my_price=float(product.current_price) if product.current_price else None,
                    cost_price=float(product.cost_price) if product.cost_price else None,
                    min_price=float(product.min_price_threshold) if product.min_price_threshold else None,
                    competitor_offers=offers
                )

                ai_rec = AIRecommendation(
                    product_id=product.id,
                    recommended_price=ai_result.get("recommended_price"),
                    alert_type=ai_result.get("alert_type", "INFO"),
                    analysis_text=ai_result.get("analysis_text", "")
                )
                db.add(ai_rec)
                db.commit()

                processed_count += 1
                time.sleep(random.uniform(1.2, 2.5))

            return processed_count
        except Exception as e:
            logger.error(f"❌ Мониторинг қатесі: {e}")
            db.rollback()
            return 0
        finally:
            db.close()


if __name__ == "__main__":
    print("=" * 65)
    print("🚀 SellerAI Multi-Marketplace Parser (Kaspi + WB + Ozon + Yandex)")
    print("=" * 65)

    test_urls = [
        "https://kaspi.kz/shop/p/apple-iphone-15-128gb-chernyi-113137790/",
        "https://www.wildberries.ru/catalog/211694533/detail.aspx",
        "https://www.ozon.ru/product/smartfon-apple-iphone-15-128-gb-128456123/"
    ]

    for url in test_urls:
        mp, sku, title = UnifiedMarketplaceRouter.extract_info(url)
        print(f"\n📦 Маркетплейс: {mp.upper()} | SKU: {sku} | Атауы: {title}")
        offers = UnifiedMarketplaceRouter.fetch_offers(mp, sku)
        for idx, o in enumerate(offers[:3], 1):
            print(f"   [{idx}] {o['seller_name']:<25} | {o['price']:>9,.0f} ₸ | {o['delivery_type']}")
