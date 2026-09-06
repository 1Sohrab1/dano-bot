from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class UserNavAction(StrEnum):
    HELP = "help"
    START = "start"


class UserNav(CallbackData, prefix="usernav"):
    action: UserNavAction
