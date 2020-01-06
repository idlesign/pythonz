
class PythonzException(Exception):
    """Базовое исключение проекта. Остальные должны наследоваться от него."""

    def __init__(self, message=None, **kwargs):
        super().__init__(message, **kwargs)
        self.message = message


class RemoteSourceError(PythonzException):
    """Исключение, указывающее на то, что произошла ошибка получения данных удалённого ресурса."""


class RedirectRequired(PythonzException):
    """Исключение, сигнализирующее необходимость перенаправления.
    Используется в представлениях.

    """

class LogicError(PythonzException):
    """Логическая ошибка в приложении."""
