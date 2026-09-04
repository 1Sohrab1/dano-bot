from app.database.models import User
from app.database.repositories import get_or_create_admin, get_or_create_user


async def ensure_user(telegram_id: int) -> User:
    return await get_or_create_user(telegram_id)


async def seed_administrators(admin_ids: list[int]) -> None:
    for telegram_id in admin_ids:
        await get_or_create_admin(telegram_id)
