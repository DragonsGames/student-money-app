from datetime import date, datetime
from decimal import Decimal

from flask_login import UserMixin
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    ForeignKey,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from extensions import db


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
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    budgets: Mapped[list["Budget"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    savings_goals: Mapped[list["SavingsGoal"]] = relationship(
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

    appearance: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="system",
        server_default="system"
    )

    language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        default="en",
        server_default="en"
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

    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="category"
    )

    budget: Mapped["Budget"] = relationship(
        back_populates="category",
        uselist=False
    )


# AI assistance: OpenAI Codex assisted with drafting the Transaction model
# structure; reviewed and adapted by the project author.
class Transaction(db.Model):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('income', 'expense')",
            name="ck_transactions_type"
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_transactions_amount_positive"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False
    )

    transaction_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False
    )

    description: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

    user: Mapped["User"] = relationship(
        back_populates="transactions"
    )

    category: Mapped["Category"] = relationship(
        back_populates="transactions"
    )


# AI assistance: OpenAI Codex assisted with drafting the Budget model and its
# integrity constraints; reviewed and adapted by the project author.
class Budget(db.Model):
    __tablename__ = "budgets"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "category_id",
            name="uq_budgets_user_category"
        ),
        CheckConstraint(
            "amount > 0",
            name="ck_budgets_amount_positive"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id"),
        nullable=False
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

    user: Mapped["User"] = relationship(
        back_populates="budgets"
    )

    category: Mapped["Category"] = relationship(
        back_populates="budget"
    )


# AI assistance: OpenAI Codex assisted with drafting the monetary SavingsGoal
# model and constraints; reviewed and adapted by the project author.
class SavingsGoal(db.Model):
    __tablename__ = "savings_goals"
    __table_args__ = (
        CheckConstraint(
            "target_amount > 0",
            name="ck_savings_goals_target_positive"
        ),
        CheckConstraint(
            "saved_amount >= 0",
            name="ck_savings_goals_saved_nonnegative"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    target_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False
    )

    saved_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 3),
        nullable=False,
        default=Decimal("0.000"),
        server_default="0.000"
    )

    target_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )

    user: Mapped["User"] = relationship(
        back_populates="savings_goals"
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
