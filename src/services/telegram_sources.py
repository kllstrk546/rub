import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Callable

from aiogram import Bot
from telethon import TelegramClient
from telethon.tl.custom.message import Message

from src.config import Settings
from src.db import async_session_maker
from src.models import RateSnapshot
from src.repositories.rates import RateRepository
from src.services.notification_service import notify_parse_error
from src.services.parser_service import NobitexAssets, parse_nobitex_assets, parse_rapira_usdt_rub
from src.services.rate_service import (
    calculate_partner_rate,
    calculate_seconds_until_next_aligned_refresh,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ParsedSourceMessage:
    source_name: str
    message_id: int
    message_date: datetime | None
    text: str
    parsed_value: NobitexAssets | Decimal


@dataclass(frozen=True)
class SourceDebugMessage:
    source_name: str
    message_id: int
    message_date: datetime | None
    text_preview: str
    parsed_value: NobitexAssets | Decimal | None


class TelegramSourcesService:
    def __init__(
        self,
        *,
        client: TelegramClient,
        settings: Settings,
        bot: Bot | None = None,
    ) -> None:
        self.client = client
        self.settings = settings
        self.bot = bot
        self._refresh_lock = asyncio.Lock()
        self._scheduler_task: asyncio.Task[None] | None = None
        self._stopped = asyncio.Event()
        self._last_snapshot: RateSnapshot | None = None

    async def start(self) -> None:
        if not self.settings.nobitex_source or not self.settings.rapira_source:
            logger.warning("NOBITEX_SOURCE or RAPIRA_SOURCE is not set; Telegram source reader is disabled.")
            return

        await self.client.start()
        logger.info("Telethon source client started with session %s.", self.settings.telethon_session_name)

        await self._restore_latest_snapshot()
        await self.force_refresh_rate(reason="startup")

        if self.settings.rate_refresh_mode == "aligned_5min":
            self._scheduler_task = asyncio.create_task(self._run_aligned_refresh_loop())

    async def stop(self) -> None:
        self._stopped.set()
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

        if self.client.is_connected():
            await self.client.disconnect()

    async def run_until_disconnected(self) -> None:
        await self.client.run_until_disconnected()

    async def force_refresh_rate(self, reason: str) -> RateSnapshot | None:
        async with self._refresh_lock:
            logger.info("Rate refresh started: reason=%s.", reason)
            nobitex_message = await self._find_latest_valid_message(
                source_name="Nobitex",
                source=self.settings.nobitex_source,
                parser=parse_nobitex_assets,
            )
            rapira_message = await self._find_latest_valid_message(
                source_name="Rapira",
                source=self.settings.rapira_source,
                parser=parse_rapira_usdt_rub,
            )

            if nobitex_message is None or rapira_message is None:
                logger.warning(
                    "Rate refresh skipped: nobitex_found=%s rapira_found=%s.",
                    nobitex_message is not None,
                    rapira_message is not None,
                )
                return self._last_snapshot

            result = calculate_partner_rate(
                nobitex_usdt_toman=nobitex_message.parsed_value.usdt_toman,
                rapira_usdt_rub_base=Decimal(rapira_message.parsed_value),
                margin_percent=self.settings.rate_margin_percent,
            )

            async with async_session_maker() as session:
                snapshot = await RateRepository(session).save_snapshot(
                    nobitex_usdt_toman=Decimal(result.nobitex_usdt_toman),
                    rapira_usdt_rub_base=result.rapira_usdt_rub_base,
                    rapira_usdt_rub_with_margin=result.rapira_usdt_rub_with_margin,
                    margin_percent=result.margin_percent,
                    rub_toman_raw=result.rub_toman_raw,
                    rub_toman_display=result.rub_toman_display,
                    nobitex_message_id=nobitex_message.message_id,
                    nobitex_message_date=nobitex_message.message_date,
                    rapira_message_id=rapira_message.message_id,
                    rapira_message_date=rapira_message.message_date,
                    refresh_reason=reason,
                    bitcoin_usd=nobitex_message.parsed_value.bitcoin_usd,
                    gold_ounce_usd=nobitex_message.parsed_value.gold_ounce_usd,
                    oil_usd=nobitex_message.parsed_value.oil_usd,
                )
                await session.commit()
                await session.refresh(snapshot)

            self._last_snapshot = snapshot
            logger.info(
                "Rate refresh saved: reason=%s nobitex_message_id=%s nobitex_value=%s "
                "rapira_message_id=%s rapira_value=%s display=%s.",
                reason,
                nobitex_message.message_id,
                nobitex_message.parsed_value.usdt_toman,
                rapira_message.message_id,
                rapira_message.parsed_value,
                result.rub_toman_display,
            )
            return snapshot

    async def describe_recent_sources(self, limit: int = 3) -> str:
        parts = []
        for source_name, source, parser in (
            ("Nobitex", self.settings.nobitex_source, parse_nobitex_assets),
            ("Rapira", self.settings.rapira_source, parse_rapira_usdt_rub),
        ):
            debug_messages = await self._inspect_recent_messages(
                source_name=source_name,
                source=source,
                parser=parser,
                limit=limit,
            )
            parts.append(f"{source_name}:")
            if not debug_messages:
                parts.append("  сообщений нет или источник недоступен")
                continue
            for item in debug_messages:
                date = _format_optional_datetime(item.message_date)
                parts.append(
                    f"  id={item.message_id}, date={date}, parsed={item.parsed_value}\n"
                    f"  text={item.text_preview}"
                )

        return "\n".join(parts)

    async def _run_aligned_refresh_loop(self) -> None:
        while not self._stopped.is_set():
            sleep_seconds = calculate_seconds_until_next_aligned_refresh(
                datetime.now().astimezone(),
                self.settings.rate_refresh_every_minutes,
                self.settings.rate_refresh_delay_seconds,
            )
            logger.info("Next aligned rate refresh scheduled in %.3f seconds.", sleep_seconds)
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=sleep_seconds)
                return
            except asyncio.TimeoutError:
                await self.force_refresh_rate(reason="scheduled_aligned_5min")

    async def _restore_latest_snapshot(self) -> None:
        async with async_session_maker() as session:
            self._last_snapshot = await RateRepository(session).get_latest_snapshot()

        if self._last_snapshot is not None:
            logger.info("Restored latest RateSnapshot id=%s from database.", self._last_snapshot.id)

    async def _find_latest_valid_message(
        self,
        *,
        source_name: str,
        source: str | None,
        parser: Callable[[str], NobitexAssets | Decimal | None],
    ) -> ParsedSourceMessage | None:
        if source is None:
            await self._handle_parse_error(source_name, "", "Source is not configured.")
            return None

        messages = await self.client.get_messages(source, limit=self.settings.fetch_last_messages_limit)
        for message in messages:
            text = _message_text(message)
            parsed_value = parser(text)
            logger.info(
                "%s source message inspected: message_id=%s parsed=%s.",
                source_name,
                message.id,
                parsed_value,
            )
            if parsed_value is not None:
                return ParsedSourceMessage(
                    source_name=source_name,
                    message_id=message.id,
                    message_date=message.date,
                    text=text,
                    parsed_value=parsed_value,
                )

        await self._handle_parse_error(
            source_name,
            "\n\n".join(_message_text(message)[:500] for message in messages),
            f"No valid rate found in last {self.settings.fetch_last_messages_limit} messages.",
        )
        return None

    async def _inspect_recent_messages(
        self,
        *,
        source_name: str,
        source: str | None,
        parser: Callable[[str], NobitexAssets | Decimal | None],
        limit: int,
    ) -> list[SourceDebugMessage]:
        if source is None:
            return []

        messages = await self.client.get_messages(source, limit=limit)
        result = []
        for message in messages:
            text = _message_text(message)
            result.append(
                SourceDebugMessage(
                    source_name=source_name,
                    message_id=message.id,
                    message_date=message.date,
                    text_preview=text.replace("\n", " ")[:180],
                    parsed_value=parser(text),
                )
            )
        return result

    async def _handle_parse_error(self, source_name: str, message_text: str, error: str) -> None:
        logger.warning("%s parse error: %s", source_name, error)
        if not self.settings.auto_notify_admins_on_parse_error:
            return

        await notify_parse_error(self.bot, source_name, message_text, error)


def _message_text(message: Message) -> str:
    return message.raw_text or message.message or ""


def _format_optional_datetime(value: datetime | None) -> str:
    if value is None:
        return "-"
    return value.astimezone().strftime("%d.%m.%Y %H:%M:%S")
