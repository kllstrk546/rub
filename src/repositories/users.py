from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        return await self.session.get(User, user_id)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create_or_update_from_telegram(self, telegram_user: Any) -> User:
        telegram_id = _read_telegram_attr(telegram_user, "id")
        if telegram_id is None:
            raise ValueError("telegram_user must have an id field")

        user = await self.get_by_telegram_id(int(telegram_id))
        if user is None:
            user = User(telegram_id=int(telegram_id))
            self.session.add(user)

        user.username = _read_telegram_attr(telegram_user, "username")
        user.first_name = _read_telegram_attr(telegram_user, "first_name")
        user.last_name = _read_telegram_attr(telegram_user, "last_name")

        await self.session.flush()
        return user

    async def set_admin(self, telegram_id: int, is_admin: bool = True) -> User | None:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            return None

        user.is_admin = is_admin
        await self.session.flush()
        return user

    async def approve_user(self, telegram_id: int) -> User | None:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            return None

        user.is_approved = True
        await self.session.flush()
        return user

    async def revoke_user(self, telegram_id: int) -> User | None:
        user = await self.get_by_telegram_id(telegram_id)
        if user is None:
            return None

        user.is_approved = False
        await self.session.flush()
        return user

    async def list_approved_users(self) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.is_approved.is_(True)).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_admins(self) -> list[User]:
        result = await self.session.execute(
            select(User).where(User.is_admin.is_(True)).order_by(User.created_at.asc())
        )
        return list(result.scalars().all())

    async def is_admin(self, telegram_id: int) -> bool:
        user = await self.get_by_telegram_id(telegram_id)
        return bool(user and user.is_admin)

    async def is_approved(self, telegram_id: int) -> bool:
        user = await self.get_by_telegram_id(telegram_id)
        return bool(user and user.is_approved)


def _read_telegram_attr(telegram_user: Any, field: str) -> Any:
    if isinstance(telegram_user, dict):
        return telegram_user.get(field)

    return getattr(telegram_user, field, None)
