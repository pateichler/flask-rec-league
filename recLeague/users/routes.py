from flask import (
    render_template, url_for, flash, redirect, request, Blueprint, abort
)
from flask.typing import ResponseReturnValue
from flask_login import login_user, current_user, logout_user
from sqlalchemy import func

from recLeague import db, bcrypt
from recLeague.models import User, Settings
from recLeague.users.forms import (
    RegistrationForm, LoginForm, RequestResetForm, ResetPasswordForm
)
from recLeague.users.utils import send_reset_email
from recLeague.config import STAT_HIGHLIGHT, STAT_CATEGORY_KEYS, STAT_CATEGORY_NAMES

users = Blueprint('users', __name__)


@users.route("/register", methods=['GET', 'POST'])
def register() -> ResponseReturnValue:
    """Route for registering a new user.
    """

    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        s = Settings.query.first()
        if s is None:
            raise Exception("Settings object not found!")

        valid_league_pass = bcrypt.check_password_hash(
            s.password, form.league_password.data
        )

        # Check if user has correct league password to join
        if s and valid_league_pass:
            hashed_password = bcrypt.generate_password_hash(
                form.password.data
            ).decode('utf-8')
            name = (form.first_name.data.capitalize() 
                    + " " + form.last_name.data.capitalize())
            user = User(
                name=name, email=form.email.data, password=hashed_password
            )
            db.session.add(user)
            db.session.commit()
            flash(
                'Your account has been created! You are now able to log in', 
                'success'
            )
            return redirect(url_for('users.login'))
        else:
            flash('Incorrect League password', 'danger')
            
    return render_template('register.html', title='Register', form=form)


@users.route("/login", methods=['GET', 'POST'])
def login() -> ResponseReturnValue:
    """Route for login page.
    """

    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        # Get user associated with email and check password
        # TODO: The func.lower may not be needed if we store emails as 
        # lowercase to begin with.
        user = User.query.filter(
            func.lower(User.email) == func.lower(form.email.data)
        ).first()
        assert user is not None

        valid_user_pass = bcrypt.check_password_hash(
            user.password, form.password.data
        )

        if user and valid_user_pass:
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            
            if next_page:
                return redirect(next_page)

            return redirect(url_for('main.home'))
        else:
            flash(
                'Login Unsuccessful. Please check email and password', 
                'danger'
            )
    return render_template('login.html', title='Login', form=form)


@users.route("/logout")
def logout() -> ResponseReturnValue:
    """Route for logging out user.
    """

    logout_user()
    return redirect(url_for('users.login'))


@users.route("/user/<int:user_id>")
def account(user_id: int) -> ResponseReturnValue:
    """Route for displaying user page.
    """

    user = User.query.get_or_404(user_id)
    return render_template(
        'account.html', user=user, stat_names=STAT_CATEGORY_NAMES, 
        stat_var_names=STAT_CATEGORY_KEYS, highlight_stat=STAT_HIGHLIGHT
    )


@users.route("/user/<int:user_id>/delete", methods=['POST'])
def delete_user(user_id: int) -> ResponseReturnValue:
    """Route for deleting a user.
    
    Used only by admin.
    
    Args:
        user_id (int): ID of user
    """

    user = User.query.get_or_404(user_id)
    # Can only delete games if one of players edit before verified or 
    # if the user is admin
    if current_user.is_admin is False or len(user.games) > 0:
        abort(403)
    db.session.delete(user)
    db.session.commit()

    flash('User has been deleted!', 'success')
    return redirect(url_for('admin.users'))


@users.route("/reset_password", methods=['GET', 'POST'])
def reset_request() -> ResponseReturnValue:
    """Route for requesting a password reset.
    """

    # Ignore requests for users already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter(
            func.lower(User.email) == func.lower(form.email.data)
        ).first()
        assert user is not None

        send_reset_email(user)
        flash(
            'An email has been sent with instructions to reset your password.', 
            'info'
        )
        return redirect(url_for('users.login'))
    
    return render_template(
        'reset_request.html', title='Reset Password', form=form
    )


@users.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token) -> ResponseReturnValue:
    """Route for validating reset password token.
    
    Args:
        token (str): Reset token.
    """

    # Ignore requests for users already logged in
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    user = User.verify_reset_token(token)
    # Make sure token is valid
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('users.reset_request'))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        # Update user to new password
        hashed_password = bcrypt.generate_password_hash(
            form.password.data
        ).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(
            'Your password has been updated! You are now able to log in', 
            'success'
        )
        return redirect(url_for('users.login'))

    return render_template(
        'reset_token.html', title='Reset Password', form=form
    )
