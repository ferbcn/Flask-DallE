# Built-in Imports
import os
from datetime import datetime
from base64 import b64encode
import base64
from io import BytesIO #Converts data from Database into bytes

# Flask
from flask import Flask, render_template, request, flash, redirect, url_for, send_file # Converst bytes into a file for downloads

# Flask SQLAlchemy, Database
from flask_sqlalchemy import SQLAlchemy

basedir = 'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'data.sqlite')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = basedir
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'dev'
db = SQLAlchemy(app)

# Picture table. By default the table name is filecontent
class FileContent(db.Model):
    """
    The first time the app runs you need to create the table. In Python
    terminal import db, Then run db.create_all()
    """
    """ ___tablename__ = 'yourchoice' """   # You can override the default table name

    id = db.Column(db.Integer,  primary_key=True)
    title = db.Column(db.Text)
    data = db.Column(db.LargeBinary, nullable=False) #Actual data, needed for Download
    rendered_data = db.Column(db.Text, nullable=False)#Data to render the pic in browser
    pic_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    def __repr__(self):
        return f'Pic Name: {self.title}, created on: {self.pic_date}'


def render_picture(data):
    render_pic = base64.b64encode(data).decode('ascii')
    return render_pic


# Index It routes to index.html where the upload forms is
@app.route('/index', methods=['GET', 'POST'])
@app.route('/')
def index():
    #db.create_all()

    # TODO: Read images from DB and pass to template
    images = FileContent.query.all()
    for image in images:
        print(image)

    flash(images)
    return render_template('index.html')


@app.route('/upload/', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        title = request.form['title']
        file = request.files['inputFile']
        if not title:
            flash('Title is required!')
        elif not file:
            flash('Image is required!')
        else:
            data = file.read()
            render_file = render_picture(data)
            newFile = FileContent(title=title, data=data,
                                  rendered_data=render_file)
            db.session.add(newFile)
            db.session.commit()

            return redirect(url_for('index'))


    return render_template('upload.html')

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000, debug=True)
