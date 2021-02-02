from flask import Flask, flash, redirect, render_template, request, session
import sqlite3

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure SQLite database
db = sqlite3.connect("who.db")

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Registers user"""
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
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
