from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import date
from app import db
from app.goals import goals
from app.goals.forms import AddGoalForm, UpdateGoalForm
from app.models import Goal


@goals.route('/', methods=['GET', 'POST'])
@login_required
def index():
    add_form = AddGoalForm()

    if add_form.validate_on_submit() and 'goal_name' in request.form:
        new_goal = Goal(
            user_id=current_user.user_id,
            goal_name=add_form.goal_name.data,
            target_amount=add_form.target_amount.data,
            current_amount=add_form.current_amount.data,
            deadline=add_form.deadline.data
        )
        db.session.add(new_goal)
        db.session.commit()
        flash(f'Goal "{add_form.goal_name.data}" created!', 'success')
        return redirect(url_for('goals.index'))

    user_goals = Goal.query.filter_by(
        user_id=current_user.user_id
    ).order_by(Goal.deadline).all()

    # Enrich each goal with progress data
    goal_list = []
    for g in user_goals:
        target  = float(g.target_amount)
        current = float(g.current_amount)
        pct     = min(round((current / target * 100), 1) if target > 0 else 0, 100)
        remaining = max(target - current, 0)
        days_left = (g.deadline - date.today()).days if g.deadline else None
        status = (
            'success' if pct >= 100 else
            'info'    if pct >= 60  else
            'warning' if pct >= 30  else
            'danger'
        )
        is_completed = pct >= 100
        is_overdue   = days_left is not None and days_left < 0 and not is_completed
        goal_list.append({
            'goal':        g,
            'target':      target,
            'current':     current,
            'remaining':   remaining,
            'pct':         pct,
            'days_left':   days_left,
            'status':      status,
            'is_completed': is_completed,
            'is_overdue':   is_overdue,
        })

    # Chart.js data — goal progress bars
    chart_labels  = [g['goal'].goal_name  for g in goal_list]
    chart_current = [g['current']         for g in goal_list]
    chart_targets = [g['target']          for g in goal_list]
    chart_pcts    = [g['pct']             for g in goal_list]

    # Summary stats
    total_goals     = len(goal_list)
    completed_goals = sum(1 for g in goal_list if g['is_completed'])
    total_saved     = sum(g['current'] for g in goal_list)
    total_target    = sum(g['target']  for g in goal_list)

    return render_template(
        'goals/index.html',
        add_form=add_form,
        goal_list=goal_list,
        chart_labels=chart_labels,
        chart_current=chart_current,
        chart_targets=chart_targets,
        chart_pcts=chart_pcts,
        total_goals=total_goals,
        completed_goals=completed_goals,
        total_saved=total_saved,
        total_target=total_target,
    )


@goals.route('/update/<int:goal_id>', methods=['POST'])
@login_required
def update_goal(goal_id):
    goal = Goal.query.filter_by(
        goal_id=goal_id,
        user_id=current_user.user_id
    ).first_or_404()

    new_amount = request.form.get('current_amount', type=float)
    if new_amount is not None and new_amount >= 0:
        goal.current_amount = new_amount
        db.session.commit()
        flash(f'Progress updated for "{goal.goal_name}".', 'success')
    else:
        flash('Invalid amount entered.', 'danger')

    return redirect(url_for('goals.index'))