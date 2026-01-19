from .payout_crud_service import PayoutCRUDService
from .payout_task_service import PayoutTaskService

class PayoutService(PayoutCRUDService, PayoutTaskService):
    """Сервис для работы с выплатами"""
    pass

