import os
from flask import Flask, render_template, url_for, request, session, redirect, flash, Markup
from flask.ext.pymongo import PyMongo
import bcrypt
import time
from bson.objectid import ObjectId
import hashlib
import pymongo
import re
from flask_mail import Mail, Message

#############################################
import smtplib
from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login("dushyant7917official@gmail.com", "password")

#############################################

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'blog'
app.config['MONGO_URI'] = 'online mongodb uri'
# Use below URI for local db
# app.config['MONGO_URI'] = 'mongodb://localhost:27017/blog'

mongo = PyMongo(app)

#############################################################
'''
app.config['MAIL_SERVER']='smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'dushyant7917official@gmail.com'
app.config['MAIL_PASSWORD'] = 'password'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)
'''
#############################################################

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('blog'))

    return render_template('index.html')


@app.route('/blog', methods = ['GET'])
def blog():
    if request.method == 'GET':
        articles = mongo.db.articles
        content = articles.find().sort([ ('date', pymongo.DESCENDING )])
        return render_template('blog.html', content = content)


@app.route('/search', methods = ['POST'])
def search():
    if request.method == 'POST':
        query = request.form['query']
        articles = mongo.db.articles
        results = articles.find({'$text': { '$search': query }}, { "score": { "$meta": "textScore" } }).sort([('score', {'$meta': 'textScore'})]).limit(9)
        count = articles.find({'$text': { '$search': query }}, { "score": { "$meta": "textScore" } }).sort([('score', {'$meta': 'textScore'})]).limit(9).count()
        return render_template("search.html", results = results, count = count, query = query)


@app.route('/search/<search_text>', methods = ['GET'])
def searchTag(search_text):
    if request.method == 'GET':
        articles = mongo.db.articles
        results = articles.find({'$text': { '$search': search_text }}, { "score": { "$meta": "textScore" } }).sort([('score', {'$meta': 'textScore'})]).limit(9)
        count = articles.find({'$text': { '$search': search_text }}, { "score": { "$meta": "textScore" } }).sort([('score', {'$meta': 'textScore'})]).limit(9).count()
        return render_template("search.html", results = results, count = count, query = search_text)


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
            comment_author = users.find_one({'username': session['username']})
            comments = mongo.db.comments
            comments.insert({'comment_id': art_id, 'comment': new_comment, 'comment_username': session['username'], 'date': date, 'pic': comment_author['pic']})
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
        other_posts = articles.find({'author': author['username']})
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
        tags = mongo.db.tags
        universal_tags = tags.find({})
        return render_template('article.html', item = item, author = author, comment_data = zip(lN,lC,lD,lP), UT = universal_tags, other_posts = other_posts)

    return render_template('login.html')


@app.route('/like/<article_id>', methods = ['GET'])
def like(article_id):
    if 'username' in session:
        if request.method == "GET":
            users = mongo.db.users
            likeID = users.find_one({'username': session['username']})
            if article_id not in likeID['liked_articles']:
                articles = mongo.db.articles
                item = articles.find_one({'_id': ObjectId(article_id)})
                likes = item['likes']
                users = mongo.db.users
                users.update({'username': session['username']}, {'$push': {'liked_articles': article_id}})
                articles.update({'_id': ObjectId(article_id)}, {'$set': {'likes': likes + 1}})
                return redirect(url_for('article', article_id = item['_id']))
            else:
                message = Markup("You can click it only once!")
                flash(message)
                articles = mongo.db.articles
                item = articles.find_one({'_id': ObjectId(article_id)})
                return redirect(url_for('article', article_id = item['_id']))


    else:
        return render_template('login.html')


@app.route('/profile')
def profile():
    if 'username' in session:
        users = mongo.db.users
        details = users.find_one({'username': session['username']})
        articles = mongo.db.articles
        blogs = articles.find({'author': session['username']}).sort([ ('date', pymongo.DESCENDING )])
        tt = []
        pc = []
        dt = []
        ai = []
        for i in blogs:
            tt.append(i['title'])
            dt.append(i['date'])
            pc.append(i['pic'])
            ai.append(i['_id'])
        return render_template('profile.html', details = details, blogs = zip(pc,tt,dt,ai))

    return render_template('login.html')


@app.route('/edit/<article_id>', methods = ['GET', 'POST'])
def editArticle(article_id):
    if 'username' in session:
        if request.method == 'GET':
            article = mongo.db.articles
            item = article.find_one({'_id': ObjectId(article_id)})
            return render_template('editArticle.html', item = item)
        else:
            articles = mongo.db.articles
            tag1 = request.form['tags']
            tag1 = tag1.split(";")
            uw = ['these','are','prefilled','tags','try','entering','one','of']
            art_tags = []
            for i in tag1:
                if i not in uw:
                    art_tags.append(i)
                else:
                    continue

            tags = mongo.db.tags
            for t in art_tags:
                if tags.find_one({'tag': t}) is None:
                    tags.insert({'tag': t})

            art = request.form['editor1']
            artTitle = request.form['title']
            artPic = request.form['art_pic']
            articles.update({'_id': ObjectId(article_id)}, {'$set': {'article': art , 'title': artTitle , 'pic': artPic, 'tags': art_tags}})
            return redirect(url_for('profile'))

    else:
        return redirect(url_for('login'))



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
            art_tags = []
            for i in tag1:
                if i not in uw:
                    art_tags.append(i)
                else:
                    continue

            art = request.form['editor1']
            artTitle = request.form['title']
            artPic = request.form['art_pic']
            date = time.strftime("%B %d,"+" %Y")
            tags = mongo.db.tags
            for t in art_tags:
                if tags.find_one({'tag': t}) is None:
                    tags.insert({'tag': t})

            articles.insert({ 'author': session['username'], 'article': art , 'title': artTitle , 'tags': art_tags, 'date': date, 'pic': artPic, 'likes': 0})
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
            if login_user['password'] == 'dushyant7917blogPASSWORD':
                message = Markup("Check your mail and verify your account!")
                flash(message)
                return render_template('login.html', colour = "red")

            elif bcrypt.hashpw(request.form['pass'].encode('utf-8'), login_user['password'].encode('utf-8')) == login_user['password'].encode('utf-8') and login_user['password'] is not 'dushyant7917blogPASSWORD':
                session['username'] = request.form['username']
                return redirect(url_for('index'))

            else:
                message = Markup("Invalid password!")
                flash(message)
                return render_template('login.html', colour = "red")

        else:
            message = Markup("Invalid username!")
            flash(message)
            return render_template('login.html', colour = "red")

    else:
        return render_template('login.html')


@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        users = mongo.db.users
        existing_user = users.find_one({'username': request.form['username']})
        email = request.form['email']

        if existing_user is None:
            if len(request.form['username']) > 3:
                if email:
                    hashpass = bcrypt.hashpw(request.form['pass'].encode('utf-8'), bcrypt.gensalt())
                    if request.form['pass'] == request.form['confirm_pass']:
                        token = hashpass.replace('/', '')
                        users.insert({ 'username': request.form['username'], 'password': 'dushyant7917blogPASSWORD', 'pic': '/static/defaultProfilePic.png', 'email': email, 'token': token, 'secret': hashpass, 'liked_articles': [] })

                        #################################
                        msg = MIMEMultipart('alternative')
                        msg['From'] = "dushyant7917official@gmail.com"
                        msg['To'] = email
                        msg['Subject'] = "Confirm Account!"

                        html = """
                        <!DOCTYPE html>
                        <html >
                          <head>
                            <meta charset="UTF-8">
                          </head>

                          <body>

                            <html>

                          <head>
                            <title>dushyant7917blog - Confirm your account!</title>
                            <style>
                              @font-face {
                                  	font-family: 'Avenir';
                                  	src: url('../fonts/avenirltstd-heavy-webfont.eot');
                                  	src: url('../fonts/avenirltstd-heavy-webfont.eot?#iefix') format('embedded-opentype'),
                                      	 url('../fonts/avenirltstd-heavy-webfont.woff2') format('woff2'),
                                      	 url('../fonts/avenirltstd-heavy-webfont.woff') format('woff'),
                                      	 url('../fonts/avenirltstd-heavy-webfont.ttf') format('truetype'),
                                      	 url('../fonts/avenirltstd-heavy-webfont.svg#webfontregular') format('svg');
                                  	font-weight: bold;
                                  	font-style: normal;
                              	}

                              	@font-face {
                                  	font-family: 'Avenir';
                                  	src: url('../fonts/avenirltstd-medium-webfont.eot');
                                  	src: url('../fonts/avenirltstd-medium-webfont.eot?#iefix') format('embedded-opentype'),
                                      	url('../fonts/avenirltstd-medium-webfont.woff2') format('woff2'),
                                 	     	url('../fonts/avenirltstd-medium-webfont.woff') format('woff'),
                                       	url('../fonts/avenirltstd-medium-webfont.ttf') format('truetype'),
                                  	    url('../fonts/avenirltstd-medium-webfont.svg#webfontregular') format('svg');
                                  	font-weight: normal;
                                  	font-style: normal;

                              	}

                              	@font-face {
                                 	font-family: 'Avenir';
                              	    src: url('../fonts/avenirltstd-light-webfont.eot');
                              	    src: url('../fonts/avenirltstd-light-webfont.eot?#iefix') format('embedded-opentype'),
                              	         url('../fonts/avenirltstd-light-webfont.woff2') format('woff2'),
                              	         url('../fonts/avenirltstd-light-webfont.woff') format('woff'),
                              	         url('../fonts/avenirltstd-light-webfont.ttf') format('truetype'),
                              	         url('../fonts/avenirltstd-light-webfont.svg#webfontregular') format('svg');
                              	    font-weight: 100;
                              	    font-style: normal;
                              	}
                              	body{
                              		background: #ffffff;
                              		margin: 0px;
                              		text-align: center;
                              		font-family: 'Avenir', 'Open Sans', Arial, sans-serif;
                              	}
                              	.head{
                              		background: #488dfb;
                              		color: #ffffff;
                              	}

                              	.head h1{
                              		font-size: 50px;
                              		font-weight: normal;
                              		line-height: 100px;
                              		margin-top: 100px;
                              	}

                              	.button{
                              		background: #39ce00;
                              		color: #ffffff;
                              		line-height: 50px;
                              		text-decoration: none;
                              		text-align: center;
                              		margin-top: 50px;
                              		margin-bottom: 50px;
                              	}

                              	.button a{
                              		color: #ffffff;
                              		text-decoration: none;
                              	}
                              	a{ color: #fff; }
                              	p a{ color: #565656; }
                              	.black a{ color: #000; }
                            </style>
                            <link href='https://fonts.googleapis.com/css?family=Open+Sans' rel='stylesheet'
                            type='text/css'>
                          </head>

                          <body bgcolor="#ffffff">
                            <table bgcolor="#efefef" cellpadding="0" cellspacing="0" border-collapse="collapse"
                            width="100%">
                              <tr>
                                <td align="center" style="padding: 30px;">
                                  <table bgcolor="#efefef" cellpadding="0" cellspacing="0" border-collapse="collapse"
                                  width="700px">
                                    <tr>
                                      <td align="center">
                                        <table cellpadding="0" cellspacing="0" border="0" border-collapse="collapse" width="100%">
                                          <tr>
                                            <td>&nbsp;</td>
                                          </tr>
                                          <tr>
                                            <td>&nbsp;</td>
                                          </tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" border="0" border-collapse="collapse" width="100%">
                                          <tr>
                                            <td>&nbsp;</td>
                                          </tr>
                                          <tr>
                                            <td>&nbsp;</td>
                                          </tr>
                                        </table>

                                        <table bgcolor="#488dfb" class="head" style="background: #488dfb;" cellpadding="0"
                                        cellspacing="0" border="0" border-collapse="collapse" width="100%">
                                          <tr>
                                            <td style="text-align: center;" colspan="3">
                                              	<h1>Account Confirmation</h1>
                                            </td>
                                          </tr>
                                          <tr>
                                            <td colspan="3" style="padding: 0px 80px; font-size: 20px; text-align: center;">Hi {0}! Welcome to dushyant7917blog, please confirm your email address to get started.</td>
                                          </tr>
                                          <tr>
                                            <td width="30%">&nbsp;</td>
                                            <td style="text-align: center;" width="40%">
                                              <a href="http://dushyant7917blog.herokuapp.com/verification/{1}/{2}" style="font-size: 20px; text-decoration:none">
                                              <table cellpadding="0" cellspacing="0" border-collapse="collapse" class="button"
                                              width="100%">
                                                <tr>
                                                  <td><b>Confirm your email</b></td>
                                                </tr>
                                              </table>
                                              </a>
                                            </td>
                                            <td width="30%">&nbsp;</td>
                                          </tr>
                                          <tr>
                                            <td>&nbsp;</td>
                                          </tr>
                                          <tr>
                                            <td>&nbsp;</td>
                                          </tr>
                                          <tr>
                                            <td>&nbsp;</td>
                                          </tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" border="0" border-collapse="collapse" width="100%">
                                          <tr>
                                            <td>&nbsp;</td>
                                          </tr>
                                          <tr>
                                            <td>&nbsp;</td>
                                          </tr>
                                        </table>
                                        <table cellpadding="0" cellspacing="0" border="0" border-collapse="collapse" width="100%">
                                          <tr>
                                            <td>&nbsp;</td>
                                          </tr>
                                          <tr>
                                            <td>&nbsp;</td>
                                          </tr>
                                        </table>

                                      </td>
                                    </tr>
                                  </table>
                                </td>
                                <td>&nbsp;</td>
                              </tr>
                              <tr>
                                <td>&nbsp;</td>
                              </tr>
                            </table>

                            </body>

                        </html>


                          </body>
                        </html>
                        """.replace("{", "{{").replace("}", "}}").format(request.form['username'], token)

                        msg.attach(MIMEText(html, 'html'))
                        text = msg.as_string()
                        server.sendmail("dushyant7917official@gmail.com", email, text)

                        #################################
                        '''
                        msg = Message('Confirm your account!', sender = 'dushyant7917official@gmail.com', recipients = [email])
                        msg.html = render_template("email.html", username = request.form['username'], token = token)
                        mail.send(msg)
                        '''
                        #################################

                        message = Markup("Check your mail to verify your account!")
                        flash(message)
                        return render_template('login.html', colour = "black")

                    else:
                        message = Markup("Type same password in both fields!")
                        flash(message)
                        return render_template('register.html', colour = "red")

                else:
                    message = Markup("Please enter a valid email ID!")
                    flash(message)
                    return render_template('register.html', colour = "red")

            else:
                message = Markup("Username should be atleast 4 charachter long!")
                flash(message)
                return render_template('register.html', colour = "red")


        message = Markup("This username is already registered!")
        flash(message)
        return render_template('register.html', colour = "red")

    return render_template('register.html')


@app.route('/verification/<username>/<token>')
def verify(username, token):
    users = mongo.db.users
    validID = users.find_one({'username': username})
    if validID is None:
        return "Invalid attempt to verify account!"
    elif validID and validID['token'] == token:
        users.update({'username': username}, {'$set': {'password': validID['secret']}})
        message = Markup("Registration Successful!")
        flash(message)
        return render_template('login.html', colour = "black")
    else:
        return "Invalid attempt to verify account!"


if __name__ == '__main__':
    app.secret_key = 'dushyant7917'
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug = True)
