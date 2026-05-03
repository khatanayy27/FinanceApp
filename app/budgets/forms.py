from flask_wtf import FlaskForm
from wtforms import SelectField, DecimalField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange


class AddBudgetForm(FlaskForm):
    category_id = SelectField(
        'Category',
        coerce=int,
        validators=[DataRequired()]
    )
    monthly_limit = DecimalField(
        'Monthly Limit',
        validators=[DataRequired(), NumberRange(min=1)],
        places=2,
        render_kw={"placeholder": "e.g. 500.00"}
    )
    start_date = DateField(
        'Start Date',
        validators=[DataRequired()]
    )
    end_date = DateField(
        'End Date',
        validators=[DataRequired()]
    )
    submit = SubmitField('Add Budget')