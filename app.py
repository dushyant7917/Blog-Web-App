import os
from flask import Flask, render_template, url_for, request, session, redirect, flash, Markup
from flask.ext.pymongo import PyMongo
import bcrypt
import time
from bson.objectid import ObjectId
import hashlib

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'blog'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/blog'  # for local db

mongo = PyMongo(app)

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('blog'))

    return render_template('index.html')


@app.route('/blog', methods = ['GET'])
def blog():
    if request.method == 'GET':
        if 'username' in session:
            articles = mongo.db.articles
            content = articles.find()
            return render_template('blog.html', content = content)

        return render_template('login.html')


@app.route('/beta')
def beta():
    return render_template('beta.html')


@app.route('/comment/<article_id>', methods = ['POST'])
def comment(article_id):
    if request.method == 'POST':
        if 'username' in session:
            new_comment = request.form['comment']

            articles = mongo.db.articles
            item = articles.find_one({'_id': ObjectId(article_id)})
            hash_str = item['date'] + item['author'] + item['title']
            art_id = hashlib.md5(hash_str).hexdigest()
            date = time.strftime("%B %d,"+" %Y")
            users = mongo.db.users
            author = users.find_one({'username': item['author']})
            comments = mongo.db.comments
            comments.insert({'comment_id': art_id, 'comment': new_comment, 'comment_username': session['username'], 'date': date, 'pic': author['pic']})
            #articles = mongo.db.articles

            return redirect(url_for('article', article_id = article_id))

        else:
            render_template('login.html')

    else:
        return render_template('login.html')


@app.route('/article/<article_id>')
def article(article_id):
    if 'username' in session:
        articles = mongo.db.articles
        item = articles.find_one({'_id': ObjectId(article_id)})
        hash_str = item['date'] + item['author'] + item['title']
        art_id = hashlib.md5(hash_str).hexdigest()
        users = mongo.db.users
        author = users.find_one({'username': item['author']})
        comments = mongo.db.comments
        comment_data = comments.find({'comment_id': art_id})
        lC = []
        lN = []
        lD = []
        lP = []
        for i in comment_data:
            lP.append(i['pic'])
            lD.append(i['date'])
            lC.append(i['comment'])
            lN.append(i['comment_username'])
        return render_template('article.html', item = item, author = author, comment_data = zip(lN,lC,lD,lP))

    return render_template('login.html')



@app.route('/like/<article_id>', methods = ['GET'])
def like(article_id):
    if request.method == "GET":
        articles = mongo.db.articles
        item = articles.find_one({'_id': ObjectId(article_id)})
        likes = item['likes']
        articles.update({'_id': ObjectId(article_id)}, {'$set': {'likes': likes + 1}})
        return redirect(url_for('article', article_id = item['_id']))

    else:
        return "Error!"


@app.route('/profile')
def profile():
    if 'username' in session:
        users = mongo.db.users
        details = users.find_one({'username': session['username']})
        articles = mongo.db.articles
        blogs = articles.find({'author': session['username']})
        tt = []
        pc = []
        dt = []
        smmry = []
        for i in blogs:
            tt.append(i['title'])
            dt.append(i['date'])
            pc.append(i['pic'])
        return render_template('profile.html', details = details, blogs = zip(pc,tt,dt))

    return render_template('login.html')


@app.route('/editProfile/<username>', methods=['GET', 'POST'])
def editProfile(username):
    if request.method == "GET":
        if 'username' in session:
            users = mongo.db.users
            details = users.find_one({'username': username})
            return render_template('editProfile.html', details = details)

        return render_template('login.html')

    else:
        name = request.form['name']
        about = request.form['about']
        dob = request.form['dob']
        profession = request.form['profession']
        pic = request.form['pic']
        users = mongo.db.users
        users.update({'username': session['username']}, {'$set': {'name': name, 'about': about, 'dob': dob, 'profession': profession, 'pic': pic}})
        return redirect(url_for('profile'))




@app.route('/addBlog', methods = ['POST', 'GET'])
def addBlog():
    if 'username' in session:
        if request.method == 'GET':
            return render_template('addBlog.html')
        else:
            articles = mongo.db.articles
            tag1 = request.form['tags']
            tag1 = tag1.split(";")
            uw = ['these','are','prefilled','tags','try','entering','one','of']
            tags = []
            for i in tag1:
                if i not in uw:
                    tags.append(i)
                else:
                    continue

            art = request.form['editor1']
            artTitle = request.form['title']
            artPic = request.form['art_pic']
            date = time.strftime("%B %d,"+" %Y")
            articles.insert({ 'author': session['username'], 'article': art , 'title': artTitle , 'date': date, 'pic': artPic, 'tags': tags, 'likes': 0})
            return redirect(url_for('blog'))

    else:
        return redirect(url_for('login'))


@app.route('/home')
def home():
    return redirect(url_for('index'))


@app.route("/logout")
def logout():
    session.pop('username', None)
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

            message = Markup("Registration Successful! You can login now.")
            flash(message)
            return redirect(url_for('login'))

        message = Markup("This username is already registered!")
        flash(message)

        print "Wrong!"

        return render_template('register.html')

    return render_template('register.html')


if __name__ == '__main__':
    app.secret_key = 'dushyant7917'
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug = True)
