import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

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
        db.execute("SELECT rowid FROM users WHERE email = ?", [request.form.get("email")])
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

        #session["user_id"] = db.execute("SELECT id FROM users WHERE name = ?", [request.form.get("name")])[0]["id"]

        flash("Registered!")

        return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Logs user in"""
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        return redirect("/")

if __name__ == "__main__":
    app.run(debug=True)
