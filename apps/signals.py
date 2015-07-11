import django.dispatch


# Сигнализирует о добавлении новой сущности.
sig_entity_new = django.dispatch.Signal(providing_args=['entity'])

# Сигнализирует о публикации новой сущности.
sig_entity_published = django.dispatch.Signal(providing_args=['entity'])

# Сигнализирует о том, что пользователь проголосовал за материал или отозвал голос.
sig_support_changed = django.dispatch.Signal()

# Сигнализирует о поиске без результатов.
sig_search_failed = django.dispatch.Signal(providing_args=['search_term'])
