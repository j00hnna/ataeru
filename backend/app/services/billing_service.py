"""
خدمة الفوترة عبر Stripe.
"""
import os
import stripe
import logging
from app.models.company import Company

logger = logging.getLogger("ataeru.billing")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class BillingService:
    @staticmethod
    def create_checkout_session(company: Company, plan: str, success_url: str, cancel_url: str) -> str:
        price_id = os.getenv(f"STRIPE_PRICE_ID_{plan.upper()}")
        if not price_id:
            raise ValueError(f"لا يوجد سعر معرف للخطة {plan}")
        if not company.stripe_customer_id:
            customer = stripe.Customer.create(
                metadata={"company_id": company.id}
            )
            company.stripe_customer_id = customer.id
        session = stripe.checkout.Session.create(
            customer=company.stripe_customer_id,
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"company_id": company.id, "plan": plan}
        )
        return session.url