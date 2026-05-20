"""认证异常类"""


class AuthException(Exception):
    """认证异常基类"""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


class InvalidTokenError(AuthException):
    """无效的Token"""
    def __init__(self, message: str = "无效的Token"):
        super().__init__(status_code=401, message=message)


class TokenExpiredError(AuthException):
    """Token过期"""
    def __init__(self, message: str = "Token已过期"):
        super().__init__(status_code=401, message=message)


class MissingTokenError(AuthException):
    """缺少Token"""
    def __init__(self, message: str = "缺少认证Token"):
        super().__init__(status_code=401, message=message)


class InvalidCredentialsError(AuthException):
    """凭证无效"""
    def __init__(self, message: str = "用户名或密码错误"):
        super().__init__(status_code=401, message=message)


class UserAlreadyExistsError(AuthException):
    """用户已存在"""
    def __init__(self, message: str = "用户已存在"):
        super().__init__(status_code=409, message=message)


class TokenRevokedError(AuthException):
    """Token已被撤销"""
    def __init__(self, message: str = "Token已被撤销"):
        super().__init__(status_code=401, message=message)


class AccessTokenRequired(AuthException):
    """需要访问Token"""
    def __init__(self, message: str = "仅允许访问Token"):
        super().__init__(status_code=422, message=message)


class RefreshTokenRequired(AuthException):
    """需要刷新Token"""
    def __init__(self, message: str = "仅允许刷新Token"):
        super().__init__(status_code=422, message=message)
