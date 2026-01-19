from decimal import Decimal
import uuid
from unittest import TestCase
from pydantic import ValidationError

from api_payouts.schemas import (
    CardSchema,
    PayoutCreateSchema,
    PayoutUpdateSchema,
    PayoutResponseSchema,
    ErrorSchema,
    ValidationErrorSchema
)
from api_payouts.models import Currency, Status


class SchemaValidationTestCase(TestCase):
    """Тесты валидации схем"""

    def test_card_schema_valid(self):
        """Тест валидных данных карты"""
        # Валидные данные
        valid_data = {
            "card_number": "5555555555554444",
            "card_holder": "Ivanov Ivan",
            "expiry_date": "12/25"
        }

        card = CardSchema(**valid_data)
        self.assertEqual(card.card_number, "5555555555554444")
        self.assertEqual(card.card_holder, "Ivanov Ivan")
        self.assertEqual(card.expiry_date, "12/25")

        # Двойные фамилии/имена
        valid_data2 = {
            "card_number": "6011000990139424",
            "card_holder": "Petrov-Vasilev Ivan",
            "expiry_date": "01/30"
        }

        card2 = CardSchema(**valid_data2)
        self.assertEqual(card2.card_holder, "Petrov-Vasilev Ivan")

    def test_card_schema_invalid(self):
        """Тест невалидных данных карты"""
        test_cases = [
            {
                "data": {
                    "card_number": "123",  # Слишком короткий
                    "card_holder": "Ivanov Ivan",
                    "expiry_date": "12/25"
                },
                "error_field": "card_number"
            },
            {
                "data": {
                    "card_number": "5555555555554444",
                    "card_holder": "ivanov ivan",  # С маленькой буквы
                    "expiry_date": "12/25"
                },
                "error_field": "card_holder"
            },
            {
                "data": {
                    "card_number": "5555555555554444",
                    "card_holder": "Ivanov Ivan",
                    "expiry_date": "13/25"  # Неправильный месяц
                },
                "error_field": "expiry_date"
            },
            {
                "data": {
                    "card_number": "5555555555554444",
                    "card_holder": "Ivanov Ivan",
                    "expiry_date": "12/2"  # Неправильный формат года
                },
                "error_field": "expiry_date"
            }
        ]

        for test_case in test_cases:
            with self.subTest(test_case=test_case):
                with self.assertRaises(ValidationError):
                    CardSchema(**test_case["data"])

    def test_payout_create_schema_valid(self):
        """Тест валидных данных создания выплаты"""
        valid_data = {
            "amount": Decimal("100.50"),
            "currency": Currency.USD,
            "description": "Test payout",
            "recipient_details": {
                "card_number": "5555555555554444",
                "card_holder": "Ivanov Ivan",
                "expiry_date": "12/25"
            }
        }

        payout = PayoutCreateSchema(**valid_data)
        self.assertEqual(payout.amount, Decimal("100.50"))
        self.assertEqual(payout.currency, Currency.USD)
        self.assertEqual(payout.description, "Test payout")
        self.assertIsInstance(payout.recipient_details, CardSchema)

    def test_payout_create_schema_invalid_amount(self):
        """Тест невалидной суммы"""
        invalid_data = {
            "amount": Decimal("0.00"),  # Должно быть > 0
            "currency": Currency.USD,
            "recipient_details": {
                "card_number": "5555555555554444",
                "card_holder": "Ivanov Ivan",
                "expiry_date": "12/25"
            }
        }

        with self.assertRaises(ValidationError):
            PayoutCreateSchema(**invalid_data)

        # Отрицательная сумма
        invalid_data["amount"] = Decimal("-100.00")
        with self.assertRaises(ValidationError):
            PayoutCreateSchema(**invalid_data)

    def test_payout_update_schema(self):
        """Тест схемы обновления выплаты"""
        # Обновление только статуса
        data1 = {"status": Status.COMPLETED}
        update1 = PayoutUpdateSchema(**data1)
        self.assertEqual(update1.status, Status.COMPLETED)
        self.assertIsNone(update1.description)

        # Обновление только описания
        data2 = {"description": "New description"}
        update2 = PayoutUpdateSchema(**data2)
        self.assertIsNone(update2.status)
        self.assertEqual(update2.description, "New description")

        # Обновление обоих полей
        data3 = {
            "status": Status.FAILED,
            "description": "Failed payment"
        }
        update3 = PayoutUpdateSchema(**data3)
        self.assertEqual(update3.status, Status.FAILED)
        self.assertEqual(update3.description, "Failed payment")

    def test_payout_response_schema(self):
        """Тест схемы ответа выплаты"""
        response_data = {
            "id": uuid.uuid4(),
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:35:00Z",
            "status": Status.PENDING,
            "description": "Test payout",
            "amount": Decimal("100.50"),
            "currency": Currency.USD,
            "recipient_details": {
                "card_number": "5555555555554444",
                "card_holder": "Ivanov Ivan",
                "expiry_date": "12/25"
            }
        }

        response = PayoutResponseSchema(**response_data)
        self.assertEqual(response.id, response_data["id"])
        self.assertEqual(response.status, Status.PENDING)
        self.assertEqual(response.amount, Decimal("100.50"))
        self.assertEqual(response.currency, Currency.USD)

    def test_error_schema(self):
        """Тест схемы ошибки"""
        error_data = {
            "detail": "Not found",
            "code": "not_found",
            "field": "id"
        }

        error = ErrorSchema(**error_data)
        self.assertEqual(error.detail, "Not found")
        self.assertEqual(error.code, "not_found")
        self.assertEqual(error.field, "id")

        # Только обязательное поле
        error_data2 = {"detail": "Internal server error"}
        error2 = ErrorSchema(**error_data2)
        self.assertEqual(error2.detail, "Internal server error")
        self.assertIsNone(error2.code)
        self.assertIsNone(error2.field)

    def test_validation_error_schema(self):
        """Тест схемы ошибки валидации"""
        validation_errors = {
            "detail": [
                {"loc": ["body", "amount"], "msg": "must be greater than 0"},
                {"loc": ["body", "card_number"], "msg": "invalid format"}
            ]
        }

        error = ValidationErrorSchema(**validation_errors)
        self.assertEqual(len(error.detail), 2)
        self.assertEqual(error.detail[0]["msg"], "must be greater than 0")