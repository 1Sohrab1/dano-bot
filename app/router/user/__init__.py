from app.middlewares.rate_limit import USER_SCOPE, RateLimitMiddleware

from . import handlers
from .filters import UserFilter
from .router import users

users.message.filter(UserFilter())
users.message.middleware(RateLimitMiddleware(scope=USER_SCOPE))

__all__ = ["handlers", "users"]
