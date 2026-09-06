from aiogram.fsm.state import State, StatesGroup


class ExpirationStates(StatesGroup):
    awaiting_days = State()