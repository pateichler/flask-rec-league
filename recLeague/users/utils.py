from flask import url_for
from flask_mail import Message

from recLeague import mail
from recLeague.models import User


def send_reset_email(user: User) -> None:
    """Sends a reset password email to user.
    
    Uses the email stored in the User.

    Args:
        user (User): User to send password email.
    """

    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='recLeague@gmail.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('users.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes \
will be made.
'''
    mail.send(msg)
