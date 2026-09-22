import sys
from app.services.parser import UnifiedMarketplaceRouter

urls = [
    "https://kaspi.kz/shop/p/apple-iphone-15-128gb-chernyi-113137790/",
    "https://www.wildberries.ru/catalog/211694533/detail.aspx",
    "https://www.ozon.ru/product/smartfon-apple-iphone-15-128-gb-128456123/"
]

for u in urls:
    mp, sku, name = UnifiedMarketplaceRouter.extract_info(u)
    offers = UnifiedMarketplaceRouter.fetch_offers(mp, sku)
    print(f"[{mp.upper()}] SKU: {sku} | Title: {name} | Offers: {len(offers)} | Min Price: {offers[0]['price']} KZT")
