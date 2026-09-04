from . import handlers
from .filters import AdminFilter
from .middleware import AdminMiddleware
from .router import admins

admins.message.filter(AdminFilter())
admins.message.middleware(AdminMiddleware())

__all__ = ["admins"]
