# app.py
from flask import Flask, render_template, request, url_for, flash, redirect

app = Flask(__name__)
app.config['SECRET_KEY'] = 'fb432487413e7ef019fe2000b2fe94277565b7218be4e100'

images = [  {'title': 'Lasting Rainbow',
         'content': 'Hello World',
         'url': 'miro.jpg'},
        {'title': 'Superb Firework',
         'content': 'Hello Flask',
         'url': 'rock.jpg'},
        ]


@app.route('/')
def index():
    return render_template('index.html', images=images)


@app.route('/create/', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        url = request.form['url']

        if not title:
            flash('Title is required!')
        elif not content:
            flash('Content is required!')
        else:
            images.append({'title': title, 'content': content, 'url': url})
            return redirect(url_for('index'))

    return render_template('create.html')


if __name__ == '__main__':
    # Threaded option to enable multiple instances for multiple user access support
    app.run(threaded=True, port=5000, debug=True)
