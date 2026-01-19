from celery import shared_task
import logging
from .services.celery_services.payout_task_proccessing_service import PayoutProcessingService, ProcessingInProgress, StopProcessing

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    ignore_result=False,
    acks_late=True,
)
def payout_task(self, payout_id):
    """
    Асинхронная задача обработки выплаты

    1. Принимает идентификатор созданной заявки (payout_id)
    2. Имитирует обработку (задержка, логирование, проверки)
    3. Изменяет статус заявки после обработки
    """

    try:
        service = PayoutProcessingService(payout_id, task=self)
        return service.process()

    except ProcessingInProgress as exc:
        # Если обработка уже идет, ждем и пробуем снова
        logger.info(f"Обработка выплаты {payout_id} уже выполняется, повтор через 10 секунд")
        raise self.retry(countdown=10, exc=exc)

    except StopProcessing as exc:
        # Обработка уже завершена или не требуется
        return exc.result if hasattr(exc, 'result') else {
            'success': True,
            'payout_id': payout_id,
            'message': 'Обработка уже была выполнена'
        }

    except Exception as exc:
        logger.error(f"Ошибка в задаче обработки выплаты {payout_id}: {str(exc)}")
        raise self.retry(exc=exc)