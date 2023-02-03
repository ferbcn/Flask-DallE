# Built-in Imports
import json
import os
import base64

# OpenAI
import openai

# Flask
import requests
from flask import Flask, render_template, request, flash, redirect, url_for, send_file
# Flask SQLAlchemy, Database
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, current_user, logout_user

from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from datetime import datetime
# from flask_migrate import Migrate

openai.api_key = os.getenv("OPENAI_KEY")
quote_url = 'https://zenquotes.io/api/quotes'

# Local DB
# basedir = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data.sqlite')

db_name = os.environ.get('DB_NAME')
db_user = os.environ.get('DB_USER')
db_pass = os.environ.get('DB_PASSWORD')
db_url = os.environ.get('DB_URL')

basedir = f"postgresql://{db_user}:{db_pass}@{db_url}:5432/{db_name}"

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = basedir
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

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


#migrate = Migrate(app, db)

# flask --app main.py db init
# flask --app main.py db migrate
# flask --app main.py db upgrade

login = LoginManager()
login.init_app(app)

@login.user_loader
def load_user(id):
    return db.session.query(UserModel).get(int(id))


# Index It routes to index.html where the upload forms is
@app.route('/index', methods=['GET', 'POST'])
@app.route('/')
def index():
    ### Danger ###
    # Delete all users
    # db.session.query(UserModel).delete()
    # db.session.commit()
    # Delete all tables
    # db.drop_all()
    ##############
    # db.create_all()

    # read last 10 images from db
    # images = FileContent.query.limit(10).all()
    images = FileContent.query.order_by(-FileContent.id).limit(10).all()
    if current_user.is_authenticated:
        user_auth = True
    else:
        user_auth = False
    return render_template('index.html', images=images, user_auth=user_auth)


@app.route('/quote/', methods=['GET', 'POST'])
def quote():
    if current_user.is_authenticated:
        user_auth = True
    else:
        user_auth = False

    if request.method == 'POST':
        quote = request.form['quote']
        author = request.form['author']
        quote_author = {'quote': quote, 'author': author}
        # Generate Image on Dall-E
        try:
            url = get_image_url(quote)
            response = requests.get(url, stream=True)
            data = response.content
            render_file = render_picture(data)
            # add file to db
            new_file = FileContent(title=author, data=data, rendered_data=render_file)
            db.session.add(new_file)
            db.session.commit()
            image = {'url': url}
            return render_template('quote.html', quote=quote_author, image=image, user_auth=user_auth)
        except Exception as e:
            print(e)
            flash('Image creation error!', 'alert')

    try:
        response = requests.get(quote_url)
        data_str = response.text
        data = json.loads(data_str)[0]
        quote = data.get("q")
        author = data.get("a")
        quote_author = {'quote': quote, 'author': author}

    except Exception as e:
        print(e)
        quote_author = None

        flash('Quote retrieval error!', 'alert')

    return render_template('quote.html', quote=quote_author, user_auth=user_auth)


@app.route('/create/', methods=('GET', 'POST'))
def create():
    if current_user.is_authenticated:
        user_auth = True
    else:
        user_auth = False

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!', 'alert')
        elif not content:
            flash('Content is required!', 'alert')
        else:
            try:
                url = get_image_url(content)
                response = requests.get(url, stream=True)
                data = response.content
                render_file = render_picture(data)
                new_file = FileContent(title=title, data=data, rendered_data=render_file)
                db.session.add(new_file)
                db.session.commit()
                image = {"title": title, 'url': url}
                return render_template('create.html', image=image, user_auth=user_auth)

            except Exception as e:
                print(e)
                flash('Image creation error! Please, try something else.', 'alert')

    return render_template('create.html', user_auth=user_auth)


@app.route('/delete', methods=['GET'])
@login_required
def delete():
    img_id = request.args['img_id']
    FileContent.query.filter_by(id=img_id).delete()
    db.session.commit()
    flash(f"Image deleted!", 'success')
    return redirect(url_for('index'))


@app.route('/about', methods=['GET'])
def about():
    if current_user.is_authenticated:
        user_auth = True
    else:
        user_auth = False

    try:
        num_images = FileContent.query.count()
    except Exception as e:
        print(e)
        num_images = None
    return render_template('about.html', num_images=num_images, user_auth=user_auth)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        user = UserModel.query.filter_by(username=username).first()
        if user is not None and user.check_password(request.form['password']):
            login_user(user)
            flash('User logged in!', 'success')
            return redirect(url_for('index'))
        flash('Wrong credentials!', 'alert')

    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if len(username) < 3:
            flash("Username too short", 'alert')
        elif len(password) < 3:
            flash("Password too short", 'alert')
        else:
            existing_user = UserModel.query.filter_by(username=username).first()
            if existing_user is None:
                # create user if it does not exist in DB
                try:
                    user = UserModel(username=username)
                    user.set_password(password)
                    db.session.add(user)
                    db.session.commit()
                    flash(f"User {username} created!", 'success')
                    return redirect(url_for('login'))
                except Exception as e:
                    print(e)
                    flash("DB Error!", 'alert')
            # user already exists
            else:
                flash("Username already in use!", 'alert')
    # GET request
    return render_template('register.html')


@app.route('/logout')
def logout():
    logout_user()
    flash(f"User logged out!", 'success')
    return redirect(url_for('index'))


def get_image_url(prompt):
    """Get the image from the prompt."""
    response = openai.Image.create(prompt=prompt, n=1, size="512x512")
    image_url = response["data"][0]["url"]
    return image_url


# needed to save the image in base64 in DB: this should be don in an object storage like S3
def render_picture(data):
    render_pic = base64.b64encode(data).decode('ascii')
    return render_pic


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(host='0.0.0.0', threaded=True, port=80, debug=True)
