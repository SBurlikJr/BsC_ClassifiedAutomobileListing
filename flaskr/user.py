from flask import Blueprint, render_template, session, request, url_for, redirect

from . import db, bcrypt
from .models import User, Listing, CarSetting, CarModel, CarMaker

bp = Blueprint("user", __name__, url_prefix="/profile")


@bp.route("/", methods=['GET', 'POST'])
def home():
    if session.get('logged_in'):
        user = User.query.filter_by(email=session.get('email')).first()
        return render_template("Profile/profile.html",
                               user=user)
    return render_template("Auth/login.html")


@bp.route("/user_lists")
def user_listings():
    if session.get('logged_in'):
        user = User.query.filter_by(email=session.get('email')).first()
        user_listings = (db.session.query(Listing)
                         .join(CarSetting)
                         .join(CarModel)
                         .join(CarMaker)
                         .filter(Listing.user_id == user.id).all())

        return render_template("UsersListing/userslisting.html",
                               user=user,
                               listings=user_listings)
    return "You have no permission for this page."


@bp.route("/mod_lists")
def mod_listings():
    if session.get('logged_in') and session['role'] == 2:
        user_listings = (db.session.query(Listing)
                         .join(CarSetting)
                         .join(CarModel)
                         .join(CarMaker)
                         .filter(Listing.is_unlisted == True).all())

        return render_template("UsersListing/modlisting.html",
                               listings=user_listings)
    return "You have no permission for this page."


@bp.route("/mod_lists/unflag/<int:item_id>", methods=['POST'])
def unflag(item_id):
    if session.get('logged_in') and session['role'] == 2:
        listing = Listing.query.get(item_id)
        listing.is_unlisted = False
        db.session.commit()
        return redirect(url_for("user.mod_listings"))


@bp.route("/user/info", methods=['GET', 'POST'])
def info():
    if session.get('logged_in'):
        if request.method == "GET":
            return render_template("Profile/info.html")
        if request.method == "POST":
            error_message = ""
            phone_num = request.form.get('phone_number')
            current_pass = request.form.get('current_password')
            new_pass = request.form.get('new_password')

            user = User.query.get(session['id'])

            if current_pass != "" and new_pass != "":
                if bcrypt.check_password_hash(user.password, current_pass):
                    user.password = (bcrypt.generate_password_hash(new_pass)
                                     .decode('utf-8'))
                else:
                    error_message = "Current password is incorrect."
                    return render_template('Profile/info.html', error_message=error_message)
            if phone_num != "":
                user.phone_number = phone_num

            db.session.commit()
            return redirect(url_for('user.home'))
