import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required, load_csv

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
        connection.commit()

        flash("Successfully changed password!")

        return redirect("/profile")

@app.route("/vaccines", methods=["GET", "POST"])
@login_required
def vaccines():
    """Displays vaccine tracker"""
    vaccines = {"MCV1": "The percentage of children under 1 year of age who have received at least one dose of measles-containing vaccine in a given year. For countries recommending the first dose of measles vaccine in children over 12 months of age, the indicator is calculated as the proportion of children less than 12-23 months of age receiving one dose of measles-containing vaccine.",
                "MCV2": "The percentage of children who have received two doses of measles containing vaccine (MCV2) in a given year, according to the nationally recommended schedule.",
                "BCG": "The percentage of 1-year-olds who have received one dose of bacille Calmette-Guérin (BCG) vaccine in a given year.",
                "DTP3": "The percentage of 1-year-olds who have received three doses of the combined diphtheria, tetanus toxoid and pertussis vaccine in a given year.",
                "PAB": "The proportion of neonates in a given year that can be considered as having been protected against tetanus as a result of maternal immunization.",
                "PCV3": "The percentage of 1-year-olds who have received three doses of pneumococcal conjugate vaccine (PCV3) in a given year.",
                "HepB3": "The percentage of 1-year-olds who have received three doses of hepatitis B vaccine in a given year.",
                "Pol3": "The percentage of 1-year-olds who have received three doses of polio vaccine in a given year.",
                "Hib3": "The percentage of 1-year-olds who have received three doses of Haemophilus influenzae type B vaccine in a given year.",
                "ROTAC": "The percentage of surviving infants who received the final recommended dose of rotavirus vaccine, which can be either the 2nd or the 3rd dose depending on the vaccine in a given year."}

    # Dictionary of dictionaries for vaccine data
    all_vaccines = {}
    for vaccine in vaccines:
        all_vaccines[vaccine] = load_csv(vaccine)
    if request.method == "GET":
        return render_template("vaccines.html", all_vaccines=all_vaccines)
    if request.method == "POST":
        if "search" in request.form:
            # Check that user entered vaccine abbreviation
            if not request.form.get("abbr"):
                flash("Must enter vaccine abbr.")
                return redirect("/vaccines")

            # Check if user input is an actual vaccine
            abbr = request.form.get("abbr")
            if abbr not in vaccines:
                flash("Data unavailable")
                return redirect("/vaccines")
            else:
                return render_template("vaccinedata.html", vaccine=abbr, vaccine_data=all_vaccines[abbr], vaccine_info=vaccines[abbr], startyear=1980, endyear=2018)

        if "datasearch" in request.form:
            vaccine = request.form["datasearch"]
            # If nothing is inputted, refresh original page
            if not request.form.get("country") and not request.form.get("startyear") and not request.form.get("endyear"):
                return render_template("vaccinedata.html", vaccine=vaccine, vaccine_data=all_vaccines[vaccine], vaccine_info=vaccines[vaccine], startyear=1980, endyear=2018)

            # Check that country exists
            country = request.form["country"]
            if country != "" and country not in all_vaccines[vaccine]:
                flash("Country data not available")
                return render_template("vaccinedata.html", vaccine=vaccine, vaccine_data=all_vaccines[vaccine], vaccine_info=vaccines[vaccine], startyear=1980, endyear=2018)

            # Check that years are valid
            startyear = request.form["startyear"]
            endyear = request.form["endyear"]
            if startyear != "" and (int(startyear) > 2018 or int(startyear) < 1980):
                flash("Invalid start year")
                return render_template("vaccinedata.html", vaccine=vaccine, vaccine_data=all_vaccines[vaccine], vaccine_info=vaccines[vaccine], startyear=1980, endyear=2018)
            if endyear != "" and (int(endyear) > 2018 or int(endyear) < 1980):
                flash("Invalid end year")
                return render_template("vaccinedata.html", vaccine=vaccine, vaccine_data=all_vaccines[vaccine], vaccine_info=vaccines[vaccine], startyear=1980, endyear=2018)
            if startyear != "" and endyear != "" and int(startyear) > int(endyear):
                flash("End year must be later than start year")
                return render_template("vaccinedata.html", vaccine=vaccine, vaccine_data=all_vaccines[vaccine], vaccine_info=vaccines[vaccine], startyear=1980, endyear=2018)

            start = 1980
            if startyear != "":
                start = int(startyear)
            end = 2018
            if endyear != "":
                end = int(endyear)

            spliced_dict = {}
            if country != "":
                spliced_dict[country] = all_vaccines[vaccine][country]
            else:
                spliced_dict = all_vaccines[vaccine]
            for country in spliced_dict:
                spliced_dict[country] = spliced_dict[country][2018-end:2019-start]

            return render_template("vaccinedata.html", vaccine=vaccine, vaccine_data=spliced_dict, vaccine_info=vaccines[vaccine], startyear=start, endyear=end)

        for vaccine in vaccines:
            if vaccine in request.form:
                return render_template("vaccinedata.html", vaccine=vaccine, vaccine_data=all_vaccines[vaccine], vaccine_info=vaccines[vaccine], startyear=1980, endyear=2018)


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

        flash("You're logged in!")

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
