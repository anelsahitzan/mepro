from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import logging

from app.database import SessionLocal
from app.models import Product, PriceHistory, PriceChange
from app.services.parser import UnifiedMarketplaceRouter

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler()

JOB_ID = "refresh_prices_job"

def refresh_prices_task():
    logger.info("Scheduler: Starting automatic price refresh...")
    db = SessionLocal()
    try:
        products = db.query(Product).filter(Product.is_active == True).all()
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
                            product_id=p.id,
                            seller_name=item["seller_name"],
                            is_my_shop=is_mine,
                            price=item["price"],
                            recorded_at=now
                        ))
                    p.last_checked_at = now
                    if curr_my: p.current_price = curr_my
                    
                    # --- AUTO REPRICING LOGIC ---
                    if p.is_auto_repricing and curr_my:
                        comp_prices = [item["price"] for item in offers if not bool(my_shop_name and item["seller_name"].lower() == my_shop_name)]
                        if comp_prices:
                            min_comp = min(comp_prices)
                            if min_comp < curr_my:
                                target = min_comp - 100
                                if p.min_price_threshold and target < p.min_price_threshold:
                                    target = p.min_price_threshold
                                
                                if target < curr_my:
                                    db.add(PriceChange(
                                        user_id=p.user_id,
                                        product_id=p.id,
                                        old_price=curr_my,
                                        new_price=target,
                                        reason="Auto-Repricing",
                                        created_at=now
                                    ))
                                    p.current_price = target

                    updated += 1
                except Exception as e:
                    logger.warning(f"Scheduler: Failed to update product {p.id}: {e}")
        db.commit()
        logger.info(f"Scheduler: Automatic price refresh completed. {updated} products updated.")
    except Exception as e:
        logger.error(f"Scheduler: Fatal error during background refresh: {e}")
    finally:
        db.close()

def start_scheduler():
    if not scheduler.running:
        scheduler.start()
        # Ensure job exists by default
        if not scheduler.get_job(JOB_ID):
            scheduler.add_job(
                func=refresh_prices_task,
                trigger=IntervalTrigger(minutes=30),
                id=JOB_ID,
                name="Auto refresh prices every 30m",
                replace_existing=True
            )
            
def get_scheduler_status():
    job = scheduler.get_job(JOB_ID)
    if job:
        return {
            "enabled": True,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
        }
    return {
        "enabled": False,
        "next_run_time": None
    }

def toggle_scheduler():
    job = scheduler.get_job(JOB_ID)
    if job:
        scheduler.remove_job(JOB_ID)
        return {"enabled": False, "next_run_time": None}
    else:
        scheduler.add_job(
            func=refresh_prices_task,
            trigger=IntervalTrigger(minutes=30),
            id=JOB_ID,
            name="Auto refresh prices every 30m",
            replace_existing=True
        )
        new_job = scheduler.get_job(JOB_ID)
        return {"enabled": True, "next_run_time": new_job.next_run_time.isoformat() if new_job.next_run_time else None}
