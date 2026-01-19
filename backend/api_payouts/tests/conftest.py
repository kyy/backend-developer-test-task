import pytest
from decimal import Decimal
from django.test import Client
from ninja.testing import TestClient

from api_payouts.models import Payout, Currency, Status
from api_payouts.api import router


@pytest.fixture
def api_client():
    """Фикстура для API клиента"""
    return TestClient(router)


@pytest.fixture
def django_client():
    """Фикстура для Django клиента"""
    return Client()


@pytest.fixture
def card_data():
    """Фикстура с данными карты"""
    return {
        "card_number": "5555555555554444",
        "card_holder": "Ivanov Ivan",
        "expiry_date": "12/25"
    }


@pytest.fixture
def payout_data(card_data):
    """Фикстура с данными для создания выплаты"""
    return {
        "amount": Decimal("100.50"),
        "currency": Currency.USD,
        "description": "Test payout",
        "recipient_details": card_data
    }


@pytest.fixture
def payout(payout_data):
    """Фикстура с созданной выплатой"""
    return Payout.objects.create(
        **payout_data,
    )


@pytest.fixture
def update_data():
    """Фикстура с данными для обновления выплаты"""
    return {
        "status": Status.COMPLETED,
        "description": "Updated description"
    }