from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class UserModel(UserMixin, db.Model):
    __tablename__ = 'art-users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    password_hash = db.Column(db.String())

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Picture table. By default the table name is filecontent
class FileContent(db.Model):
    """ ___tablename__ = 'yourchoice' """  # You can override the default table name
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.Text)
    data = db.Column(db.LargeBinary, nullable=False)  # Actual data, needed for Download
    rendered_data = db.Column(db.Text, nullable=False)  # Data to render the pic in browser
    pic_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'Pic Name: {self.title}, created on: {self.pic_date}'
