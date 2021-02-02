import os
import csv
from flask import redirect, render_template, request, session
from functools import wraps

def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function

def load_csv(filename):
    """Loads csv into dictionary"""
    file_dict = {}
    path = os.getcwd() + "/static/vaccine-data/" + filename + ".csv"
    with open(path, "r") as f:
        reader = csv.reader(f, delimiter=',')
        line_count = 0
        for row in reader:
            if line_count == 0:
                line_count += 1
            else:
                years = []
                for n in range(len(row)):
                    if n != 0:
                        years.append(row[n])
                file_dict[row[0]] = years
    return file_dict
