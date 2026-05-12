from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, CheckConstraint, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class CreatedAtMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class TimestampMixin(CreatedAtMixin):
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String(255))
    first_name: Mapped[str | None] = mapped_column(String(255))
    last_name: Mapped[str | None] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    access_requests: Mapped[list["AccessRequest"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        foreign_keys="AccessRequest.user_id",
    )
    processed_access_requests: Mapped[list["AccessRequest"]] = relationship(
        back_populates="processed_by_admin",
        foreign_keys="AccessRequest.processed_by_admin_id",
    )


class AccessRequest(Base, CreatedAtMixin):
    __tablename__ = "access_requests"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'approved', 'rejected')",
            name="ck_access_requests_status",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    processed_by_admin_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    user: Mapped[User] = relationship(
        back_populates="access_requests",
        foreign_keys=[user_id],
    )
    processed_by_admin: Mapped[User | None] = relationship(
        back_populates="processed_access_requests",
        foreign_keys=[processed_by_admin_id],
    )


class RateSnapshot(Base, CreatedAtMixin):
    __tablename__ = "rate_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nobitex_usdt_toman: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    rapira_usdt_rub_base: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    rapira_usdt_rub_with_margin: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    margin_percent: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False)
    rub_toman_raw: Mapped[Decimal] = mapped_column(Numeric(18, 6), nullable=False)
    rub_toman_display: Mapped[int] = mapped_column(Integer, nullable=False)
    nobitex_message_id: Mapped[int | None] = mapped_column(BigInteger)
    nobitex_message_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    rapira_message_id: Mapped[int | None] = mapped_column(BigInteger)
    rapira_message_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refresh_reason: Mapped[str] = mapped_column(String(64), default="startup", nullable=False)
    bitcoin_usd: Mapped[int | None] = mapped_column(Integer)
    gold_ounce_usd: Mapped[int | None] = mapped_column(Integer)
    oil_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 6))


class Setting(Base):
    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(255), primary_key=True)
    value: Mapped[str] = mapped_column(String, nullable=False)
