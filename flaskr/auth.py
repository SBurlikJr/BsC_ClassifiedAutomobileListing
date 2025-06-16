from flask import Blueprint, render_template, request, redirect, url_for, session

from . import bcrypt, db
from .models import User
bp = Blueprint("auth", __name__, url_prefix="/")


@bp.route("login", methods=["POST", "GET"])
def login():
    error_message = ""
    if request.method == "GET":
        if not session:
            return render_template("Auth/Login.html")
        else:
            return redirect(url_for("user.home",
                                    email=session['email']))
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user is not None and bcrypt.check_password_hash(user.password, password):
            session['logged_in'] = True
            session['email'] = email
            session['id'] = user.id
            session['role'] = user.role_id
            return redirect(url_for('main.home'))
        elif user is not None:
            error_message = "Login failed. Password incorrect."
            return render_template("Auth/Login.html",
                                   error_message=error_message)
        else:
            error_message = "Such user doesn't exist"
            return render_template("Auth/Login.html",
                                   error_message=error_message)


@bp.route("signup", methods=["POST", "GET"])
def signup():
    error_message = ""
    if request.method == "GET":
        return render_template("Auth/Signup.html")
    if request.method == "POST":
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()

        if user is None:
            password_hash = (bcrypt.generate_password_hash(password)
                             .decode('utf-8'))

            new_user = User(email=email, password=password_hash)
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for('user.home'))
        else:
            error_message = "Email already used."
            return render_template("Auth/Signup.html",
                                   error_message=error_message)


@bp.route("logout")
def logout():
    session.clear()
    return redirect(url_for('main.home'))
