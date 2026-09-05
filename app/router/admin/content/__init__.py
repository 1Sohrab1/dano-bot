from app.middlewares.rate_limit import ADMIN_SCOPE, RateLimitMiddleware

from ..filters import AdminCallbackQueryFilter, AdminFilter
from . import handlers
from .router import content_admin

content_admin.message.filter(AdminFilter())
content_admin.callback_query.filter(AdminCallbackQueryFilter())
content_admin.callback_query.middleware(RateLimitMiddleware(scope=ADMIN_SCOPE))

__all__ = ["content_admin", "handlers"]