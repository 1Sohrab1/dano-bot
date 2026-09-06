from app.middlewares.rate_limit import ADMIN_SCOPE, RateLimitMiddleware

from . import callbacks, content, dashboard, handlers
from .filters import AdminCallbackQueryFilter, AdminFilter
from .router import admins

admins.message.filter(AdminFilter())
admins.callback_query.filter(AdminCallbackQueryFilter())
admins.message.middleware(RateLimitMiddleware(scope=ADMIN_SCOPE))
admins.include_router(content.content_admin)
admins.include_router(dashboard.dashboard_admin)

__all__ = ["admins", "callbacks", "dashboard", "handlers"]
