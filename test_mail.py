

from flask_mail import Mail, Message
from flask import Flask

app = Flask(__name__)

app.config.update(
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME="avik82of53@gmail.com",        # your Gmail
    MAIL_PASSWORD="cxujzcndtpoegnll",     # your app password
    MAIL_DEFAULT_SENDER=("CineSense Support", "avik82of53@gmail.com")  # ✅ Added line
)

mail = Mail(app)

with app.app_context():
    try:
        msg = Message("Test from CineSense", recipients=["avik82of53@gmail.com"])
        msg.body = "✅ This is a test email from Flask-Mail."
        mail.send(msg)
        print("✅ Mail sent successfully!")
    except Exception as e:
        print("❌ Error:", e)

