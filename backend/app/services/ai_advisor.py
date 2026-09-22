import logging
from typing import Dict, List, Optional
from app.config import settings

logger = logging.getLogger("sellerai.ai")

class AIAdvisorService:
    """
    SellerAI үшін нарықтық деректерді сараптап, қазақ тілінде сатушыға кеңес дайындайтын AI модулі
    """

    @classmethod
    def generate_recommendation(
        cls,
        product_name: str,
        my_price: Optional[float],
        cost_price: Optional[float],
        min_price: Optional[float],
        competitor_offers: List[Dict]
    ) -> Dict:
        """
        Бәсекелестер бағасына қарай AI талдау жүргізу және ұсыныс қайтару
        """
        if not competitor_offers:
            return {
                "alert_type": "INFO",
                "recommended_price": my_price,
                "analysis_text": "Бәсекелестер туралы деректер табылмады."
            }

        lowest_competitor = competitor_offers[0]
        lowest_price = lowest_competitor["price"]
        lowest_seller = lowest_competitor["seller_name"]

        # Егер OpenAI кілті бар болса, LLM-ге сұраныс жолдауға болады
        if settings.OPENAI_API_KEY:
            try:
                import openai
                client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

                prompt = f"""
                Сен — Kaspi.kz сатушыларының маржасы мен сатылымын арттыруға маманданған білікті бизнес-аналитиксің (SellerAI).
                Мына деректерді талдап, сатушыға нақты, түсінікті қазақ тілінде 3-4 сөйлемнен тұратын кеңес бер:

                Тауар: {product_name}
                Менің бағам: {my_price or 'Көрсетілмеген'} ₸
                Өзіндік құны: {cost_price or 'Көрсетілмеген'} ₸
                Минималды шекті баға: {min_price or 'Көрсетілмеген'} ₸
                Ең арзан бәсекелес: {lowest_seller} ({lowest_price} ₸)
                Барлық бәсекелестер саны: {len(competitor_offers)}

                Кеңес форматы:
                1. Нарықтағы ахуал (Демпинг бар ма, әлде баға тұрақты ма?)
                2. Сатушыға нақты қадам: бағаны түсіру керек пе, әлде маржаны сақтау керек пе?
                3. Ұсынылатын жаңа баға.
                """

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "Сен қазақстандық маркетплейстер бойынша білікті сарапшысың."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=300
                )
                ai_text = response.choices[0].message.content.strip()

                # Рекомендация бағасы
                rec_price = lowest_price - 100 if (min_price is None or (lowest_price - 100) >= min_price) else min_price

                return {
                    "alert_type": "PRICE_DROP" if (my_price and lowest_price < my_price) else "STABLE",
                    "recommended_price": rec_price,
                    "analysis_text": ai_text
                }
            except Exception as e:
                logger.error(f"OpenAI API қатесі: {e}. Ережеге негізделген логика іске қосылды.")

        # Ережеге негізделген аналитикалық модуль (Rule-based Expert Engine)
        return cls._rule_based_advice(product_name, my_price, cost_price, min_price, lowest_price, lowest_seller, len(competitor_offers))

    @classmethod
    def _rule_based_advice(
        cls,
        product_name: str,
        my_price: Optional[float],
        cost_price: Optional[float],
        min_price: Optional[float],
        lowest_price: float,
        lowest_seller: str,
        competitor_count: int
    ) -> Dict:
        """
        Бизнес-ережелерге негізделген автоматты қазақша кеңес шығару
        """
        # 1. Егер селлердің бағасы әлі қойылмаса:
        if not my_price:
            rec_price = lowest_price - 100 if (min_price is None or lowest_price - 100 >= min_price) else lowest_price
            return {
                "alert_type": "OPPORTUNITY",
                "recommended_price": rec_price,
                "analysis_text": f"Нарықта {competitor_count} бәсекелес бар. Ең төмен баға — {lowest_price:,.0f} ₸ ({lowest_seller}). Сатылымның бірінші орнына шығу үшін бағаны {rec_price:,.0f} ₸ етіп қою ұсынылады."
            }

        price_diff = my_price - lowest_price

        # 2. Мен бірінші орындамын ба?
        if price_diff <= 0:
            return {
                "alert_type": "LEADER",
                "recommended_price": my_price,
                "analysis_text": f"Құттықтаймыз! Сіздің бағаңыз ({my_price:,.0f} ₸) нарықта ең тиімді орында тұр. Жақын бәсекелесіңізден {abs(price_diff):,.0f} ₸ артықшылығыңыз бар. Бағаны өзгертпей, маржаны сақтаған жөн."
            }

        # 3. Бәсекелес демпинг жасады ма?
        if min_price and lowest_price < min_price:
            return {
                "alert_type": "DUMPING_DETECTED",
                "recommended_price": min_price,
                "analysis_text": f"⚠️ Назар аударыңыз: '{lowest_seller}' дүкені бағаны {lowest_price:,.0f} ₸-ге дейін түсірді (демпинг). Бұл сіздің шекті бағаңыздан ({min_price:,.0f} ₸) төмен. Залалға ұшырамау үшін бағаны бұдан әрі түсірмей, тез жеткізуге немесе бонустарға көңіл бөліңіз."
            }

        # 4. Бағаны оңтайландыру (1-орынды қайтарып алу)
        target_price = lowest_price - 100
        if min_price and target_price < min_price:
            target_price = min_price

        margin_info = ""
        if cost_price:
            margin = ((target_price - cost_price) / target_price) * 100
            margin_info = f" Бұл бағада таза маржаңыз: {margin:.1f}% құрайды."

        return {
            "alert_type": "PRICE_DROP",
            "recommended_price": target_price,
            "analysis_text": f"Нарықта '{lowest_seller}' дүкені {lowest_price:,.0f} ₸ бағасымен бірінші орынды иеленді. Баға айырмасы: {price_diff:,.0f} ₸. Қайта көшбасшы болу үшін бағаны {target_price:,.0f} ₸ деңгейіне түсіру тиімді.{margin_info}"
        }
