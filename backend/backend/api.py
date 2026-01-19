from django.conf import settings
from django.http import JsonResponse
from ninja import NinjaAPI
from ninja.errors import ValidationError

from api_payouts.api import router as api_app_payment_router


api = NinjaAPI(
    title="API",
    version="1.0.0",
    description="API-Django",
    docs_url="/docs/",
    openapi_url="/openapi.json",
)

api.add_router("/payouts/", api_app_payment_router)


@api.exception_handler(ValidationError)
def validation_errors(request, exc):
    errors = exc.errors
    if errors:
        first_error = errors[0]
        field = first_error.get("loc")[-1] if first_error.get("loc") else "field"
        msg = first_error.get("msg", "Validation error")

        # Простое сообщение
        error_msg = f"Ошибка в поле '{field}': {msg}"
    else:
        error_msg = "Ошибка валидации"

    return JsonResponse({"detail": error_msg}, status=422)


if settings.DEBUG is False:
    # В PRODUCTION режиме - общие ошибки
    @api.exception_handler(Exception)
    def production_error_handler(request, exc):
        # Логируем для себя
        import logging
        logging.getLogger(__name__).error(
            f"Server error: {exc}",
            exc_info=True
        )

        return api.create_response(
            request,
            {"detail": "Внутренняя ошибка сервера", "code": "server_error"},
            status=500,
        )
