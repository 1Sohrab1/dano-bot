from datetime import UTC, datetime

from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.database.database import get_session
from app.database.models import Admin, Content, ContentState, User


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


class ContentCodeCollisionError(Exception):
    pass


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value

    return value.replace(tzinfo=UTC)


def _normalize_content_datetimes(content: Content) -> Content:
    content.created_at = _normalize_datetime(content.created_at)
    content.expires_at = _normalize_datetime(content.expires_at)
    return content


async def create_content(
    *,
    source_chat_id: int,
    source_message_id: int,
    content_type: str,
    code: str,
    state: str = ContentState.ACTIVE,
    expires_at: datetime | None = None,
) -> Content:
    async with get_session() as session:
        content = Content(
            source_chat_id=source_chat_id,
            source_message_id=source_message_id,
            content_type=content_type,
            code=code,
            state=state,
            expires_at=expires_at,
        )
        session.add(content)
        try:
            await session.commit()
        except IntegrityError as error:
            await session.rollback()
            raise ContentCodeCollisionError from error

        await session.refresh(content)
        return _normalize_content_datetimes(content)


async def get_content_by_code(code: str) -> Content | None:
    async with get_session() as session:
        result = await session.exec(select(Content).where(Content.code == code))
        content = result.one_or_none()

        if content is None:
            return None

        return _normalize_content_datetimes(content)


async def activate_content(code: str) -> Content | None:
    return await _set_content_state(code, ContentState.ACTIVE)


async def deactivate_content(code: str) -> Content | None:
    return await _set_content_state(code, ContentState.INACTIVE)


async def _set_content_state(code: str, state: str) -> Content | None:
    async with get_session() as session:
        result = await session.exec(select(Content).where(Content.code == code))
        content = result.one_or_none()
        if content is None:
            return None

        content.state = state
        session.add(content)
        await session.commit()
        await session.refresh(content)
        return _normalize_content_datetimes(content)
