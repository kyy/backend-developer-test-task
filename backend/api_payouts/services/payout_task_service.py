from typing import Dict, Any
from django.db import transaction
from ..tasks import payout_task


class PayoutTaskService:
    """Сервис для работы с фоновыми задачами"""

    @staticmethod
    def execute_payout(payout_id: str, countdown=1) -> Dict[str, Any]:
        """Фоновая обработка выплаты - запуск"""
        return transaction.on_commit(lambda: payout_task.apply_async(args=[payout_id], countdown=countdown))
