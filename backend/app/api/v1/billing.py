"""
نقاط نهاية الفوترة و Stripe Webhook.
"""
import os
import stripe
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.company import Company, SubscriptionPlan
from app.services.billing_service import BillingService

logger = logging.getLogger("ataeru.billing")
router = APIRouter(prefix="/billing", tags=["الفوترة"])

@router.post("/create-checkout")
def create_checkout(
    plan: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    company = current_user.company
    if not company:
        raise HTTPException(400, "لا توجد شركة مرتبطة")
    try:
        success_url = "http://localhost:5173/dashboard?payment=success"
        cancel_url = "http://localhost:5173/billing?payment=cancelled"
        url = BillingService.create_checkout_session(company, plan, success_url, cancel_url)
        db.commit()
        return {"url": url}
    except Exception as e:
        logger.error(f"Checkout error: {e}", exc_info=True)
        raise HTTPException(500, "فشل إنشاء جلسة الدفع")

@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        raise HTTPException(500, "لم يتم تعريف سر الـ Webhook")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        raise HTTPException(400, "توقيع غير صالح")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        company_id = session["metadata"].get("company_id")
        plan = session["metadata"].get("plan", "PRO")
        if company_id:
            company = db.query(Company).filter(Company.id == int(company_id)).first()
            if company:
                company.subscription_plan = SubscriptionPlan[plan.upper()]
                db.commit()
    elif event["type"] == "customer.subscription.deleted":
        sub = event["data"]["object"]
        company_id = sub["metadata"].get("company_id")
        if company_id:
            company = db.query(Company).filter(Company.id == int(company_id)).first()
            if company:
                company.subscription_plan = SubscriptionPlan.FREE
                company.subscription_end_date = None
                db.commit()
    return {"status": "ok"}