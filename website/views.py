from flask import Blueprint, render_template, session, current_app

views = Blueprint('views', __name__)


@views.route('/')
def home():
    session.permanent = False
    return render_template("base.html")


