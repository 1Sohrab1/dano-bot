from app.middlewares.rate_limit import ADMIN_SCOPE, RateLimitMiddleware

from . import callbacks, content, handlers
from .filters import AdminCallbackQueryFilter, AdminFilter
from .router import admins

admins.message.filter(AdminFilter())
admins.callback_query.filter(AdminCallbackQueryFilter())
admins.message.middleware(RateLimitMiddleware(scope=ADMIN_SCOPE))
admins.callback_query.middleware(RateLimitMiddleware(scope=ADMIN_SCOPE))
admins.include_router(content.content_admin)

__all__ = ["admins", "callbacks", "handlers"]
