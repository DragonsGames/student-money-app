from datetime import datetime

from sqlalchemy import String, func
from sqlalchemy.orm import Mapped, mapped_column
from flask_login import UserMixin
from extensions import db
from datetime import datetime
from decimal import Decimal

from flask_login import UserMixin
from sqlalchemy import Boolean, ForeignKey, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from datetime import date, datetime
from decimal import Decimal

from flask_login import UserMixin
from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

class User(UserMixin, db.Model):
    goals: Mapped[list["UserGoal"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan"
)
    categories: Mapped[list["Category"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan"
)
    income_sources: Mapped[list["IncomeSource"]] = relationship(
    back_populates="user",
    cascade="all, delete-orphan"
    )
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )

    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0")
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

    settings: Mapped["UserSettings"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )


class UserSettings(db.Model):
    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    display_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        default="TND",
        server_default="TND"
    )

    starting_balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=Decimal("0.000"),
        server_default="0.000"
    )

    budget_period: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="monthly",
        server_default="monthly"
    )

    user: Mapped["User"] = relationship(
        back_populates="settings"
    )
class IncomeSource(db.Model):
    __tablename__ = "income_sources"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False
    )

    frequency: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    next_payment_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    is_recurring: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("1")
    )

    user: Mapped["User"] = relationship(
        back_populates="income_sources"
    )

class Category(db.Model):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    category_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    icon: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    color: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    is_default: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("0")
    )

    user: Mapped["User"] = relationship(
        back_populates="categories"
    )
class UserGoal(db.Model):
    __tablename__ = "user_goals"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    goal_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False
    )

    user: Mapped["User"] = relationship(
        back_populates="goals"
    )