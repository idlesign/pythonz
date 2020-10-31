import django.dispatch


sig_entity_new = django.dispatch.Signal()
"""Сигнализирует о добавлении новой сущности.
Аргументы: entity

"""

sig_entity_published = django.dispatch.Signal()
"""Сигнализирует о публикации новой сущности.
Аргументы: entity

"""

sig_support_changed = django.dispatch.Signal()
"""Сигнализирует о том, что пользователь проголосовал за материал или отозвал голос."""

sig_integration_failed = django.dispatch.Signal()
"""Сигнализирует о неисправности в процессах интеграции со внешними сервисами.
Аргументы: description

"""

sig_send_generic_telegram = django.dispatch.Signal()
"""Сингал отправки сообщения в Telegram.
Аргументы: text

"""
