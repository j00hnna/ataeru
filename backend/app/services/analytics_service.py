"""
خدمة تحليلات العميل: عدد العطاءات، الردود، متوسط الامتثال، ونسبة الفوز.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.rfp_analysis import RFPAnalysis
from app.models.response import Response


class AnalyticsService:
    @staticmethod
    def get_client_analytics(db: Session, company_id: int) -> dict:
        total_analyses = db.query(func.count(RFPAnalysis.id)).filter(
            RFPAnalysis.company_id == company_id
        ).scalar()

        total_responses = db.query(func.count(Response.id)).join(RFPAnalysis).filter(
            RFPAnalysis.company_id == company_id
        ).scalar()

        avg_compliance = db.query(func.avg(Response.compliance_score)).join(RFPAnalysis).filter(
            RFPAnalysis.company_id == company_id,
            Response.compliance_score.isnot(None)
        ).scalar()

        exported_responses = db.query(func.count(Response.id)).join(RFPAnalysis).filter(
            RFPAnalysis.company_id == company_id,
            Response.status == "EXPORTED"
        ).scalar()

        return {
            "total_analyses": total_analyses,
            "total_responses": total_responses,
            "avg_compliance": round(avg_compliance, 2) if avg_compliance else 0,
            "exported_responses": exported_responses,
        }