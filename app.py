from flask import Flask, render_template, request, session, redirect
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_mail import Mail
import math
import json
import os

cwd = os.getcwd()

with open(f'{cwd}/templates/config.json', 'r') as file:
    params = json.load(file)['parameters']
local_server = params['local_server']

app = Flask(__name__)
app.config['UPLOADER'] = params['location']
app.secret_key = 'super secret key'
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT='465',
    MAIL_USE_SSL=True,
    MAIL_USERNAME=params['gmail-user'],
    MAIL_PASSWORD=params['gmail-password']
)
mail = Mail(app)

if local_server:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_uri']
db = SQLAlchemy(app)


class Contacts(db.Model):
    SNO = db.Column(db.Integer, primary_key=True)
    FIRST_NAME = db.Column(db.String, nullable=False)
    LAST_NAME = db.Column(db.String, nullable=False)
    EMAIL = db.Column(db.String, unique=True)
    CONTACT_NO = db.Column(db.String, unique=True, nullable=False)
    MESSAGE = db.Column(db.String, unique=False, nullable=False)
    DATE = db.Column(db.String, nullable=True)


class Posts(db.Model):
    SNO = db.Column(db.Integer, primary_key=True)
    TITLE = db.Column(db.String, nullable=False)
    SLUG = db.Column(db.String, nullable=False)
    CONTENT = db.Column(db.String, unique=True)
    tagline = db.Column(db.String, unique=False)
    POSTED_BY = db.Column(db.String, unique=False)
    POSTED_ON = db.Column(db.DATE, unique=False)


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    post = Posts.query.all()
    return render_template('dashboard.html', params=params, posts=post)

    if request.method == 'POST':
        user_name = request.form.get("email")
        password = request.form.get("password")
        if user_name == 'qwert@qwerty.com' and password == 'qwerty':
            session['user'] = user_name
            post = Posts.query.all()
            return render_template('dashboard.html', params=params, posts=post)

    return render_template('signin.html', params=params)


@app.route('/')
def home():
    post = Posts.query.filter_by().all()
    last = math.floor(len(post) / int(params['no_of_posts']))
    prev = ''
    next = ''
    # [0: params['no_of_posts']]
    page = request.args.get('number')
    if page is not None:
        page = int(page)
    if not str(page).isnumeric():
        page = 0

    post = post[page * int(params['no_of_posts']): page * int(params['no_of_posts']) + int(params['no_of_posts'])]
    if page == 1 and page != last:
        prev = '#'
        next = '/?number=' + str(page + 1)
    elif page == last:
        next = '#'
        prev = '/?number=' + str(page - 1)
    elif page > 1:
        next = '/?number=' + str(page + 1)
        prev = '/?number=' + str(page - 1)
    else:
        page = ''
        prev = '#'
        next = '/?number=' + str(page + 1)


    return render_template('index.html', params=params, posts=post, prev=prev, next=next)


@app.route('/about')
def about():
    return render_template('about.html', params=params)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        uploader = request.files['uploader']
        filename = secure_filename(uploader.filename)
        uploader.save(os.path.join(app.config['UPLOADER'], filename))
        return 'File uploaded successfully'


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('user')
    return redirect('/dashboard')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        contact_no = request.form.get('contact')
        message = request.form.get('message')
        entry = Contacts(FIRST_NAME=first_name, LAST_NAME=last_name, EMAIL=email, CONTACT_NO=contact_no,
                         MESSAGE=message)
        db.session.add(entry)
        db.session.commit()
    return render_template('contact.html', params=params)


@app.route('/post/<string:post_slug>', methods=['GET'])
def post_route(post_slug):
    post = Posts.query.filter_by(SLUG=post_slug).first()
    return render_template('post.html', params=params, post=post)


@app.route('/edit/<string:sno>', methods=['GET', 'POST'])
def edit(sno):
    if request.method == 'POST':
        title = request.form.get('title')
        slug = request.form.get('slug')
        content = request.form.get('content')
        tag_line = request.form.get('tag_line')
        posted_by = request.form.get('posted_by')
        posted_on = datetime.now()
        if sno == '0':
            post = Posts(TITLE=title, SLUG=slug, CONTENT=content, tagline=tag_line, POSTED_BY=posted_by,
                         POSTED_ON=posted_on)
            db.session.add(post)
            db.session.commit()
        else:
            post = Posts.query.filter_by(SNO=sno).first()
            post.TITLE = title
            post.SLUG = slug
            post.CONTENT = content
            post.tagline = tag_line
            post.POSTED_BY = posted_by
            post.POSTED_ON = posted_on
            db.session.commit()
            return redirect('/edit/' + sno)
    post = Posts.query.filter_by(SNO=sno).first()
    return render_template('edit.html', params=params, post=post)


@app.route('/delete/<string:sno>', methods=['GET', 'POST'])
def delete(sno):
    post = Posts.query.filter_by(SNO=sno).first()
    db.session.delete(post)
    db.session.commit()
    return redirect('/dashboard')


if __name__ == '__main__':
    app.run()
