from app.database.models import User
from app.database.repositories import (
    delete_admin_by_telegram_id,
    get_or_create_admin,
    get_or_create_user,
    list_admin_telegram_ids,
)


async def ensure_user(telegram_id: int) -> User:
    return await get_or_create_user(telegram_id)


async def seed_administrators(admin_ids: list[int]) -> None:
    desired = set(admin_ids)
    current = set(await list_admin_telegram_ids())

    for telegram_id in desired - current:
        await get_or_create_admin(telegram_id)

    for telegram_id in current - desired:
        await delete_admin_by_telegram_id(telegram_id)
