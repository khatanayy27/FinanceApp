from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, DateField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange


class AddGoalForm(FlaskForm):
    goal_name = StringField(
        'Goal Name',
        validators=[DataRequired(), Length(max=150)],
        render_kw={"placeholder": "e.g. Emergency Fund"}
    )
    target_amount = DecimalField(
        'Target Amount',
        validators=[DataRequired(), NumberRange(min=1)],
        places=2,
        render_kw={"placeholder": "e.g. 5000.00"}
    )
    current_amount = DecimalField(
        'Amount Saved So Far',
        validators=[DataRequired(), NumberRange(min=0)],
        places=2,
        default=0.00,
        render_kw={"placeholder": "0.00"}
    )
    deadline = DateField(
        'Target Date',
        validators=[DataRequired()]
    )
    submit = SubmitField('Add Goal')


class UpdateGoalForm(FlaskForm):
    current_amount = DecimalField(
        'Update Saved Amount',
        validators=[DataRequired(), NumberRange(min=0)],
        places=2,
        render_kw={"placeholder": "0.00"}
    )
    submit = SubmitField('Update Progress')