from aiogram.filters.callback_data import CallbackData


class AdminNavAction:
    DASHBOARD = "dashboard"
    UPLOAD = "upload"
    MANAGE = "manage"
    HELP = "help"


class AdminNav(CallbackData, prefix="adminnav"):
    action: str
