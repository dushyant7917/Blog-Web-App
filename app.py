from flask import Flask, render_template, url_for, request, session, redirect, flash, Markup
from flask.ext.pymongo import PyMongo
import bcrypt
import re
import time

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'blog'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/blog'


mongo = PyMongo(app)


@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('blog'))

    return render_template('index.html')


@app.route('/blog', methods = ['GET', 'POST'])
def blog():
    if request.method == 'GET':
        if 'username' in session:
            articles = mongo.db.articles
            content = articles.find()
            return render_template('blog.html', content = content)

        return render_template('login.html')

    else:
        comments = mongo.db.comments
        #comments.insert({'_id':,'number': })
        return "dff"



@app.route('/comment/<string:artcl>')
def comment(artcl):
    if 'username' in session:
        print artcl['author']
        return render_template('comment.html', item = artcl)

    return render_template('login.html')



@app.route('/profile')
def profile():
    if 'username' in session:
        users = mongo.db.users
        details = users.find_one({'username': session['username']})
        return render_template('profile.html', details = details)

    return render_template('login.html')


@app.route('/editProfile', methods=['GET', 'POST'])
def editProfile():
    if request.method == "GET":
        if 'username' in session:
            users = mongo.db.users
            details = users.find_one({'username': session['username']})
            return render_template('editProfile.html', details = details)

        return render_template('login.html')

    else:
        name = request.form['name']
        age = request.form['age']
        profession = request.form['profession']
        pic = request.form['pic']
        users = mongo.db.users
        users.update({'username': session['username']}, {'$set': {'name': name, 'age': age, 'profession': profession, 'pic': pic}})
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
            artTitle = request.form['title']
            artPic = request.form['art_pic']
            date = time.strftime("%B %d,"+" %Y")
            articles.insert({ 'author': session['username'], 'article': art , 'title': artTitle , 'date': date, 'pic': artPic})
            return redirect(url_for('blog'))

    else:
        return redirect(url_for('login'))


@app.route('/home')
def home():
    return redirect(url_for('index'))


@app.route("/logout")
def logout():
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
        return render_template('login.html')

    else:
        return render_template('login.html')



@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'username': request.form['username']})

        print ("entered username : " + str(request.form['username']))

        if existing_user is None:
            hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
            users.insert({ 'username': request.form['username'], 'password': hashpass, 'pic': '/static/defaultProfilePic.png'})

            print ("New Username : " + str(request.form['username']))

            return redirect(url_for('index'))

        message = Markup("This username is already registered!")
        flash(message)

        print "Wrong!"

        return render_template('register.html')

    return render_template('register.html')


if __name__ == '__main__':
    app.secret_key = 'dushyant7917'
    app.run(debug=True)
