import logging

from django.db import models
from uuid import uuid4

from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)

class Status(models.TextChoices):
    PENDING = 'pending', 'Ожидание'
    PROCESSING = 'processing', 'В обработке'
    COMPLETED = 'completed', 'Выплачено'
    FAILED = 'failed', 'Ошибка'
    CANCELLED = 'cancelled', 'Отменено'

class Currency(models.TextChoices):
    RUB = 'RUB', 'Российский рубль'
    USD = 'USD', 'Доллар США'
    EUR = 'EUR', 'Евро'

class PayoutQuerySet(models.QuerySet):

    def get_by_id(self, payout_id: str) -> 'Payout':
        return get_object_or_404(self, id=payout_id)


class PayoutManager(models.Manager):

    def get_queryset(self):
        return PayoutQuerySet(self.model, using=self._db)


    def get_payout(self, payout_id: str) -> 'Payout':
        return self.get_queryset().get_by_id(payout_id)

    def create_payout(self, **kwargs) -> 'Payout':
        kwargs.setdefault('status', Status.PENDING)
        return self.create(**kwargs)

    def update_payout(self, payout_id: str, **kwargs) -> 'Payout':
        payout = self.get_queryset().get_by_id(payout_id)
        for key, value in kwargs.items():
            if hasattr(payout, key):
                setattr(payout, key, value)
        payout.save()
        return payout

    def delete_payout(self, payout_id: str) -> None:
        payout = self.get_queryset().get_by_id(payout_id)
        payout.delete()

class Payout(models.Model):

    id = models.UUIDField(
        primary_key=True,
        default=uuid4,
        editable=False,
        verbose_name='Идентификатор'
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Сумма выплаты'
    )

    currency = models.CharField(
        max_length=3,
        choices=Currency.choices,
        default=Currency.RUB,
        verbose_name='Валюта'
    )

    recipient_details = models.JSONField(
        verbose_name='Реквизиты получателя'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name='Статус заявки'
    )

    description = models.TextField(
        blank=True,
        null=True,
        verbose_name='Описание/Комментарий'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    objects = PayoutManager()

    class Meta:
        verbose_name = 'Заявка на выплату'
        verbose_name_plural = 'Заявки на выплату'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def mark_as_pending(self) -> None:
        """Отметить как обрабатываемую"""
        self.status = Status.PENDING
        self.save(update_fields=['status', 'updated_at'])

    def mark_as_processing(self) -> None:
        """Отметить как обрабатываемую"""
        self.status = Status.PROCESSING
        self.save(update_fields=['status', 'updated_at'])

    def mark_as_completed(self) -> None:
        """Отметить как завершенную"""
        self.status = Status.COMPLETED
        self.save(update_fields=['status', 'updated_at'])

    def mark_as_failed(self, error_message: str = None) -> None:
        """Отметить как неудачную"""
        self.status = Status.FAILED
        if error_message:
            self.description += f'\n {error_message}'
        self.save(update_fields=['status', 'description', 'updated_at'])

    def mark_as_cancelled(self) -> None:
        """Отметить как отмененную"""
        self.status = Status.CANCELLED
        self.save(update_fields=['status', 'updated_at'])

    def can_be_processed(self) -> bool:
        """Можно ли обрабатывать выплату"""
        return self.status in [Status.PENDING, Status.FAILED]

    def is_completed(self) -> bool:
        """Завершена ли выплата"""
        return self.status == Status.COMPLETED

    def is_processing(self) -> bool:
        """В процессе ли обработки"""
        return self.status == Status.PROCESSING

    def is_failed(self) -> bool:
        """В ошибке"""
        return self.status == Status.FAILED

    def is_pending(self) -> bool:
        """В ожидании ли обработки"""
        return self.status == Status.PENDING

    def is_cancelled(self) -> bool:
        """Отменена"""
        return self.status == Status.CANCELLED

    def __str__(self):
        return f"Выплата {self.id} - {self.amount} {self.currency}"
