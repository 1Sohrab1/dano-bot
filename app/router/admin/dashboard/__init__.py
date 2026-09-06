from app.middlewares.rate_limit import ADMIN_SCOPE, RateLimitMiddleware

from ..filters import AdminCallbackQueryFilter
from . import handlers
from .router import dashboard_admin

dashboard_admin.callback_query.filter(AdminCallbackQueryFilter())
dashboard_admin.callback_query.middleware(RateLimitMiddleware(scope=ADMIN_SCOPE))

__all__ = ["dashboard_admin", "handlers"]
