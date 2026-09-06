from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class AdminNavAction(StrEnum):
    DASHBOARD = "dashboard"
    UPLOAD = "upload"
    MANAGE = "manage"
    HELP = "help"


class AdminNav(CallbackData, prefix="adminnav"):
    action: AdminNavAction
