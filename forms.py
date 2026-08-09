from datetime import date
from decimal import Decimal

from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    DecimalField,
    EmailField,
    FieldList,
    Form,
    FormField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
    widgets,
)
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    InputRequired,
    Length,
    NumberRange,
    Optional,
    Regexp,
    ValidationError,
)


class RegistrationForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
            Length(
                max=255,
                message="Email must be 255 characters or fewer."
            ),
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired(),
            Length(min=8)
        ]
    )

    confirmation = PasswordField(
        "Confirm Password",
        validators=[
            DataRequired(),
            EqualTo("password")
        ]
    )

    submit = SubmitField("Create Account")

class LoginForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email(),
            Length(
                max=255,
                message="Email must be 255 characters or fewer."
            ),
        ]
    )

    password = PasswordField(
        "Password",
        validators=[
            DataRequired()
        ]
    )

    remember = BooleanField("Remember me")

    submit = SubmitField("Log In")

class OnboardingProfileForm(FlaskForm):
    display_name = StringField(
        "What should we call you?",
        validators=[
            DataRequired(),
            Length(min=2, max=100)
        ]
    )

    currency = SelectField(
        "Your currency",
        choices=[
            ("TND", "Tunisian Dinar (TND)"),
            ("USD", "US Dollar (USD)"),
            ("EUR", "Euro (EUR)"),
            ("CAD", "Canadian Dollar (CAD)")
        ],
        default="TND",
        validators=[DataRequired()]
    )

    submit = SubmitField("Continue")

class OnboardingGoalsForm(FlaskForm):
    goals = SelectMultipleField(
        "What do you want help with?",
        choices=[
            ("save_more", "Save more"),
            ("stop_overspending", "Stop overspending"),
            ("understand_spending", "Understand where my money goes"),
            ("better_habits", "Build better money habits"),
            ("track_money", "Just track my money"),
            ("save_for_something", "Save for something specific"),
        ],
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False),
        validators=[
    Length(
        min=1,
        message="Choose at least one goal."
        )]
    )

    submit = SubmitField("Continue")
class IncomeSourceForm(Form):
    name = StringField(
        "Income source",
        validators=[DataRequired(), Length(max=100)]
    )

    amount = DecimalField(
        "Amount",
        places=3,
        validators=[
            InputRequired(),
            NumberRange(
                min=Decimal("0.001"),
                max=Decimal("999999999.999"),
                message="Enter a valid amount."
            )
        ]
    )

    frequency = SelectField(
        "How often?",
        choices=[
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("one_time", "One time"),
            ("manual", "Irregular / manual"),
        ],
        validators=[DataRequired()]
    )

    next_payment_date = DateField(
        "Next payment date",
        validators=[Optional()]
    )

    def validate_next_payment_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError(
                "Next payment date cannot be in the past."
            )


class OnboardingIncomeForm(FlaskForm):
    sources = FieldList(
        FormField(IncomeSourceForm),
        min_entries=1
    )

    submit = SubmitField("Continue")

class OnboardingBalanceForm(FlaskForm):
    starting_balance = DecimalField(
    "Starting balance",
    places=3,
    validators=[
        InputRequired(),
        NumberRange(
            min=Decimal("0.000"),
            max=Decimal("999999999.999"),
            message="Balance must be between 0 and 999,999,999.999."
            )
        ]
    )
    submit = SubmitField("Continue")
class OnboardingCategoryForm(Form):
    name = StringField(
        "Category name",
        validators=[DataRequired(), Length(max=100)]
    )

    category_type = SelectField(
        "Type",
        choices=[
            ("expense", "Expense"),
            ("income", "Income")
        ],
        validators=[DataRequired()]
    )

    icon = StringField(
        "Icon",
        validators=[Optional(), Length(max=50)]
    )


class OnboardingCategoriesForm(FlaskForm):
    categories = FieldList(
        FormField(OnboardingCategoryForm),
        min_entries=1
    )

    submit = SubmitField("Finish setup")


# AI assistance: OpenAI Codex helped draft the category-management form and
# safe color validation; reviewed and adapted by the project author.
class CategoryForm(FlaskForm):
    name = StringField(
        "Category name",
        validators=[
            DataRequired(message="Enter a category name."),
            Length(max=100),
        ]
    )

    category_type = SelectField(
        "Category type",
        choices=[
            ("expense", "Expense"),
            ("income", "Income"),
        ],
        validators=[DataRequired()]
    )

    icon = StringField(
        "Icon",
        validators=[Optional(), Length(max=50)]
    )

    color = StringField(
        "Color",
        validators=[
            Optional(),
            Length(max=20),
            Regexp(
                r"\A#[0-9A-Fa-f]{6}\Z",
                message="Use a six-digit hex color such as #b6532e."
            ),
        ]
    )

    submit = SubmitField("Save category")


class DeleteCategoryForm(FlaskForm):
    submit = SubmitField("Delete category")


# AI assistance: OpenAI Codex helped draft the budget and period forms;
# reviewed and adapted by the project author.
class BudgetForm(FlaskForm):
    category_id = SelectField(
        "Expense category",
        coerce=int,
        validators=[
            InputRequired(message="Choose an expense category."),
            NumberRange(min=1, message="Choose an expense category.")
        ]
    )

    amount = DecimalField(
        "Budget amount",
        places=3,
        validators=[
            InputRequired(),
            NumberRange(
                min=Decimal("0.001"),
                max=Decimal("999999999.999"),
                message="Enter an amount between 0.001 and 999,999,999.999."
            )
        ]
    )

    submit = SubmitField("Save budget")


class BudgetPeriodForm(FlaskForm):
    budget_period = SelectField(
        "Budget period",
        choices=[
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField("Update period")


class DeleteBudgetForm(FlaskForm):
    submit = SubmitField("Delete budget")


# AI assistance: OpenAI Codex helped draft the monetary savings-goal and
# progress-adjustment forms; reviewed and adapted by the project author.
class SavingsGoalForm(FlaskForm):
    name = StringField(
        "Goal name",
        validators=[
            DataRequired(message="Enter a savings goal name."),
            Length(max=100),
        ]
    )

    target_amount = DecimalField(
        "Target amount",
        places=3,
        validators=[
            InputRequired(),
            NumberRange(
                min=Decimal("0.001"),
                max=Decimal("999999999.999"),
                message="Enter an amount between 0.001 and 999,999,999.999."
            )
        ]
    )

    target_date = DateField(
        "Target date",
        validators=[Optional()]
    )

    submit = SubmitField("Save goal")


class SavingsAmountForm(FlaskForm):
    action = SelectField(
        "Action",
        choices=[
            ("add", "Add to savings"),
            ("withdraw", "Withdraw from savings"),
        ],
        validators=[DataRequired()]
    )

    amount = DecimalField(
        "Amount",
        places=3,
        validators=[
            InputRequired(),
            NumberRange(
                min=Decimal("0.001"),
                max=Decimal("999999999.999"),
                message="Enter an amount between 0.001 and 999,999,999.999."
            )
        ]
    )

    submit = SubmitField("Update savings")


class DeleteSavingsGoalForm(FlaskForm):
    submit = SubmitField("Delete savings goal")


class LogoutForm(FlaskForm):
    submit = SubmitField("Log out")


# AI assistance: OpenAI Codex helped draft the transaction forms and date
# validation; reviewed and adapted by the project author.
class TransactionForm(FlaskForm):
    transaction_type = SelectField(
        "Transaction type",
        choices=[
            ("expense", "Expense"),
            ("income", "Income"),
        ],
        default="expense",
        validators=[DataRequired()]
    )

    category_id = SelectField(
        "Category",
        coerce=int,
        validators=[
            InputRequired(message="Choose a category."),
            NumberRange(min=1, message="Choose a category.")
        ]
    )

    amount = DecimalField(
        "Amount",
        places=3,
        validators=[
            InputRequired(),
            NumberRange(
                min=Decimal("0.001"),
                max=Decimal("999999999.999"),
                message="Enter an amount between 0.001 and 999,999,999.999."
            )
        ]
    )

    description = TextAreaField(
        "Description",
        validators=[Optional(), Length(max=255)]
    )

    transaction_date = DateField(
        "Transaction date",
        default=date.today,
        validators=[InputRequired()]
    )

    submit = SubmitField("Save transaction")

    def validate_transaction_date(self, field):
        if field.data and field.data > date.today():
            raise ValidationError(
                "Transaction date cannot be in the future."
            )


class DeleteTransactionForm(FlaskForm):
    submit = SubmitField("Delete transaction")


# AI assistance: OpenAI Codex helped draft this GET-only history filter form
# and date-range validation; reviewed and adapted by the project author.
class HistoryFilterForm(Form):
    transaction_type = SelectField(
        "Type",
        choices=[
            ("all", "All transactions"),
            ("income", "Income"),
            ("expense", "Expenses"),
        ],
        default="all",
        validators=[DataRequired()]
    )

    category_id = SelectField(
        "Category",
        coerce=int,
        default=0
    )

    start_date = DateField(
        "From",
        validators=[Optional()]
    )

    end_date = DateField(
        "To",
        validators=[Optional()]
    )

    sort = SelectField(
        "Sort by",
        choices=[
            ("newest", "Newest first"),
            ("oldest", "Oldest first"),
            ("amount_high", "Highest amount"),
            ("amount_low", "Lowest amount"),
        ],
        default="newest",
        validators=[DataRequired()]
    )

    submit = SubmitField("Apply filters")

    def validate_end_date(self, field):
        if (
            self.start_date.data
            and field.data
            and self.start_date.data > field.data
        ):
            raise ValidationError(
                "The start date must be on or before the end date."
            )


# AI assistance: OpenAI Codex helped draft these separate settings and
# income-source management forms; reviewed and adapted by the project author.
class ProfileSettingsForm(FlaskForm):
    display_name = StringField(
        "Display name",
        validators=[Optional(), Length(max=100)]
    )

    submit = SubmitField("Save profile")


class MoneySettingsForm(FlaskForm):
    currency = SelectField(
        "Currency",
        choices=[
            ("TND", "Tunisian Dinar (TND)"),
            ("USD", "US Dollar (USD)"),
            ("EUR", "Euro (EUR)"),
            ("CAD", "Canadian Dollar (CAD)"),
        ],
        validators=[DataRequired()]
    )

    starting_balance = DecimalField(
        "Starting balance",
        places=3,
        validators=[
            InputRequired(),
            NumberRange(
                min=Decimal("0.000"),
                max=Decimal("999999999.999"),
                message="Enter a balance between 0 and 999,999,999.999."
            )
        ]
    )

    budget_period = SelectField(
        "Budget period",
        choices=[
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField("Save money settings")


class PreferenceSettingsForm(FlaskForm):
    appearance = SelectField(
        "Appearance",
        choices=[
            ("system", "Use device setting"),
            ("light", "Light"),
            ("dark", "Dark"),
        ],
        validators=[DataRequired()]
    )

    language = SelectField(
        "Language",
        choices=[
            ("en", "English"),
            ("fr", "Français"),
            ("ar", "العربية"),
        ],
        validators=[DataRequired()]
    )

    submit = SubmitField("Save preferences")


class LanguagePreferenceForm(FlaskForm):
    language = SelectField(
        "Language",
        choices=[
            ("en", "English"),
            ("fr", "Français"),
            ("ar", "العربية"),
        ],
        validators=[DataRequired()]
    )


class GoalsSettingsForm(FlaskForm):
    goals = SelectMultipleField(
        "What do you want to improve?",
        choices=[
            ("save_more", "Save more"),
            ("stop_overspending", "Stop overspending"),
            ("understand_spending", "Understand where my money goes"),
            ("better_habits", "Build better money habits"),
            ("track_money", "Just track my money"),
            ("save_for_something", "Save for something specific"),
        ],
        option_widget=widgets.CheckboxInput(),
        widget=widgets.ListWidget(prefix_label=False),
        validators=[
            Length(min=1, message="Choose at least one goal.")
        ]
    )

    submit = SubmitField("Save money goals")


class IncomeSourceSettingsForm(FlaskForm):
    name = StringField(
        "Income source",
        validators=[
            DataRequired(message="Enter an income source name."),
            Length(max=100),
        ]
    )

    amount = DecimalField(
        "Amount",
        places=3,
        validators=[
            InputRequired(),
            NumberRange(
                min=Decimal("0.001"),
                max=Decimal("999999999.999"),
                message="Enter an amount between 0.001 and 999,999,999.999."
            )
        ]
    )

    frequency = SelectField(
        "How often?",
        choices=[
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("one_time", "One time"),
            ("manual", "Irregular / manual"),
        ],
        validators=[DataRequired()]
    )

    next_payment_date = DateField(
        "Next payment date",
        validators=[Optional()]
    )

    submit = SubmitField("Save income source")

    def validate_next_payment_date(self, field):
        if field.data and field.data < date.today():
            raise ValidationError(
                "Next payment date cannot be in the past."
            )


class DeleteIncomeSourceForm(FlaskForm):
    submit = SubmitField("Delete income source")
