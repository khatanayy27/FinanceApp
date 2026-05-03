from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional

class AddAccountForm(FlaskForm):
    account_name = StringField(
        'Account Name',
        validators=[DataRequired(), Length(max=100)],
        render_kw={'placeholder': 'e.g. Chase Checking'}
    )
    account_type_id = SelectField(
        'Account Type',
        coerce=int,
        validators=[DataRequired()]
    )
    current_balance = DecimalField(
        'Current Balance',
        validators=[DataRequired(), NumberRange(min=0)],
        places=2,
        default=0.00,
        render_kw={'placeholder': '0.00'}
    )
    credit_last4 = StringField(
        'Last 4 Digits (credit cards only)',
        validators=[Optional(), Length(min=4, max=4)],
        render_kw={'placeholder': '1234'}
    )
    submit = SubmitField('Add Account')