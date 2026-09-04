from . import handlers
from .filters import UserFilter
from .middleware import UserMiddleware
from .router import users

users.message.filter(UserFilter())
users.message.middleware(UserMiddleware())

__all__ = ["users"]
