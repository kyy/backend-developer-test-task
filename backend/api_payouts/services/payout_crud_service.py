from typing import List, Dict, Any
from ..models import Payout
from ..schemas import PayoutCreateSchema, PayoutUpdateSchema


class PayoutCRUDService:
    """Сервис для работы с выплатами CRUD"""

    @staticmethod
    def get_list_payouts() -> List[Payout]:
        """Получить все выплаты"""
        return Payout.objects.all().order_by('-created_at')

    @staticmethod
    def get_payout(payout_id: str) -> Payout:
        """Получить выплату по ID"""
        return Payout.objects.get_payout(payout_id=payout_id)

    @staticmethod
    def create_payout(payload: PayoutCreateSchema) -> Payout:
        """Создать новую выплату"""
        payout = Payout.objects.create_payout(**payload.dict(exclude_unset=True), status='pending')

        return payout

    @staticmethod
    def delete_payout(payout_id: str) -> Dict[str, Any]:
        """Удалить выплату"""
        Payout.objects.delete_payout(payout_id=payout_id)
        return {"success": True}

    @staticmethod
    def update_payout(payout_id: str, payload: PayoutUpdateSchema) -> Payout:
        """Обновить заявку - статус или комментарий"""
        payout = Payout.objects.update_payout(payout_id=payout_id, payload=payload.dict(exclude_unset=True))
        return payout


