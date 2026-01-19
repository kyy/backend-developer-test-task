import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone
from ninja.testing import TestClient

from api_payouts.models import Payout, Currency, Status
from api_payouts.api import router
from api_payouts.schemas import PayoutCreateSchema, CardSchema, PayoutResponseSchema, PayoutUpdateSchema


class PayoutAPITestCase(TestCase):
    def setUp(self):
        self.client = TestClient(router)

        # Тестовые данные
        self.card_data = {
            "card_number": "5555555555554444",
            "card_holder": "Ivanov Ivan",
            "expiry_date": "12/25"
        }

        self.payout_data = {
            "amount": "100.50",
            "currency": Currency.USD.value,
            "description": "Test payout",
            "recipient_details": self.card_data
        }

        self.update_data = {
            "status": Status.COMPLETED.value,
            "description": "Updated description"
        }

        # Создаем тестовую выплату
        self.payout = Payout.objects.create(
            amount=Decimal("100.50"),
            currency=Currency.USD,
            description="Test payout",
            recipient_details=self.card_data
        )

    def test_list_payouts_success(self):
        """Тест получения списка выплат"""
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), dict)

        # Проверяем пагинацию
        self.assertIn("items", response.json())
        self.assertIn("count", response.json())

    def test_get_payout_success(self):
        """Тест получения конкретной выплаты"""
        response = self.client.get(f"/{self.payout.id}/")

        self.assertEqual(response.status_code, 200)
        data = response.json()

        self.assertEqual(str(self.payout.id), data["id"])
        self.assertEqual(str(self.payout.amount), data["amount"])
        self.assertEqual(self.payout.currency.value, data["currency"])

    def test_get_payout_not_found(self):
        """Тест получения несуществующей выплаты"""
        non_existent_id = uuid.uuid4()
        response = self.client.get(f"/{non_existent_id}/")

        self.assertEqual(response.status_code, 404)

    @patch('api_payouts.services.payout_service.PayoutService.create_payout')
    @patch('api_payouts.services.payout_service.PayoutService.execute_payout')
    def test_create_payout_success(self, mock_execute, mock_create):
        """Тест создания выплаты"""
        # Настраиваем моки
        payout_data = {
            "id": uuid.uuid4(),  # Добавляем id
            "amount": Decimal("100.50"),
            "currency": Currency.USD,
            "description": "Test payout",
            "recipient_details": self.card_data,
            "created_at": timezone.now(),
            "updated_at": timezone.now(),
            "status": Status.PENDING
        }


        mock_payout = PayoutResponseSchema(**payout_data)
        mock_create.return_value = mock_payout
        mock_execute.return_value = {"task_id": "test_task_id"}

        response = self.client.post("/", json=self.payout_data)

        self.assertEqual(response.status_code, 200)
        mock_create.assert_called_once()
        mock_execute.assert_called_once_with(str(mock_payout.id))

    def test_create_payout_validation_error(self):
        """Тест создания выплаты с невалидными данными"""
        invalid_data = {
            "amount": "-100.50",  # Отрицательная сумма
            "currency": "INVALID",  # Невалидная валюта
            "recipient_details": {
                "card_number": "123",  # Слишком короткий номер
                "card_holder": "IV",  # Слишком короткое имя
                "expiry_date": "13/25"  # Невалидный месяц
            }
        }

        response = self.client.post("/", json=invalid_data)

        self.assertEqual(response.status_code, 422)

        errors = response.json()
        self.assertIn("detail", errors)

        # Проверяем конкретные ошибки валидации
        error_details = errors["detail"]
        error_fields = [error.get("loc")[-1] for error in error_details]

        self.assertIn("amount", error_fields)
        self.assertIn("currency", error_fields)

    @patch('api_payouts.services.payout_service.PayoutService.update_payout')
    def test_update_payout_success(self, mock_update):
        """Тест обновления выплаты"""
        mock_update.return_value = self.payout

        response = self.client.patch(f"/{self.payout.id}/", json=self.update_data)

        self.assertEqual(response.status_code, 200)

        # Проверяем, что метод был вызван с правильными аргументами
        mock_update.assert_called_once()

        # Получаем фактические аргументы вызова
        call_args = mock_update.call_args
        self.assertEqual(call_args.kwargs['payout_id'], str(self.payout.id))

        # Проверяем, что payload является экземпляром PayoutUpdateSchema
        payload = call_args.kwargs['payload']
        self.assertIsInstance(payload, PayoutUpdateSchema)

        # Проверяем содержимое
        self.assertEqual(payload.status, Status.COMPLETED)
        self.assertEqual(payload.description, "Updated description")

    def test_update_payout_partial(self):
        """Тест частичного обновления"""
        partial_data = {"description": "Only description updated"}

        with patch('api_payouts.services.payout_service.PayoutService.update_payout') as mock_update:
            mock_update.return_value = self.payout
            response = self.client.patch(f"/{self.payout.id}/", json=partial_data)

            self.assertEqual(response.status_code, 200)

    @patch('api_payouts.services.payout_service.PayoutService.delete_payout')
    def test_delete_payout_success(self, mock_delete):
        """Тест удаления выплаты"""
        mock_delete.return_value = {"success": True}

        response = self.client.delete(f"/{self.payout.id}/")

        self.assertEqual(response.status_code, 200)
        mock_delete.assert_called_once_with(payout_id=str(self.payout.id))

    def test_card_schema_validation(self):
        """Тест валидации данных карты"""
        # Валидные данные
        valid_card = CardSchema(**self.card_data)
        self.assertEqual(valid_card.card_number, "5555555555554444")
        self.assertEqual(valid_card.card_holder, "Ivanov Ivan")

        # Невалидный номер карты
        with self.assertRaises(ValueError):
            CardSchema(
                card_number="123",  # Слишком короткий
                card_holder="Ivanov Ivan",
                expiry_date="12/25"
            )

        # Невалидный держатель карты
        with self.assertRaises(ValueError):
            CardSchema(
                card_number="5555555555554444",
                card_holder="ivanov ivan",  # С маленькой буквы
                expiry_date="12/25"
            )

        # Невалидная дата
        with self.assertRaises(ValueError):
            CardSchema(
                card_number="5555555555554444",
                card_holder="Ivanov Ivan",
                expiry_date="13/25"  # Неправильный месяц
            )

    def test_payout_create_schema_validation(self):
        """Тест валидации схемы создания выплаты"""
        # Валидные данные
        valid_data = self.payout_data.copy()
        valid_data["amount"] = Decimal("100.50")

        schema = PayoutCreateSchema(**valid_data)
        self.assertEqual(schema.amount, Decimal("100.50"))
        self.assertEqual(schema.currency, Currency.USD)

        # Невалидная сумма (0 или отрицательная)
        invalid_data = valid_data.copy()
        invalid_data["amount"] = Decimal("0.00")

        with self.assertRaises(ValueError):
            PayoutCreateSchema(**invalid_data)

    def test_pagination(self):
        """Тест пагинации"""
        # Создаем дополнительные выплаты для теста пагинации
        for i in range(15):
            Payout.objects.create(
                amount=Decimal(f"{i + 1}.00"),
                currency=Currency.USD,
                status=Status.PENDING,
                recipient_details=self.card_data
            )

        response = self.client.get("/?page=2")
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("items", data)
        self.assertIn("count", data)
        self.assertLessEqual(len(data["items"]), 10)  # page_size=10