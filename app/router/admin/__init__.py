from app.middlewares.rate_limit import ADMIN_SCOPE, RateLimitMiddleware

from . import content, handlers
from .filters import AdminFilter
from .router import admins

admins.message.filter(AdminFilter())
admins.message.middleware(RateLimitMiddleware(scope=ADMIN_SCOPE))
admins.include_router(content.content_admin)

__all__ = ["admins", "handlers"]
