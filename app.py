import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure SQLite database
connection = sqlite3.connect("who.db", check_same_thread=False)
db = connection.cursor()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home")
@login_required
def home():
    return render_template("home.html")

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Displays profile"""
    if request.method == "GET":
        db.execute("SELECT name, email FROM users WHERE rowid = ?", [session["user_id"]])
        user = db.fetchall()[0]
        return render_template("profile.html", user=user)
    if request.method == "POST":
        # Checks that user inputted old and new passwords
        if not request.form.get("old_password"):
            flash("Must input old password")
            return redirect("/profile")
        if not request.form.get("new_password"):
            flash("Must input new password")
            return redirect("/profile")

        old = request.form.get("old_password")
        db.execute("SELECT password FROM users WHERE rowid = ?", [session["user_id"]])
        current = db.fetchall()[0][0]

        # Checks that old password matches password in database
        if not check_password_hash(current, old):
            flash("Old password does not match")
            return redirect("/profile")

        new = request.form.get("new_password")
        new_hash = generate_password_hash(new)

        # Updates to new password
        db.execute("UPDATE users SET password = ? WHERE rowid = ?", (new_hash, session["user_id"]))
        flash("Successfully changed password!")

        return redirect("/profile")

@app.route("/vaccines", methods=["GET", "POST"])
@login_required
def vaccines():
    """Displays vaccine tracker"""
    if request.method == "GET":
        return render_template("vaccines.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Registers user"""
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        # Ensure name was submitted
        if not request.form.get("name"):
            flash("Must enter name")
            return redirect("/register")

        # Ensure email was submitted
        elif not request.form.get("email"):
            flash("Must enter email")
            return redirect("/register")
        db.execute("SELECT * FROM users WHERE email = ?", [request.form.get("email")])
        duplicate = db.fetchall()
        if len(duplicate) > 0:
            flash("Email already taken")
            return redirect("/register")

        # Ensure password was submitted
        if not request.form.get("password"):
            flash("Must enter password")
            return redirect("/register")

        elif not request.form.get("confirmation"):
            flash("Must confirm password")
            return redirect("/register")

        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        if password != confirmation:
            flash("Passwords must match")
            return redirect("/register")

        db.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (request.form.get("name"), request.form.get("email"), generate_password_hash(password)))
        connection.commit()

        db.execute("SELECT rowid FROM users WHERE email = ?", [request.form.get("email")])
        session["user_id"] = db.fetchall()[0][0]

        flash("Registered!")

        return redirect("/home")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Logs user in"""

    # Forgets any user_id
    session.clear()

    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        # Ensure email was submitted
        if not request.form.get("email"):
            flash("Must enter email")
            return redirect("/login")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Must enter password")
            return redirect("/login")

        # Query database for user
        db.execute("SELECT * FROM users WHERE email = ?", [request.form.get("email")])
        rows = db.fetchall()

        # Ensures user exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0][2], request.form.get("password")):
            flash("Invalid username or password")
            return redirect("/login")

        # Remember which user has logged in
        db.execute("SELECT rowid FROM users WHERE email = ?", [request.form.get("email")])
        session["user_id"] = db.fetchall()[0][0]

        return redirect("/home")

@app.route("/logout")
def logout():
    """Logs user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to initial page
    return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
