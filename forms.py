from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from datetime import date
from wtforms import SelectField, StringField
from wtforms import SelectMultipleField, SubmitField, widgets
from wtforms import DateField, DecimalField
from wtforms.validators import NumberRange, Optional
from wtforms import (
    DateField,
    DecimalField,
    FieldList,
    Form,
    FormField,
    SelectField,
    StringField,
    SubmitField
)
from wtforms.validators import InputRequired
from wtforms.validators import (
    DataRequired,
    EqualTo,
    Length,
    NumberRange,
    Optional,
    ValidationError,
)
class RegistrationForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email()
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

from wtforms import BooleanField

class LoginForm(FlaskForm):
    email = EmailField(
        "Email",
        validators=[
            DataRequired(),
            Email()
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
            DataRequired(),
            NumberRange(
                min=0.001,
                max=999999999.999,
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
            min=0,
            max=999999999.999,
            message="Balance must be between 0 and 999,999,999.999."
            )
        ]
    )
    submit = SubmitField("Continue")
class CategoryForm(Form):
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
        FormField(CategoryForm),
        min_entries=1
    )

    submit = SubmitField("Finish setup")
class LogoutForm(FlaskForm):
    submit = SubmitField("Log out")
