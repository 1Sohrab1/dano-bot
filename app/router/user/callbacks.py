from aiogram.filters.callback_data import CallbackData


class UserNavAction:
    HELP = "help"
    START = "start"


class UserNav(CallbackData, prefix="usernav"):
    action: str
