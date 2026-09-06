from enum import StrEnum

from aiogram.filters.callback_data import CallbackData


class ContentUxAction(StrEnum):
    LIST = "list"
    DETAIL = "detail"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    DELETE_START = "delete_start"
    DELETE_CONFIRM = "delete_confirm"
    EXPIRE = "expire"
    EXPIRE_OFF = "expire_off"
    CANCEL = "cancel"


class ContentUx(CallbackData, prefix="cm"):
    action: ContentUxAction
    code: str = ""
    page: int = 1