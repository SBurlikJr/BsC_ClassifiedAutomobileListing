from sqlalchemy.orm import relationship

from . import db


class CarMaker(db.Model):
    """
    id
    name
    """
    __tablename__ = 'car_maker'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text(24))

    maker = relationship("CarModel")


class CarModel(db.Model):
    """DB model for the model of the car

   :Parameters
    id (int): - PK, not null; identification of each model
    maker_id (int): - not null
    name (text): - not null
    """
    __tablename__ = 'car_model'
    id = db.Column(db.Integer, primary_key=True)
    maker_id = db.Column(db.Integer, db.ForeignKey('car_maker.id'))
    name = db.Column(db.Text(24))

    makers = relationship('CarMaker', back_populates='maker')
    settings_m = relationship('CarSetting', back_populates='models')


class CarSetting(db.Model):
    """
    id
    model_id
    yeor_of_issue
    length
    width
    height
    engine_capacity
    fuel_type
    drivetrain
    transmission
    mileage
    is_registered
    registration_date
    is_inspected
    inspection_date
    price
    description
    location_city
    preview_image_id
    """
    __tablename__ = 'car_setting'

    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('car_model.id'))
    year_of_issue = db.Column(db.Integer)
    length = db.Column(db.Integer)
    width = db.Column(db.Integer)
    height = db.Column(db.Integer)
    engine_capacity = db.Column(db.Numeric)
    fuel_type = db.Column(db.Text)
    drivetrain = db.Column(db.Text)
    transmission = db.Column(db.Text)
    mileage = db.Column(db.Integer)
    is_registered = db.Column(db.Boolean)
    registration_date = db.Column(db.Text)
    is_inspected = db.Column(db.Boolean)
    inspection_date = db.Column(db.Text)
    price = db.Column(db.Numeric)
    description = db.Column(db.Text)
    location_city = db.Column(db.Text)
    body_type = db.Column(db.Text)

    listings = relationship("Listing", back_populates="settings_l")
    models = relationship("CarModel", back_populates="settings_m")


class User(db.Model):
    """
    id
    email
    password
    phone_number
    role_id
    """
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('user_role.id'), nullable=False, default=1)
    email = db.Column(db.String(48), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    phone_number = db.Column(db.Numeric(12), unique=True, nullable=True)

    def __repr__(self):
        return f'<User {self.email}>'


class Listing(db.Model):
    """
    id
    user_id
    car_id
    created_at
    voided_at
    is_unlisted
    preview_image_path
    """
    __tablename__ = 'car_listing'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    car_setting_id = db.Column(db.Integer, db.ForeignKey('car_setting.id'), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False)
    is_unlisted = db.Column(db.Boolean, default=False)
    preview_image_path = db.Column(db.Text(256), db.ForeignKey('car_image.file_path'), nullable=True)

    settings_l = relationship("CarSetting", back_populates="listings")

    def __repr__(self):
        return f'<Listing {self.id}>'


class ImageRecord(db.Model):
    """
    id
    filename
    file_path
    mimetype
    listing_id
    uploaded_at
    """
    __tablename__ = 'car_image'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.Text(128), unique=True, nullable=False)
    file_path = db.Column(db.Text(256), unique=True, nullable=False)
    mimetype = db.Column(db.Text(16), unique=True, nullable=False)
    listing_id = db.Column(db.Integer, db.ForeignKey('car_listing.id'), nullable=False)
    uploaded_at = db.Column(db.DateTime)


class UserRole(db.Model):
    """
    id
    name
    """
    __tablename__ = 'user_role'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text(24), unique=True, nullable=False)


class City(db.Model):
    """
    id
    name
    """
    __tablename__ = 'city'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Text(24), unique=True, nullable=False)
