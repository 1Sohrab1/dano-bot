from . import content, handlers
from .filters import AdminFilter
from .router import admins

admins.message.filter(AdminFilter())
admins.include_router(content.content_admin)

__all__ = ["admins", "handlers"]
