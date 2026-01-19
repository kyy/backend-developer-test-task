from ninja import Router
from typing import List
from ninja.pagination import paginate, PageNumberPagination

from .schemas import PayoutCreateSchema, PayoutUpdateSchema, PayoutResponseSchema
from .services.payout_service import PayoutService

router = Router(tags=["payouts-interface"])


@router.get("/", response=List[PayoutResponseSchema])
@paginate(PageNumberPagination, page_size=10)
def list_payouts(request):
    """Список всех заявок"""
    return PayoutService.get_list_payouts()


@router.get("/{payout_id}/", response=PayoutResponseSchema)
def get_payout(request, payout_id: str):
    """Получение заявки по ID"""
    return PayoutService.get_payout(payout_id=payout_id)


@router.post("/", response=PayoutResponseSchema)
def create_payout(request, payload: PayoutCreateSchema):
    """Создание заявки"""
    payout = PayoutService.create_payout(payload=payload)
    PayoutService.execute_payout(str(payout.id))
    return payout


@router.patch("/{payout_id}/", response=PayoutResponseSchema)
def update_payout(request, payout_id: str, payload: PayoutUpdateSchema):
    """Обновление заявки"""
    return PayoutService.update_payout(payout_id=payout_id, payload=payload)


@router.delete("/{payout_id}/")
def delete_payout(request, payout_id: str):
    """Удаление заявки"""
    return PayoutService.delete_payout(payout_id=payout_id)