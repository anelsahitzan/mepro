import unittest
from datetime import datetime, timedelta
from app.services.pricing_engine import PricingEngine

class TestPricingEngine(unittest.TestCase):

    def test_minimum_safe_price_calculation(self):
        # 85 000 / (1 - 0.10) = 94 444.44 -> math.ceil = 94 445 ₸
        safe_price = PricingEngine.calculate_minimum_safe_price(85000, 10.0)
        self.assertEqual(safe_price, 94445)

    def test_top_1_recommendation(self):
        offers = [
            {"seller_id": "s1", "seller_name": "Comp 1", "price": 107990, "available": True, "is_mine": False, "collected_at": datetime.utcnow()},
            {"seller_id": "s2", "seller_name": "Comp 2", "price": 111450, "available": True, "is_mine": False, "collected_at": datetime.utcnow()},
            {"seller_id": "s3", "seller_name": "My Shop", "price": 109990, "available": True, "is_mine": True, "collected_at": datetime.utcnow()}
        ]
        res = PricingEngine.recommend(
            cost_price=85000,
            minimum_margin_percent=10.0,
            offers=offers,
            target="TOP_1",
            current_price=109990
        )
        self.assertEqual(res.status, "RECOMMENDED")
        self.assertEqual(res.recommended_price, 107989)
        self.assertEqual(res.position["recommended"], 1)
        self.assertGreater(res.profit, 0)

    def test_top_1_unavailable(self):
        # Min comp price is 90 000, but min safe price with 15% margin for 85 000 is 100 000
        offers = [
            {"seller_id": "s1", "seller_name": "Comp 1", "price": 90000, "available": True, "is_mine": False, "collected_at": datetime.utcnow()}
        ]
        res = PricingEngine.recommend(
            cost_price=85000,
            minimum_margin_percent=15.0,
            offers=offers,
            target="TOP_1",
            current_price=109990
        )
        self.assertEqual(res.status, "TOP_1_UNAVAILABLE")
        self.assertEqual(res.recommended_price, res.minimum_safe_price)
        self.assertGreaterEqual(res.recommended_price, 100000)

    def test_no_competitors(self):
        res = PricingEngine.recommend(
            cost_price=85000,
            minimum_margin_percent=10.0,
            offers=[],
            target="TOP_1"
        )
        self.assertEqual(res.status, "NO_COMPETITORS")

    def test_invalid_input(self):
        res = PricingEngine.recommend(
            cost_price=-100,
            minimum_margin_percent=10.0,
            offers=[],
            target="TOP_1"
        )
        self.assertEqual(res.status, "INVALID_INPUT")

    def test_stale_data(self):
        stale_time = datetime.utcnow() - timedelta(minutes=45)
        offers = [
            {"seller_id": "s1", "seller_name": "Comp 1", "price": 107990, "available": True, "is_mine": False, "collected_at": stale_time}
        ]
        res = PricingEngine.recommend(
            cost_price=85000,
            minimum_margin_percent=10.0,
            offers=offers,
            target="TOP_1"
        )
        self.assertEqual(res.status, "STALE_DATA")

    def test_exclusion_of_mine_and_unavailable(self):
        offers = [
            {"seller_id": "s1", "seller_name": "Comp 1", "price": 80000, "available": False, "is_mine": False, "collected_at": datetime.utcnow()},
            {"seller_id": "s2", "seller_name": "My Shop", "price": 70000, "available": True, "is_mine": True, "collected_at": datetime.utcnow()},
            {"seller_id": "s3", "seller_name": "Comp 2", "price": 105000, "available": True, "is_mine": False, "collected_at": datetime.utcnow()}
        ]
        filtered = PricingEngine.filter_offers(offers)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["seller_name"], "Comp 2")

if __name__ == "__main__":
    unittest.main()
