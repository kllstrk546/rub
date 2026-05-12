from datetime import datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import RateSnapshot


class RateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_snapshot(
        self,
        *,
        nobitex_usdt_toman: Decimal,
        rapira_usdt_rub_base: Decimal,
        rapira_usdt_rub_with_margin: Decimal,
        margin_percent: Decimal,
        rub_toman_raw: Decimal,
        rub_toman_display: int,
        nobitex_message_id: int | None = None,
        nobitex_message_date: datetime | None = None,
        rapira_message_id: int | None = None,
        rapira_message_date: datetime | None = None,
        refresh_reason: str = "startup",
        bitcoin_usd: int | None = None,
        gold_ounce_usd: int | None = None,
        oil_usd: Decimal | None = None,
    ) -> RateSnapshot:
        snapshot = RateSnapshot(
            nobitex_usdt_toman=nobitex_usdt_toman,
            rapira_usdt_rub_base=rapira_usdt_rub_base,
            rapira_usdt_rub_with_margin=rapira_usdt_rub_with_margin,
            margin_percent=margin_percent,
            rub_toman_raw=rub_toman_raw,
            rub_toman_display=rub_toman_display,
            nobitex_message_id=nobitex_message_id,
            nobitex_message_date=nobitex_message_date,
            rapira_message_id=rapira_message_id,
            rapira_message_date=rapira_message_date,
            refresh_reason=refresh_reason,
            bitcoin_usd=bitcoin_usd,
            gold_ounce_usd=gold_ounce_usd,
            oil_usd=oil_usd,
        )
        self.session.add(snapshot)
        await self.session.flush()
        return snapshot

    async def get_latest_snapshot(self) -> RateSnapshot | None:
        result = await self.session.execute(
            select(RateSnapshot).order_by(RateSnapshot.created_at.desc(), RateSnapshot.id.desc()).limit(1)
        )
        return result.scalar_one_or_none()
