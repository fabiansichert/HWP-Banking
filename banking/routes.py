from banking import app, db
from flask import render_template, request, redirect, url_for, session
from sqlalchemy import text

@app.route("/")
def start():
    return redirect(url_for('login'))

@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('username',None)
    return redirect(url_for('login'))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == 'POST':
        username = request.form.get('Username')
        password = request.form.get('Password')

        if (username is None or isinstance(username, str) is False):
            print("something wrong with username")
            return render_template('login.html')
        if (password is None or isinstance(username, str) is False):
            print("something wrong with password")
            return render_template('login.html')

        query_stmt = f"select id from users where username='{username}' and passwd='{password}';"
        print(query_stmt)
        result = db.session.execute(text(query_stmt))
        user = result.fetchall()

        if not user:
            print("Try again ...")
            return render_template("login.html")
        
        print(user[0][0])
        session['user_id'] = user[0][0]
        session['username'] = username
        
        return redirect(url_for('home'))
    return render_template('login.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        print(request.form)
        username = request.form.get('Username')
        password = request.form.get('Password')
        confirmpassword = request.form.get('ConfirmPassword')

        print(username)
        print(password)
        print(confirmpassword)

        if (username is None or isinstance(username, str) is False):
            print("something wrong with username")
            return render_template('register.html')
        if (password is None or isinstance(username, str) is False):
            print("something wrong with password")
            return render_template('register.html')
        if (password != confirmpassword):
            print("something wrong with confirmpassword")
            return render_template('register.html')

        query_stmt = f"select username from users"
        result = db.session.execute(text(query_stmt))
        usernames = result.fetchall()

        if not usernames:
            print("Try again ...")
            return render_template("register.html")

        if username in usernames:
            print("Username already exists!")
            return render_template('register.html')
        
        query_stmt = f"""
        INSERT INTO users (username, passwd, amount) VALUES ('{username}', '{password}', '0.00');
        """
        db.session.execute(text(query_stmt))
        db.session.commit()

        query_stmt = f"select id from users where username='{username}'"
        result = db.session.execute(text(query_stmt))
        user = result.fetchall()

        session['user_id'] = user[0][0]
        session['username'] = username
        
        return redirect(url_for('home'))
    return render_template("register.html")

@app.route("/home")
def home():
    if "user_id" not in session:
        return render_template("login.html")
    
    userid = session["user_id"]
    username = session['username']

    query_stmt = f"select * from users where id={userid}"
    print(query_stmt)
    result = db.session.execute(text(query_stmt))
    usersquery = result.fetchall()

    query_stmt = f"""
        SELECT t.id, t.from_user, t.to_user, t.amount, t.transaction_date, 
               u_from.username AS from_username, u_to.username AS to_username 
        FROM transactions t
        JOIN users u_from ON t.from_user = u_from.id
        JOIN users u_to ON t.to_user = u_to.id
        WHERE t.from_user = {userid} OR t.to_user = {userid}
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

    return render_template("home.html",username=username, person=usersquery, transactions=transactions)

@app.route("/overview")
def overview():

    search_query = request.args.get('search', '')
    
    if search_query:
        query_stmt = f"SELECT * FROM users WHERE username LIKE '%{search_query}%'"
        result = db.session.execute(text(query_stmt))
    else:
        query_stmt = "SELECT * FROM users"
        result = db.session.execute(text(query_stmt))

    persons = result.fetchall()

    return render_template("overview.html", persons=persons)
