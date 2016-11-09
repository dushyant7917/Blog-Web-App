from flask import Flask, render_template, url_for, request, session, redirect, flash, Markup
from flask.ext.pymongo import PyMongo
import bcrypt
import re

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'blog'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/blog'

mongo = PyMongo(app)


@app.route('/')
def index():
    if 'username' in session:
        return render_template('blog.html')

    return render_template('index.html')


@app.route('/blog')
def blog():
    if 'username' in session:
        articles = mongo.db.articles
        content = articles.find({'author': session['username']})
        return render_template('blog.html', content = content)

    return render_template('login.html')


@app.route('/profile')
def profile():
    if 'username' in session:
        users = mongo.db.users
        details = users.find_one({'username': session['username']})
        print details['username']
        return render_template('profile.html', details = details)

    return render_template('login.html')


@app.route('/editProfile', methods=['GET', 'POST'])
def editProfile():
    if request.method == "GET":
        if 'username' in session:
            return render_template('editProfile.html')

        return render_template('login.html')

    else:
        username = request.form['username']
        name = request.form['name']
        age = request.form['age']
        profession = request.form['profession']
        users = mongo.db.users
        users.update({'_id': session['username']}, {'$set': {'name': name, 'username': username, 'age': age, 'profession': profession}})
        return redirect(url_for('profile'))



@app.route('/addBlog', methods = ['POST', 'GET'])
def addBlog():
    if 'username' in session:
        if request.method == 'GET':
            return render_template('addBlog.html')
        else:
            articles = mongo.db.articles
            art = re.sub('<p>', '', request.form['editor1'])
            art = re.sub('</p>', '', art)
            articles.insert({ 'author': session['username'], 'article': art })
            return redirect(url_for('blog'))

    else:
        return redirect(url_for('login'))


@app.route('/home')
def home():
    return redirect(url_for('index'))


@app.route("/logout")
def logout():
    #current_score = request.form['current_score']
    #current_level = request.form['current_level']
    #users = mongo.db.users
    #users.update({'_id': session['username']}, {'$set': {'score': current_score, 'level': current_level}})
    session.clear()
    return redirect(url_for('index'))


@app.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == "POST":
        users = mongo.db.users
        login_user = users.find_one({'username': request.form['username']})
        if login_user is not None:
            if bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password'].encode('utf-8')) == login_user['password'].encode('utf-8'):
                session['username'] = request.form['username']

                return redirect(url_for('index'))

        message = Markup("Invalid username or password!")
        flash(message)
        return render_template('wrong_login.html')

    else:
        return render_template('login.html')



@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'name': request.form['username']})


        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert({ '_id': request.form['username'], 'username': request.form['username'], 'password': hashpass })

            return redirect(url_for('index'))


        message = Markup("This username is already registered!")
        flash(message)
        return render_template('wrong_register.html')

    return render_template('register.html')


if __name__ == '__main__':
    app.secret_key = 'dushyant7917'
    app.run(debug=True)
