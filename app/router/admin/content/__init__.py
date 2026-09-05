from ..filters import AdminCallbackQueryFilter, AdminFilter
from . import handlers
from .router import content_admin

content_admin.message.filter(AdminFilter())
content_admin.callback_query.filter(AdminCallbackQueryFilter())

__all__ = ["content_admin", "handlers"]