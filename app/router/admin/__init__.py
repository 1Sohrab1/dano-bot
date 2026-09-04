from . import handlers as _handlers
from .filters import AdminFilter
from .router import admins

admins.message.filter(AdminFilter())

__all__ = ["admins", "handlers"]
