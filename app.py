# app.py
from flask import Flask, render_template, request, url_for, flash, redirect
import openai
import os

openai.api_key = os.getenv("OPENAI_KEY")


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY")


images = [{'title': 'Lasting Rainbow',
         'content': 'Hello World',
         'url': 'static/images/miro.jpg'},
        {'title': 'Superb Firework',
         'content': 'Hello Flask',
         'url': 'static/images/rock.jpg'},
        ]


@app.route('/')
def index():
    print(images)
    return render_template('index.html', images=list(reversed(images)))


@app.route('/create/', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        url = get_image_url(content)

        if not title:
            flash('Title is required!')
        elif not content:
            flash('Content is required!')
        else:
            images.append({'title': title, 'content': content, 'url': url})
            return redirect(url_for('index'))

    return render_template('create.html')


def get_image_url(prompt):
    """Get the image from the prompt."""
    response = openai.Image.create(prompt=prompt, n=1, size="1024x1024")
    image_url = response["data"][0]["url"]
    return image_url

if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000, debug=True)
