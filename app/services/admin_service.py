from app.database.repositories import is_admin as repository_is_admin


async def is_admin(user_id: int) -> bool:
    return await repository_is_admin(user_id)
