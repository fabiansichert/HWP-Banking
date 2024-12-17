from banking import app, db
import pyotp
import qrcode
from flask import render_template, request, redirect, url_for, session
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from sqlalchemy import text

# NEU - Bruteforce Limit
limiter = Limiter(get_remote_address, app=app)

# NEU - WTF Forms nutzen
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message="Passwords must match")])

class TwoFactorForm(FlaskForm):
    otp_code = StringField('Enter 2FA Code', validators=[DataRequired()])
    submit = SubmitField('Verify')

@app.route("/")
def start():
    return redirect(url_for('login'))

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()

    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = form.password.data
        confirmpassword = form.confirm_password.data

        query_stmt = f"SELECT username FROM users WHERE username='{username}'"
        result = db.session.execute(text(query_stmt))
        usernames = result.fetchall()

        if usernames:
            return render_template('register.html', form=form, error="Username already exists!")

        if password != confirmpassword:
            return render_template('register.html', form=form, error="Passwords do not match!")

        totp = pyotp.random_base32()

        db.session.execute(text("INSERT INTO users (username, passwd, otp_secret, amount) VALUES (:username, :passwd, :otp_secret, '0.00')"),
                           {"username": username, "passwd": password, "otp_secret": totp})
        db.session.commit()

        otp_uri = pyotp.totp.TOTP(totp).provisioning_uri(username, issuer_name="MyApp")

        img = qrcode.make(otp_uri)
        img.save("banking/static/qrcode.png")

        return render_template('register.html', form=form, qr_code="/static/qrcode.png")

    return render_template("register.html", form=form)

@app.route("/login", methods=["GET", "POST"])
@limiter.limit("3 per minute")  # NEU! 3 Versuche pro Minute
def login():
    form = LoginForm()

    if request.method == 'POST' and form.validate():
        username = form.username.data
        password = form.password.data

        query_stmt = f"SELECT id, passwd, otp_secret FROM users WHERE username='{username}';"
        result = db.session.execute(text(query_stmt))
        user = result.fetchall()

        if not user or user[0][1] != password:
            return render_template("login.html", form=form, error="incorrect")

        session['user_id'] = user[0][0]
        session['username'] = username
        session['otp_secret'] = user[0][2]

        return redirect(url_for('two_factor'))

    return render_template('login.html', form=form)

#NEU - 2FA
@app.route("/two_factor", methods=["GET", "POST"])
def two_factor():
    if request.method == 'POST':
        otp_code = request.form.get('totp_code')
        totp = pyotp.TOTP(session['otp_secret'])

        if totp.verify(otp_code):
            session['authenticated'] = True
            return redirect(url_for('home'))
        else:
            return render_template('two_factor.html', error="Invalid 2FA code.")

    return render_template('two_factor.html')


@app.route("/home")
def home():
    if "authenticated" not in session:
        return redirect(url_for('login'))

    userid = session["user_id"]
    username = session['username']

    query_stmt = f"SELECT * FROM users WHERE id={userid}"
    result = db.session.execute(text(query_stmt))
    usersquery = result.fetchall()

    query_stmt = """
        SELECT t.id, t.from_user, t.to_user, t.amount, t.transaction_date, 
               u_from.username AS from_username, u_to.username AS to_username 
        FROM transactions t
        JOIN users u_from ON t.from_user = u_from.id
        JOIN users u_to ON t.to_user = u_to.id
        WHERE t.from_user = :userid OR t.to_user = :userid
    """
    result = db.session.execute(text(query_stmt), {'userid': userid})
    transactionquery = result.fetchall()
    transactions = []

    for transaction in transactionquery:
        if transaction.from_user == userid:
            amount = f"-{transaction.amount:.2f}€"
        else:
            amount = f"{transaction.amount:.2f}€"

        transactions.append({
            "id": transaction.id,
            "from": transaction.from_username,
            "to": transaction.to_username,
            "amount": amount,
            "date": transaction.transaction_date.strftime("%d.%m.%Y")
        })

    return render_template("home.html", username=username, person=usersquery, transactions=transactions)

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('otp_secret', None)
    session.pop('authenticated', None)
    return redirect(url_for('login'))

@app.route("/overview")
def overview():
    search_query = request.args.get('search', '')

    if search_query:
        query_stmt = "SELECT * FROM users WHERE username LIKE '%:search_query%'"
        result = db.session.execute(text(query_stmt))
    else:
        query_stmt = "SELECT * FROM users"
        result = db.session.execute(text(query_stmt))

    persons = result.fetchall()

    return render_template("overview.html", persons=persons)