from decimal import Decimal
import uuid
from unittest.mock import patch, MagicMock

from django.http import Http404
from django.test import TestCase

from api_payouts.models import Payout, Currency, Status, PayoutManager


class PayoutModelTestCase(TestCase):
    def setUp(self):
        self.card_data = {
            "card_number": "5555555555554444",
            "card_holder": "Ivanov Ivan",
            "expiry_date": "12/25"
        }

        self.payout_data = {
            "amount": Decimal("100.50"),
            "currency": Currency.USD,
            "status": Status.PENDING,
            "description": "Test payout",
            "recipient_details": self.card_data
        }

    def test_create_payout(self):
        """Тест создания выплаты в базе данных"""
        payout = Payout.objects.create(**self.payout_data)

        self.assertIsNotNone(payout.id)
        self.assertEqual(payout.amount, Decimal("100.50"))
        self.assertEqual(payout.currency, Currency.USD)
        self.assertEqual(payout.status, Status.PENDING)
        self.assertEqual(payout.description, "Test payout")
        self.assertEqual(payout.recipient_details, self.card_data)
        self.assertIsNotNone(payout.created_at)
        self.assertIsNotNone(payout.updated_at)

    def test_payout_str_representation(self):
        """Тест строкового представления выплаты"""
        payout = Payout.objects.create(**self.payout_data)

        str_repr = str(payout)
        self.assertIn(str(payout.id), str_repr)
        self.assertIn(str(payout.amount), str_repr)
        self.assertIn(payout.currency.value, str_repr)

    def test_payout_manager_get_payout(self):
        """Тест менеджера для получения выплаты"""
        payout = Payout.objects.create(**self.payout_data)

        # Получаем выплату через менеджер
        retrieved = Payout.objects.get_payout(str(payout.id))

        self.assertEqual(retrieved.id, payout.id)

        # Пытаемся получить несуществующую выплату
        with self.assertRaises(Http404):
            Payout.objects.get_payout(str(uuid.uuid4()))

    def test_payout_manager_create_payout(self):
        """Тест создания выплаты через менеджер"""
        # Создаем выплату через менеджер
        payout = Payout.objects.create_payout(**self.payout_data)

        self.assertIsNotNone(payout.id)
        self.assertEqual(payout.amount, Decimal("100.50"))
        self.assertEqual(payout.currency, Currency.USD)
        self.assertEqual(payout.status, Status.PENDING)  # Должен быть установлен по умолчанию
        self.assertEqual(payout.description, "Test payout")
        self.assertEqual(payout.recipient_details, self.card_data)

    def test_payout_manager_update_payout(self):
        """Тест обновления выплаты через менеджер"""
        # Создаем выплату
        payout = Payout.objects.create(**self.payout_data)
        payout_id = str(payout.id)

        # Обновляем через менеджер
        update_data = {
            "status": Status.COMPLETED,
            "description": "Updated description"
        }

        updated = Payout.objects.update_payout(
            payout_id=payout_id,
            **update_data  # Убрали payload, так как метод принимает **kwargs
        )

        # Обновляем объект из базы данных
        payout.refresh_from_db()

        self.assertEqual(payout.status, Status.COMPLETED)
        self.assertEqual(payout.description, "Updated description")

    def test_payout_manager_delete_payout(self):
        """Тест удаления выплаты через менеджер"""
        # Создаем выплату
        payout = Payout.objects.create(**self.payout_data)
        payout_id = str(payout.id)

        # Удаляем через менеджер
        Payout.objects.delete_payout(payout_id)

        # Проверяем, что выплата больше не существует
        with self.assertRaises(Payout.DoesNotExist):
            Payout.objects.get(id=payout.id)

    def test_payout_manager_delete_payout_with_mock(self):
        """Тест удаления выплаты через менеджер с моком"""
        with patch.object(PayoutManager, 'get_queryset') as mock_get_queryset:
            # Создаем мок queryset
            mock_queryset = MagicMock()
            mock_payout = MagicMock()
            mock_queryset.get_by_id.return_value = mock_payout

            mock_get_queryset.return_value = mock_queryset

            # Удаляем через менеджер
            payout_id = str(uuid.uuid4())
            Payout.objects.delete_payout(payout_id)

            # Проверяем вызовы
            mock_queryset.get_by_id.assert_called_once_with(payout_id)
            mock_payout.delete.assert_called_once()

    def test_payout_manager_update_payout_with_mock(self):
        """Тест обновления выплаты через менеджер с моком"""
        with patch.object(PayoutManager, 'get_queryset') as mock_get_queryset:
            # Создаем мок queryset и payout
            mock_queryset = MagicMock()
            mock_payout = MagicMock()
            mock_queryset.get_by_id.return_value = mock_payout

            mock_get_queryset.return_value = mock_queryset

            # Обновляем через менеджер
            payout_id = str(uuid.uuid4())
            update_data = {
                "status": Status.COMPLETED,
                "description": "Updated description"
            }

            result = Payout.objects.update_payout(payout_id, **update_data)

            # Проверяем вызовы
            mock_queryset.get_by_id.assert_called_once_with(payout_id)

            # Проверяем, что установлены атрибуты
            self.assertEqual(mock_payout.status, Status.COMPLETED)
            self.assertEqual(mock_payout.description, "Updated description")

            mock_payout.save.assert_called_once()
            self.assertEqual(result, mock_payout)

    def test_currency_enum(self):
        """Тест перечисления валют"""
        self.assertEqual(Currency.USD.value, "USD")
        self.assertEqual(Currency.EUR.value, "EUR")

        # Проверка значений
        currencies = [c.value for c in Currency]
        self.assertIn("USD", currencies)
        self.assertIn("EUR", currencies)

    def test_status_enum(self):
        """Тест перечисления статусов"""
        self.assertEqual(Status.PENDING.value, "pending")
        self.assertEqual(Status.PROCESSING.value, "processing")
        self.assertEqual(Status.COMPLETED.value, "completed")
        self.assertEqual(Status.FAILED.value, "failed")
        self.assertEqual(Status.CANCELLED.value, "cancelled")

        # Проверка значений
        statuses = [s.value for s in Status]
        self.assertIn("pending", statuses)
        self.assertIn("completed", statuses)
        self.assertIn("failed", statuses)