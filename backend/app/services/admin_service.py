"""
خدمة إحصائيات المسؤول. تجمع أعداد المستخدمين والشركات والعطاءات والإيرادات.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.user import User
from app.models.company import Company
from app.models.rfp_analysis import RFPAnalysis
from app.models.response import Response


class AdminService:
    @staticmethod
    def get_stats(db: Session) -> dict:
        total_users = db.query(func.count(User.id)).scalar()
        total_companies = db.query(func.count(Company.id)).scalar()
        total_analyses = db.query(func.count(RFPAnalysis.id)).scalar()
        total_responses = db.query(func.count(Response.id)).scalar()
        paid_companies = db.query(func.count(Company.id)).filter(
            Company.subscription_plan.in_(["PRO", "ENTERPRISE"])
        ).scalar()
        estimated_revenue = paid_companies * 500  # تقديري

        return {
            "total_users": total_users,
            "total_companies": total_companies,
            "total_analyses": total_analyses,
            "total_responses": total_responses,
            "paid_companies": paid_companies,
            "estimated_revenue": estimated_revenue
        }

    @staticmethod
    def get_recent_analyses(db: Session, limit: int = 10) -> list:
        analyses = db.query(RFPAnalysis).order_by(RFPAnalysis.created_at.desc()).limit(limit).all()
        return [
            {
                "id": a.id,
                "company_name": a.company.name if a.company else "N/A",
                "file_name": a.original_file_name,
                "status": a.status.value,
                "created_at": a.created_at.isoformat()
            }
            for a in analyses
        ]