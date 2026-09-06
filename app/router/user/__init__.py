from app.middlewares.rate_limit import USER_SCOPE, RateLimitMiddleware

from . import callbacks, handlers
from .filters import UserCallbackQueryFilter, UserFilter
from .router import users

users.message.filter(UserFilter())
users.callback_query.filter(UserCallbackQueryFilter())
users.message.middleware(RateLimitMiddleware(scope=USER_SCOPE))
users.callback_query.middleware(RateLimitMiddleware(scope=USER_SCOPE))

__all__ = ["callbacks", "handlers", "users"]
