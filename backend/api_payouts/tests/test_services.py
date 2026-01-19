import uuid
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.http import Http404
from django.test import TestCase

from api_payouts.models import Payout, Currency, Status
from api_payouts.schemas import PayoutCreateSchema, PayoutUpdateSchema
from api_payouts.services.payout_service import PayoutService
from api_payouts.services.payout_crud_service import PayoutCRUDService
from api_payouts.services.payout_task_service import PayoutTaskService


class PayoutCRUDServiceTestCase(TestCase):
    def setUp(self):
        self.card_data = {
            "card_number": "5555555555554444",
            "card_holder": "Ivanov Ivan",
            "expiry_date": "12/25"
        }

        self.payout_data = {
            "amount": Decimal("100.50"),
            "currency": Currency.USD,
            "description": "Test payout",
            "recipient_details": self.card_data
        }

        # Создаем тестовую выплату
        self.payout = Payout.objects.create(
            **self.payout_data,
            status=Status.PENDING
        )

    def test_get_list_payouts(self):
        """Тест получения списка выплат"""
        payouts = PayoutCRUDService.get_list_payouts()

        self.assertEqual(payouts.count(), 1)
        self.assertEqual(payouts.first().id, self.payout.id)

        Payout.objects.create(
            amount=Decimal("200.00"),
            currency=Currency.EUR,
            status=Status.PENDING,
            recipient_details=self.card_data
        )

        payouts = PayoutCRUDService.get_list_payouts()
        self.assertEqual(payouts.count(), 2)

    def test_get_payout_success(self):
        """Тест получения выплаты по ID"""
        payout = PayoutCRUDService.get_payout(str(self.payout.id))

        self.assertEqual(payout.id, self.payout.id)
        self.assertEqual(payout.amount, Decimal("100.50"))
        self.assertEqual(payout.currency, Currency.USD)

    def test_get_payout_not_found(self):
        """Тест получения несуществующей выплаты"""
        with self.assertRaises(Http404):
            PayoutCRUDService.get_payout(str(uuid.uuid4()))

    @patch('api_payouts.models.PayoutManager.create_payout')
    def test_create_payout(self, mock_create_payout):
        """Тест создания выплаты"""
        mock_payout = MagicMock()
        mock_payout.id = uuid.uuid4()
        mock_create_payout.return_value = mock_payout

        payload = PayoutCreateSchema(**self.payout_data)
        result = PayoutCRUDService.create_payout(payload)

        self.assertEqual(result, mock_payout)
        mock_create_payout.assert_called_once_with(
            **self.payout_data,
            status='pending'
        )

    @patch('api_payouts.models.PayoutManager.delete_payout')
    def test_delete_payout(self, mock_delete_payout):
        """Тест удаления выплаты"""
        result = PayoutCRUDService.delete_payout(str(self.payout.id))

        self.assertEqual(result, {"success": True})
        mock_delete_payout.assert_called_once_with(payout_id=str(self.payout.id))

    @patch('api_payouts.models.PayoutManager.update_payout')
    def test_update_payout(self, mock_update_payout):
        """Тест обновления выплаты"""
        # Настраиваем мок
        updated_payout = MagicMock()
        updated_payout.id = self.payout.id
        mock_update_payout.return_value = updated_payout

        # Данные для обновления
        update_data = {
            "status": Status.COMPLETED.value,
            "description": "Updated description"
        }
        payload = PayoutUpdateSchema(**update_data)

        # Вызываем метод
        result = PayoutCRUDService.update_payout(str(self.payout.id), payload)

        # Проверяем результат
        self.assertEqual(result, updated_payout)
        mock_update_payout.assert_called_once_with(
            payout_id=str(self.payout.id),
            payload=update_data
        )

    def test_update_payout_partial(self):
        """Тест частичного обновления выплаты"""
        with patch('api_payouts.models.PayoutManager.update_payout') as mock_update_payout:
            updated_payout = MagicMock()
            mock_update_payout.return_value = updated_payout

            payload1 = PayoutUpdateSchema(status=Status.COMPLETED.value)
            result1 = PayoutCRUDService.update_payout(str(self.payout.id), payload1)


            payload2 = PayoutUpdateSchema(description="New description")
            result2 = PayoutCRUDService.update_payout(str(self.payout.id), payload2)

            self.assertEqual(mock_update_payout.call_count, 2)


class PayoutTaskServiceTestCase(TestCase):
    @patch('api_payouts.services.payout_task_service.payout_task.apply_async')
    @patch('django.db.transaction.on_commit')
    def test_execute_payout(self, mock_on_commit, mock_apply_async):
        """Тест запуска фоновой задачи"""
        payout_id = str(uuid.uuid4())

        mock_task_result = MagicMock()
        mock_task_result.id = "task_123"
        mock_apply_async.return_value = mock_task_result

        mock_callback = MagicMock()
        mock_on_commit.return_value = mock_callback

        result = PayoutTaskService.execute_payout(payout_id, countdown=5)

        self.assertEqual(result, mock_callback)
        mock_on_commit.assert_called_once()

        callback = mock_on_commit.call_args[0][0]

        callback()
        mock_apply_async.assert_called_once_with(
            args=[payout_id],
            countdown=5
        )

    @patch('api_payouts.services.payout_task_service.payout_task.apply_async')
    def test_execute_payout_default_countdown(self, mock_apply_async):
        """Тест запуска задачи с дефолтным countdown"""
        payout_id = str(uuid.uuid4())

        with patch('django.db.transaction.on_commit') as mock_on_commit:
            PayoutTaskService.execute_payout(payout_id)

            mock_on_commit.assert_called_once()

            callback = mock_on_commit.call_args[0][0]
            callback()

            mock_apply_async.assert_called_once_with(
                args=[payout_id],
                countdown=1  # Дефолтное значение
            )


class PayoutServiceIntegrationTestCase(TestCase):
    """Интеграционные тесты основного сервиса"""

    def setUp(self):
        self.service = PayoutService

        self.card_data = {
            "card_number": "5555555555554444",
            "card_holder": "Ivanov Ivan",
            "expiry_date": "12/25"
        }

        self.payout_data = {
            "amount": Decimal("100.50"),
            "currency": Currency.USD,
            "description": "Test payout",
            "recipient_details": self.card_data
        }

    def test_service_inheritance(self):
        """Тест наследования сервисов"""
        self.assertTrue(hasattr(self.service, 'get_list_payouts'))
        self.assertTrue(hasattr(self.service, 'get_payout'))
        self.assertTrue(hasattr(self.service, 'create_payout'))
        self.assertTrue(hasattr(self.service, 'update_payout'))
        self.assertTrue(hasattr(self.service, 'delete_payout'))
        self.assertTrue(hasattr(self.service, 'execute_payout'))

    @patch('api_payouts.services.payout_service.PayoutCRUDService.create_payout')
    @patch('api_payouts.services.payout_service.PayoutTaskService.execute_payout')
    def test_service_methods_call_parent(self, mock_execute, mock_create):
        """Тест, что методы вызывают родительские реализации"""
        payout_id = str(uuid.uuid4())
        mock_payout = MagicMock()
        mock_payout.id = payout_id
        mock_create.return_value = mock_payout

        # Тестируем create_payout через основной сервис
        payload = PayoutCreateSchema(**self.payout_data)
        result = self.service.create_payout(payload)

        mock_create.assert_called_once_with(payload)
        self.assertEqual(result, mock_payout)

        # Тестируем execute_payout через основной сервис
        self.service.execute_payout(payout_id, countdown=2)
        mock_execute.assert_called_once_with(payout_id, countdown=2)