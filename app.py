from flask import Flask, flash, redirect, render_template, request, session

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

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

if __name__ == "__main__":
    app.run(debug=True)
