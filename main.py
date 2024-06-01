import math
from datetime import datetime

from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy

import json


with open('config.json','r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)
# set the secret key!
app.secret_key = 'super-secret-key'

local_server = True
if(local_server):
    app.config["SQLALCHEMY_DATABASE_URI"] = params['local_uri']
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = params['prod_uri']

# configure the SQLite database, relative to the app instance folder

db = SQLAlchemy(app)

#creating the Contacts model class
class Contacts(db.Model):
    '''
    sno, name phone_num, msg, date, email
    '''
    sno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    phone_no = db.Column(db.String(12), nullable=False)
    msg = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)

#creating the Posts Model class
class Posts(db.Model):
    '''
    sno, name phone_num, msg, date, email
    '''
    sno = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(80), nullable=False)
    content = db.Column(db.String(200), nullable=False)
    date = db.Column(db.String(12), nullable=True)
    slug = db.Column(db.String(20), nullable=False)
    img_file = db.Column(db.String(20), nullable=False)
    tagline = db.Column(db.String(80), nullable=False)

#creating the Users model class
class Users(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(50), nullable = False)
    date = db.Column(db.String(12), nullable=True)


@app.route("/")
def home():
    # fetch all the posts
    posts = Posts.query.filter_by().all()

    # total no of page
    total_no_of_page = math.ceil(len(posts) / int(params['no_of_posts_per_page']))
    last_page = total_no_of_page

    # return which page user is
    current_page_no = request.args.get('page')
    print(current_page_no)

    # if current page is not numeric
    if (not str(current_page_no).isnumeric()):
        current_page_no = 1

    # typecast to int
    current_page_no = int(current_page_no)

    # List slicing to assign unique post for every page
    j = (current_page_no - 1) * int(params['no_of_posts_per_page'])
    posts = posts[j:j + 2]
    #print(posts[0].title)
    #print(posts[1].title)

    #if this is the first page
    if current_page_no == 1:
        prev = "#"
        next = "/?page=" + str(current_page_no + 1)

     #if this is the last page
    elif current_page_no == last_page:
        prev = "/?page=" + str(current_page_no - 1)
        next = "#"

    # if it is the middle or in between first and last
    else:
        prev = "/?page=" + str(current_page_no - 1)
        next = "/?page=" + str(current_page_no + 1)

    return render_template('index.html', params=params, posts=posts, prev=prev, next=next)

@app.route("/about")
def about():
    return render_template('about.html',params=params)

@app.route("/contact", methods = ['GET','POST'])
def contact():
    if(request.method == 'POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        message = request.form.get('message')
        entry = Contacts(name=name, email=email, phone_no=phone, msg=message, date=datetime.now() )
        db.session.add(entry)
        db.session.commit()

    return render_template('contact.html', params=params)

@app.route("/post/<string:post_slug>", methods=['GET'])
def post(post_slug):

    #extracting post where slug = post_slug
    post = Posts.query.filter_by(slug=post_slug).first()

    #returning to post.html with params and post
    return render_template('post.html', params=params, post=post)

@app.route("/allposts/")
def allposts():
    #fetch all the posts
    posts = Posts.query.filter_by().all()
    return render_template('allposts.html', params=params, posts=posts)

@app.route("/dashboard", methods= ['GET','POST'])
def dashboard():
    # if user is already login
    if "user" in session:
        # fetching all the posts
        posts = Posts.query.all();
        return render_template("dashboard.html", params=params, posts=posts)

    # Redirect to login page
    else:
        return redirect("/login")

@app.route("/edit/<string:sno>" , methods=['GET', 'POST'])
def edit(sno):
    if "user" in session:
        if request.method == "POST":
            title = request.form.get('title')
            tline = request.form.get('tline')
            slug = request.form.get('slug')
            content = request.form.get('content')
            img_file = request.form.get('img_file')
            date = datetime.now()

            # adding new post
            if int(sno) == 0:
                #add a new record to the database
                post = Posts(title=title, slug=slug, content=content, tagline=tline, img_file=img_file, date=date)
                db.session.add(post)
                db.session.commit()

                # return to dashboard page
                return redirect("/dashboard")

            # Existing post
            else:
                # retrieve the post from DB with sno
                post = Posts.query.filter_by(sno=sno).first()
                post.title = request.form.get('title')
                post.tagline = request.form.get('tline')
                post.slug = request.form.get('slug')
                post.content = request.form.get('content')
                post.img_file = request.form.get('img_file')
                post.date = datetime.now()

                #update the post in db
                db.session.commit()

                # return to dashboard page
                return redirect("/dashboard")

        # when no POST req is send then retrieve that post using sno to show the data in the form
        post = Posts.query.filter_by(sno=sno).first()
        return render_template('edit.html', params=params, sno=sno, post=post)

@app.route("/delete/<string:sno>")
def delete(sno):
    #fetch the post by sno
    post = Posts.query.filter_by(sno=sno).first()
    #delete the post
    db.session.delete(post)
    db.session.commit()

    return redirect("/dashboard")


@app.route("/login", methods=['GET', 'POST'])
def login():
    # if user is not logged in
    if request.method == 'POST':
        username = request.form.get("uname")
        userpass = request.form.get("upass")

        # check if user is registered or not
        user = Users.query.filter_by(email=username).first()
        #print(user)
        #print(user.password)
        # if user is already registered
        if user is not None:
            # check if both password is matching
            if ((user.password) == userpass):
                # set the session variable
                session['user'] = username
                # return to home page
                return redirect("/")
            else:
                print("Password is incorrect")
                return render_template("login.html", error=True, flag="incorrect_password")
        else:
            print("User is not registered")
            return render_template("login.html", error=True, flag="not_registered")

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/register", methods=['GET', 'POST'])
def registration():
    if (request.method == 'POST'):
        '''Add entry to the database'''
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('psw')
        confirm_password = request.form.get('pass')
        date = datetime.now()

        user = Users.query.filter_by(email=email).first()

        # check if user is already exists
        if user is not None:
            return render_template("registration.html", params=params, error=True, flag = "already_have_account0")
        # else add the user in the database
        else:
            # check if password and confirm password is same then only add the user
            if password == confirm_password:
                entry = Users(name=name, email=email, password=confirm_password, date=date)
                db.session.add(entry)
                db.session.commit()
                # redirect to login page
                return redirect("/login")
            else:
                return render_template("registration.html", params=params, error=True, flag="password_mismatch")

    return render_template("registration.html", params=params)

app.run(debug=True)