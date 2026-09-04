from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.database import get_session
from app.database.models import Admin, User


async def get_user_by_telegram_id(telegram_id: int) -> User | None:
    async with get_session() as session:
        result = await session.exec(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.one_or_none()


async def get_or_create_user(telegram_id: int) -> User:
    existing = await get_user_by_telegram_id(telegram_id)
    if existing is not None:
        return existing

    async with get_session() as session:
        user = User(telegram_id=telegram_id)
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            result = await session.exec(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.one()

        await session.refresh(user)
        return user


async def get_admin_by_telegram_id(telegram_id: int) -> Admin | None:
    async with get_session() as session:
        result = await session.exec(
            select(Admin).where(Admin.telegram_id == telegram_id)
        )
        return result.one_or_none()


async def is_admin(telegram_id: int) -> bool:
    admin = await get_admin_by_telegram_id(telegram_id)
    return admin is not None


async def list_admin_telegram_ids() -> list[int]:
    async with get_session() as session:
        result = await session.exec(select(Admin.telegram_id))
        return list(result.all())


async def delete_admin_by_telegram_id(telegram_id: int) -> None:
    async with get_session() as session:
        result = await session.exec(
            select(Admin).where(Admin.telegram_id == telegram_id)
        )
        admin = result.one_or_none()
        if admin is None:
            return

        await session.delete(admin)
        await session.commit()


async def get_or_create_admin(telegram_id: int) -> Admin:
    user = await get_or_create_user(telegram_id)
    if user.id is None:
        raise RuntimeError("persisted user is missing an id")

    existing = await get_admin_by_telegram_id(telegram_id)
    if existing is not None:
        return existing

    async with get_session() as session:
        admin = Admin(telegram_id=telegram_id, user_id=user.id)
        session.add(admin)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            result = await session.exec(
                select(Admin).where(Admin.telegram_id == telegram_id)
            )
            return result.one()

        await session.refresh(admin)
        return admin
