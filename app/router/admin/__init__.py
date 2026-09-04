from . import handlers
from .filters import AdminFilter
from .router import admins

admins.message.filter(AdminFilter())

__all__ = ["admins", "handlers"]
