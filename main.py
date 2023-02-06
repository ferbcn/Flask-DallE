# Built-in Imports
import json
import os
import base64

# OpenAI
import threading

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
from flask_migrate import Migrate

from flask_socketio import SocketIO, emit

import boto3

openai.api_key = os.getenv("OPENAI_KEY")
quote_url = 'https://zenquotes.io/api/quotes'

# Local DB
# basedir = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data.sqlite')

DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASS = os.environ.get('DB_PASSWORD')
DB_URL = os.environ.get('DB_URL')

SECRET_KEY = os.environ.get('SECRET_KEY')

basedir = f"postgresql://{DB_USER}:{DB_PASS}@{DB_URL}:5432/{DB_NAME}"

# Local DB
# basedir = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data.sqlite')

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY
app.config['SQLALCHEMY_DATABASE_URI'] = basedir
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

socketio = SocketIO(app)

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
    filename = db.Column(db.Text)
    data = db.Column(db.LargeBinary, nullable=False)  # Actual data, needed for Download
    rendered_data = db.Column(db.Text, nullable=False)  # Data to render the pic in browser
    pic_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'Pic Name: {self.title}, created on: {self.pic_date}'


socketio = SocketIO(app, always_connect=True, engineio_logger=True)


linode_obj_config = {
    "aws_access_key_id": "JMUZU4LBJM1GITDW7ZII",
    "aws_secret_access_key": "bn0hxe2QhBIDi9WJue3T8p80IU3W2Cpt5hA9vaoM",
    "endpoint_url": "https://art-intel.eu-central-1.linodeobjects.com",
}

client = boto3.client("s3", **linode_obj_config)


migrate = Migrate(app, db)

# flask --app main.py db init
# flask --app main.py db migrate
# flask --app main.py db upgrade

login = LoginManager()
login.init_app(app)


@login.user_loader
def load_user(id):
    #return db.session.query(UserModel).get(int(id))
    return UserModel.query.get(int(id))


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

            # make filename and upload file to S3
            filename = make_filename(author)
            create_s3_upload_thread(filename, data)

            render_file = render_picture(data)
            # add file to db
            new_file = FileContent(title=author, filename=filename, data=data, rendered_data=render_file)
            db.session.add(new_file)
            db.session.commit()
            image = {'title': author, 'url': url}
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

                # make filename and upload file to S3
                filename = make_filename(title)
                create_s3_upload_thread(filename, data)

                # save to Postgres
                render_file = render_picture(data)
                new_file = FileContent(title=title, data=data, filename=filename, rendered_data=render_file)
                db.session.add(new_file)
                db.session.commit()
                image = {"title": title, 'url': url}
                app.logger.info(f'{current_user} created an image')
                return render_template('create.html', image=image, user_auth=user_auth)

            except Exception as e:
                print(e)
                flash('Image creation error! Please, try something else.', 'alert')

    return render_template('create.html', user_auth=user_auth)


@app.route('/edit/', methods=['GET', 'POST'])
def edit():
    if current_user.is_authenticated:
        user_auth = True
    else:
        user_auth = False

    if request.method == 'POST':
        title = request.form['title']
        instructions = request.form['instructions']
        file = request.files['inputFile']
        if not title:
            flash('Title is required!', 'alert')
        elif not file:
            flash('Image is required!', 'alert')
        elif not instructions:
            flash('AI instructions required!', 'alert')
        else:
            data = file.read()

            # make filename and upload file to S3
            filename = make_filename(title)
            create_s3_upload_thread(filename, data)

            # generate new image
            try:
                new_image_url = edit_image_ai(data, instructions)
                response = requests.get(new_image_url, stream=True)
                data = response.content

                # make filename and upload file to S3
                filename = "AI_" + make_filename(title)
                create_s3_upload_thread(filename, data)

                render_file = render_picture(data)
                new_file = FileContent(title=title, data=data, filename=filename, rendered_data=render_file)
                db.session.add(new_file)
                db.session.commit()
                image = {"title": title, 'url': new_image_url}
                app.logger.info(f'{current_user} created an image')
                return render_template('edit.html', image=image, user_auth=user_auth)

            except Exception as e:
                print(e)
                app.logger.warning(f'API error {e}')
                flash('Wrong image format', 'alert')

    return render_template('edit.html', user_auth=user_auth)


@app.route('/about', methods=['GET'])
def about():
    if current_user.is_authenticated:
        user_auth = True
    else:
        user_auth = False

    try:
        num_images = FileContent.query.count()
        last_image = FileContent.query.order_by(-FileContent.id).first()
        total_images = last_image.id
    except Exception as e:
        print(e)
        num_images = None
        total_images = None
    return render_template('about.html', num_images=num_images, total_images=total_images, user_auth=user_auth)


@app.route('/delete', methods=['GET'])
# avoiding ugly page redirect here
# @login_required
def delete():
    if not current_user.is_authenticated:
        flash("Not authenticated!", 'alert')
        return redirect(url_for('index'))
    else:
        img_id = request.args['img_id']
        FileContent.query.filter_by(id=img_id).delete()
        db.session.commit()
        flash(f"Image deleted!", 'success')
        app.logger.info(f'{current_user} deleted image id={img_id}')
        return redirect(url_for('index'))


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

    # user registration deactivated
    if request.method == 'POST':
        flash("Sorry, registration is not available!", 'alert')
    """
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
    """
    # GET request
    return render_template('register.html')


@app.route('/logout')
def logout():
    logout_user()
    flash(f"User logged out!", 'success')
    return redirect(url_for('index'))


def create_s3_upload_thread(filename, data):
    s3_upload_thread = threading.Thread(target=s3_upload_job(filename, data))
    s3_upload_thread.start()
    print('Scheduled S3 upload job!')


def s3_upload_job(filename, data):
    # some long running processing here
    try:
        filepath = "static/images/" + filename
        with open(filepath, 'wb') as f:
            f.write(data)
        client = boto3.client("s3", **linode_obj_config)
        client.upload_file(Filename=filepath, Bucket='DallE-Images', Key=filename)
        os.remove(filepath)
    except Exception as e:
        print(e)


def make_filename(title):
    return title.replace(" ", "_") + "_" + str(datetime.utcnow()).replace(" ", "_") + ".png"


def get_image_url(prompt):
    """Get the image from the prompt."""
    response = openai.Image.create(prompt=prompt, n=1, size="512x512")
    image_url = response["data"][0]["url"]
    return image_url


# needed to save the image in base64 in DB: this should be don in an object storage like S3
def render_picture(data):
    render_pic = base64.b64encode(data).decode('ascii')
    return render_pic


def edit_image_ai(image, instructions):
    response = openai.Image.create_edit(
        image=image,
        prompt=instructions,
        n=1,
        size="512x512"
    )
    image_url = response['data'][0]['url']
    return image_url


@socketio.on('connect')
def connected():
    print('connect')


@socketio.on('disconnect')
def disconnect():
    print('disconnect')


@socketio.on('my_event')
def handle_my_custom_event(json):
    last_img_id = int(json["data"])
    print("last img id:", last_img_id)
    print(f"Loading more images...")
    new_image_count = 5

    # Hacky way for retrieving next images in db
    images = []
    found_img_count = 0
    while (found_img_count < new_image_count):
        # Iterate through DB: TODO: look-up sqlalchemy on this topic
        last_img_id -= 1
        if last_img_id <= 0:
            break
        #next_image = FileContent.query.get(last_img_id)
        next_image = db.session.get(FileContent, last_img_id)
        if next_image is not None:
            images.append(next_image)
            found_img_count += 1
    # End of Hack

    images_json_data = []
    for image in images:
        img = {"title": image.title, "data": image.rendered_data, "image_id": image.id}
        images_json_data.append(img)

    print("Sending images to web-socket!")
    emit('image feed', images_json_data)


@socketio.on('delete_event')
def handle_delete_event(json):
    image_id = int(json["data"])
    print(f"Deleting image... {image_id}")
    if current_user.is_authenticated:
        # FileContent.query.filter_by(id=image_id).delete()
        item = db.session.get(FileContent, image_id)
        db.session.delete(item)
        db.session.commit()
        flash(f"Image deleted!", 'success')
    else:
        print("Not logged in. Image not deleted.")


if __name__ == '__main__':
    try:
        socketio.run(app, host='0.0.0.0', port='5000')
    except RuntimeError as e:
        print(e)
        socketio.run(app, host='0.0.0.0', port='5000', allow_unsafe_werkzeug=True)