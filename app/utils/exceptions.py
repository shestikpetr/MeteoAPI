class MeteoAPIException(Exception):
    """Базовое исключение для API"""
    status_code = 500
    message = "Внутренняя ошибка сервера"

    def __init__(self, message=None, status_code=None):
        if message:
            self.message = message
        if status_code:
            self.status_code = status_code
        super().__init__(self.message)


class ValidationError(MeteoAPIException):
    status_code = 400
    message = "Ошибка валидации данных"


class AuthenticationError(MeteoAPIException):
    status_code = 401
    message = "Ошибка аутентификации"


class AuthorizationError(MeteoAPIException):
    status_code = 403
    message = "Доступ запрещен"


class NotFoundError(MeteoAPIException):
    status_code = 404
    message = "Ресурс не найден"


class ConflictError(MeteoAPIException):
    status_code = 409
    message = "Конфликт данных"
