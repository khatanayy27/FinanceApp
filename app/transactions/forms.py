from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DecimalField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class AddTransactionForm(FlaskForm):
    account_id = SelectField(
        'Account',
        coerce=int,
        validators=[DataRequired()]
    )
    category_id = SelectField(
        'Category',
        coerce=int,
        validators=[Optional()]
    )
    transaction_type = SelectField(
        'Type',
        choices=[('income', 'Income'), ('expense', 'Expense')],
        validators=[DataRequired()]
    )
    amount = DecimalField(
        'Amount',
        validators=[DataRequired(), NumberRange(min=0.01)],
        places=2,
        render_kw={"placeholder": "0.00"}
    )
    transaction_date = DateField(
        'Date',
        validators=[DataRequired()]
    )
    description = StringField(
        'Description',
        validators=[Optional(), Length(max=255)],
        render_kw={"placeholder": "e.g. Grocery run at Walmart"}
    )
    submit = SubmitField('Add Transaction')


class FilterForm(FlaskForm):
    account_id = SelectField('Account', coerce=int)
    category_id = SelectField('Category', coerce=int)
    transaction_type = SelectField(
        'Type',
        choices=[
            (0, 'All Types'),
            ('income', 'Income'),
            ('expense', 'Expense')
        ]
    )
    date_from = DateField('From', validators=[Optional()], format='%Y-%m-%d')
    date_to = DateField('To', validators=[Optional()], format='%Y-%m-%d')
    search = StringField('Search', validators=[Optional()])
    submit = SubmitField('Apply Filters')