import os
from math import ceil
from datetime import datetime
from shutil import rmtree
from uuid import uuid4

from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from sqlalchemy import asc
from werkzeug.utils import secure_filename
from PIL import Image, UnidentifiedImageError

from . import db
from .models import Listing, ImageRecord, User, CarMaker, CarModel, CarSetting, City


bp = Blueprint("listing", __name__, url_prefix="/lists")


@bp.route("", methods=["GET"])
def listing():
    list_of_makers = CarMaker.query.all()

    query = (db.session.query(Listing)
              .join(CarSetting)
              .join(CarModel)
              .join(CarMaker)).filter(Listing.is_unlisted == False)

    maker = request.args.get("maker")
    model = request.args.get("model_select")
    body_type = request.args.get("body_type")
    transmission = request.args.get("transmission")
    drivetrain = request.args.get("drivetrain")
    fuel_type = request.args.get("fuel_type")
    mileage_from = request.args.get("mileage_from")
    mileage_to = request.args.get("mileage_to")
    price_form = request.args.get("price_from")
    price_to = request.args.get("price_to")
    year_from = request.args.get("year_from")
    year_to = request.args.get("year_to")

    if maker:
        query = query.filter(CarMaker.id == maker)
    if model:
        query = query.filter(CarModel.id == model)
    if body_type:
        query = query.filter(CarSetting.body_type == body_type)
    if transmission:
        query = query.filter(CarSetting.transmission == transmission)
    if drivetrain:
        query = query.filter(CarSetting.drivetrain == drivetrain)
    if fuel_type:
        query = query.filter(CarSetting.fuel_type == fuel_type)
    if mileage_from:
        query = query.filter(CarSetting.mileage >= mileage_from)
    if mileage_to:
        query = query.filter(CarSetting.mileage <= mileage_to)
    if price_form:
        query = query.filter(CarSetting.price >= price_form)
    if price_to:
        query = query.filter(CarSetting.price <= price_to)
    if year_from:
        query = query.filter(CarSetting.year_of_issue >= year_from)
    if year_to:
        query = query.filter(CarSetting.year_of_issue <= year_to)

    list_of_listings = query.all()

    LISTINGS_PER_PAGE = 18

    page = request.args.get("page", 1, type=int)

    start = (page - 1) * LISTINGS_PER_PAGE
    end = start + LISTINGS_PER_PAGE

    paginated_items = list_of_listings[start:end]

    total_pages = ceil(len(list_of_listings) / LISTINGS_PER_PAGE)

    return render_template("GlobalListing/listings.html",
                           list_of_items=paginated_items,
                           list_of_makers=list_of_makers,
                           page=page,
                           total_pages=total_pages)


@bp.route("/<int:item_id>")
def individual_listing(item_id):
    individual_listing = Listing.query.get(item_id)
    query = (db.session.query(Listing)
              .join(CarSetting)
              .join(CarModel)
              .join(CarMaker)
              .filter(Listing.id == item_id)
              .first())

    print(query.preview_image_path)
    list_of_images = (ImageRecord.query
                      .filter_by(listing_id=individual_listing.id).all())

    if individual_listing is None:
        return "Item not found", 404

    return render_template("GlobalListing/individual_listing.html",
                           item=query,
                           list_of_images=list_of_images)


@bp.route("/get_models/<int:maker>", methods=["GET"])
def get_models(maker):
    maker_id = maker
    temp_list_of_models = (CarModel.query
                           .filter_by(maker_id=maker_id)
                           .order_by(asc(CarModel.name)).all())
    list_of_models = [{'id': model.id, 'name': model.name} for model in temp_list_of_models]
    if maker_id:
        return jsonify(list_of_models)
    else:
        return jsonify([])


@bp.route("/create", methods=["GET", "POST"])
def create_listing():
    if not session.get("logged_in"):
        return render_template("Home/home.html")
    if request.method == "GET":
        list_of_makers = CarMaker.query.order_by(asc(CarMaker.name)).all()

        list_of_cities = City.query.all()

        return render_template("GlobalListing/new_listing.html",
                               list_of_makers=list_of_makers,
                               list_of_cities=list_of_cities)
    elif request.method == "POST":

        is_image_present = True

        try:
            images = request.files.getlist("image")
            image = Image.open(images[0])
        except UnidentifiedImageError:
            is_image_present = False
            print("No image")
        finally:

            model = request.form.get("model_select")
            body_type = request.form.get("body_type")

            transmission = request.form.get("transmission")
            drivetrain = request.form.get("drivetrain")
            fuel_type = request.form.get("fuel_type")
            mileage = request.form.get("mileage")
            price = request.form.get("price")
            engine_capacity = request.form.get("engine_capacity")
            year_of_issue = request.form.get("year_of_issue")

            length = request.form.get("length")
            width = request.form.get("width")
            height = request.form.get("height")

            inspection_date = request.form.get("inspection_date")
            registration_date = request.form.get("registration_date")

            location_city = request.form.get("location_city")
            description = request.form.get("description")

            new_setting = CarSetting(model_id=model,
                                     transmission=transmission,
                                     drivetrain=drivetrain,
                                     fuel_type=fuel_type,
                                     mileage=mileage,
                                     price=price,
                                     year_of_issue=year_of_issue,
                                     engine_capacity=engine_capacity,
                                     length=length,
                                     width=width,
                                     height=height,
                                     is_inspected=False,
                                     inspection_date=inspection_date if not None else "",
                                     is_registered=False,
                                     registration_date=registration_date if not None else "",
                                     location_city=location_city,
                                     description=description,
                                     body_type=body_type)

            db.session.add(new_setting)
            db.session.commit()

            car_setting_id = new_setting.id
            user_id = session.get("id")

            new_listing = Listing(user_id=user_id,
                                  car_setting_id=car_setting_id,
                                  created_at=datetime.now(),
                                  preview_image_path="")

            db.session.add(new_listing)
            db.session.commit()
            is_preview = True
            if is_image_present:
                current_folder = uuid4().hex

                if not os.path.exists(os.path.join('flaskr/static/images/user_listing_img', current_folder)):
                    os.makedirs(os.path.join('flaskr/static/images/user_listing_img', current_folder))

                IMG_SAVE_PATH = os.path.join('flaskr/static/images/user_listing_img', current_folder)

                temp_file_name_check = []
                file_name_duplicate_counter = {}

                for image in images:
                    filename = secure_filename(image.filename)

                    if filename not in temp_file_name_check:
                        temp_file_name_check.append(filename)
                        file_name_duplicate_counter[str(filename)] = 0
                    elif filename in temp_file_name_check:
                        file_name_duplicate_counter[str(filename)] = +1
                        filename = filename.join(file_name_duplicate_counter)

                    img = Image.open(image)

                    webp_filename = f"{os.path.splitext(filename)[0]}.webp"
                    webp_path = os.path.join(current_folder, webp_filename).replace("\\", "/")
                    webp_save_path = os.path.join(IMG_SAVE_PATH, webp_filename).replace("\\", "/")
                    img.save(webp_save_path, quality=80, format="WEBP")

                    new_image = ImageRecord(filename=webp_filename,
                                            file_path=webp_path,
                                            mimetype=image.mimetype,
                                            listing_id=new_listing.id,
                                            uploaded_at=datetime.now())

                    if is_preview:
                        new_listing.preview_image_path = new_image.file_path
                        is_preview = False
                    db.session.add(new_image)
                    db.session.commit()

        return render_template("Home/home.html")


@bp.route("/<int:item_id>/edit", methods=["GET", "POST"])
def edit_listing(item_id):
    listing = (db.session.query(Listing)
               .join(CarSetting)
               .join(CarModel)
               .join(CarMaker).filter(Listing.id == item_id).first())

    cities = City.query.all()
    images = request.files.getlist("image")
    ref_image = ImageRecord.query.filter_by(listing_id=listing.id).first()

    maker_choice = listing.settings_l.models.makers.id
    model_choice = listing.settings_l.models.name
    body_type_choice = listing.settings_l.body_type
    drivetrain_choice = listing.settings_l.drivetrain
    transmission_choice = listing.settings_l.transmission
    fuel_type_choice = listing.settings_l.fuel_type
    city_choice = listing.settings_l.location_city

    if not (session.get("logged_in") and session.get("id") == listing.user_id):
        return "Cannot edit listing", 403
    if request.method == "GET":
        return render_template('GlobalListing/edit_listing.html',
                               listing=listing,
                               maker_choice=maker_choice,
                               model_choice=model_choice,
                               body_type_choice=body_type_choice,
                               drivetrain_choice=drivetrain_choice,
                               fuel_type_choice=fuel_type_choice,
                               city_choice=city_choice,
                               transmission_choice=transmission_choice,
                               list_of_cities=cities)
    if request.method == "POST":
        new_value_maker = request.form.get("maker")
        new_value_model = request.form.get("model")

        listing.maker = new_value_maker
        listing.model = new_value_model

        db.session.commit()

        if ref_image is not None:
            # folder exists, use it.

            IMG_SAVE_PATH = os.path.join('flaskr/static/images/user_listing_img', ref_image.file_path.split("/")[0])

            temp_file_name_check = []
            file_name_duplicate_counter = {}

            for image in images:
                filename = secure_filename(image.filename)

                if filename not in temp_file_name_check:
                    temp_file_name_check.append(filename)
                    file_name_duplicate_counter[str(filename)] = 0
                elif filename in temp_file_name_check:
                    file_name_duplicate_counter[str(filename)] = +1
                    filename = filename.join(file_name_duplicate_counter)

                img = Image.open(image)

                webp_filename = f"{os.path.splitext(filename)[0]}.webp"
                webp_path = (os.path.join(ref_image.file_path.split("/")[0], webp_filename)
                             .replace("\\", "/"))
                webp_save_path = (os.path.join(IMG_SAVE_PATH, webp_filename)
                                  .replace("\\", "/"))
                img.save(webp_save_path, quality=80, format="WEBP")

                new_image = ImageRecord(filename=webp_filename,
                                        file_path=webp_path,
                                        mimetype=image.mimetype,
                                        listing_id=listing.id,
                                        uploaded_at=datetime.now())

                db.session.add(new_image)
                db.session.commit()

        else:
            # folder does not exist, create it.
            current_folder = uuid4().hex

            if not os.path.exists(os.path.join('flaskr/static/images/user_listing_img', current_folder)):
                os.makedirs(os.path.join('flaskr/static/images/user_listing_img', current_folder))

            IMG_SAVE_PATH = os.path.join('flaskr/static/images/user_listing_img', current_folder)

            temp_file_name_check = []
            file_name_duplicate_counter = {}

            for image in images:
                filename = secure_filename(image.filename)

                if filename not in temp_file_name_check:
                    temp_file_name_check.append(filename)
                    file_name_duplicate_counter[str(filename)] = 0
                elif filename in temp_file_name_check:
                    file_name_duplicate_counter[str(filename)] = +1
                    filename = filename.join(file_name_duplicate_counter)

                img = Image.open(image)

                webp_filename = f"{os.path.splitext(filename)[0]}.webp"
                webp_path = (os.path.join(current_folder, webp_filename)
                             .replace("\\", "/"))
                webp_save_path = (os.path.join(IMG_SAVE_PATH, webp_filename)
                                  .replace("\\", "/"))
                img.save(webp_save_path, quality=80, format="WEBP")

                new_image = ImageRecord(filename=webp_filename,
                                        file_path=webp_path,
                                        mimetype=image.mimetype,
                                        listing_id=listing.id,
                                        uploaded_at=datetime.now())

                db.session.add(new_image)
                db.session.commit()

        return redirect(url_for("user.user_listings"))


@bp.route("/<int:item_id>/delete")
def delete_listing(item_id):
    listing = Listing.query.get(item_id)
    image = ImageRecord.query.filter_by(listing_id=listing.id).first()
    images = ImageRecord.query.filter_by(listing_id=listing.id).all()

    if not (session.get("logged_in") and session.get("id") == listing.user_id):
        return "Cannot delete listing", 403

    db.session.delete(listing)

    for image in images:
        db.session.delete(image)

    if image is not None:
        IMG_FOLDER_PATH = os.path.join("flaskr/static/images/user_listing_img",
                                       image.file_path.split("/")[0]).replace(
                                    "\\", "/")
        if os.path.exists(IMG_FOLDER_PATH):
            print(image.file_path.split("/")[0])
            rmtree(IMG_FOLDER_PATH)

    db.session.commit()

    return redirect(url_for("user.user_listings"))


@bp.route("/<int:item_id>/flag", methods=["POST"])
def flag(item_id):
    listing = Listing.query.get(item_id)
    listing.is_unlisted = True
    db.session.commit()
    return redirect(url_for("listing.listing"))
