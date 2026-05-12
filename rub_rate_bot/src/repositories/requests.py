from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models import AccessRequest, User


class AccessRequestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_pending_request(self, user_id: int) -> AccessRequest:
        active_request = await self.get_active_pending_request(user_id)
        if active_request is not None:
            return active_request

        access_request = AccessRequest(user_id=user_id, status="pending")
        self.session.add(access_request)
        await self.session.flush()
        return access_request

    async def get_active_pending_request(self, user_id: int) -> AccessRequest | None:
        result = await self.session.execute(
            select(AccessRequest).where(
                AccessRequest.user_id == user_id,
                AccessRequest.status == "pending",
            )
        )
        return result.scalar_one_or_none()

    async def get_latest_request_for_user(self, user_id: int) -> AccessRequest | None:
        result = await self.session.execute(
            select(AccessRequest)
            .where(AccessRequest.user_id == user_id)
            .order_by(AccessRequest.created_at.desc(), AccessRequest.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_pending_requests(self) -> list[AccessRequest]:
        result = await self.session.execute(
            select(AccessRequest)
            .options(selectinload(AccessRequest.user))
            .where(AccessRequest.status == "pending")
            .order_by(AccessRequest.created_at.asc())
        )
        return list(result.scalars().all())

    async def approve_request(
        self,
        request_id: int,
        processed_by_admin_id: int | None = None,
    ) -> AccessRequest | None:
        access_request = await self._get_by_id(request_id)
        if access_request is None:
            return None

        access_request.status = "approved"
        access_request.processed_at = datetime.now(timezone.utc)
        access_request.processed_by_admin_id = processed_by_admin_id

        user = await self.session.get(User, access_request.user_id)
        if user is not None:
            user.is_approved = True

        await self.session.flush()
        return access_request

    async def reject_request(
        self,
        request_id: int,
        processed_by_admin_id: int | None = None,
    ) -> AccessRequest | None:
        access_request = await self._get_by_id(request_id)
        if access_request is None:
            return None

        access_request.status = "rejected"
        access_request.processed_at = datetime.now(timezone.utc)
        access_request.processed_by_admin_id = processed_by_admin_id

        await self.session.flush()
        return access_request

    async def _get_by_id(self, request_id: int) -> AccessRequest | None:
        return await self.session.get(AccessRequest, request_id)
