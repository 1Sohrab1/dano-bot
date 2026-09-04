from . import handlers
from .filters import UserFilter
from .router import users

users.message.filter(UserFilter())

<<<<<<< Updated upstream
__all__ = ["handlers", "users"]
=======
__all__ = ["users"]
>>>>>>> Stashed changes
