import django.dispatch


sig_entity_new = django.dispatch.Signal(providing_args=['entity'])
"""Сигнализирует о добавлении новой сущности."""

sig_entity_published = django.dispatch.Signal(providing_args=['entity'])
"""Сигнализирует о публикации новой сущности."""

sig_support_changed = django.dispatch.Signal()
"""Сигнализирует о том, что пользователь проголосовал за материал или отозвал голос."""

sig_integration_failed = django.dispatch.Signal(providing_args=['description'])
"""Сигнализирует о неисправности в процессах интеграции со внешними сервисами."""

sig_send_generic_telegram = django.dispatch.Signal(providing_args=['text'])
"""Сингал отправки сообщения в Telegram."""
