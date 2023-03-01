######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

from datetime import datetime
import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

# to hide passwords (added, not there by default. security may not be necessary)
import bcrypt

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!
with open('dbpassword.txt') as f: 
	p = f.read()
#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = p
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()


class User(flask_login.UserMixin):
	pass


@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user


@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email'].strip()
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if bcrypt.checkpw(flask.request.form['password'].encode(), pwd.encode()):
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"


@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')


@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')


#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')


@app.route("/register", methods=['POST'])
def register_user():
	try:
		first_name = request.form.get('first_name').strip()
		last_name = request.form.get('last_name').strip()
		email=request.form.get('email').strip()
		password=request.form.get('password').strip()
		hashed_pwd = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
		dob = request.form.get('date_of_birth')
		date_obj = datetime.strptime(dob, '%Y-%m-%d').date()
	except Exception as e:
		print(type(e).__name__)
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	with conn.cursor() as cursor: 
		test =  isEmailUnique(email)
		if test:
			query = "INSERT INTO Users (first_name, last_name, email, password, date_of_birth) VALUES (%s, %s, %s, %s, %s)"
			values = (first_name, last_name, email, hashed_pwd, date_obj)
			print(cursor.execute(query, values))
			conn.commit()
			#log user in
			user = User()
			user.id = email
			flask_login.login_user(user)
			return render_template('hello.html', name=email, message='Account Created!')
		else:
			print("couldn't find all tokens")
			return flask.redirect(flask.url_for('register'))


def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]


def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]


def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code


@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")


#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption) VALUES (%s, %s, %s )''', (photo_data, uid, caption))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code


#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


@app.route("/find-friends", methods=["GET", "POST"])
@flask_login.login_required
def find_friend(): 
	if request.method == "GET": 
		return render_template("find-friends.html")
	else: 
		fname = request.form.get('first_name').strip()
		lname = request.form.get('last_name').strip()
		with conn.cursor() as cursor: 
			query = f'SELECT first_name, last_name, email FROM Users WHERE \
		first_name=%s AND last_name=%s'
			values = (fname, lname)
			cursor.execute(query, values)
			conn.commit()
			users = cursor.fetchall()
			print(users)
			return render_template('find-friends.html', users=users)
		

@app.route("/add-friend", methods=["POST"])
@flask_login.login_required
def add_friend(): 
	with conn.cursor() as cursor: 
		# get friend_id
		query = "SELECT user_id FROM Users WHERE email=%s"
		values = (request.form['friend_email']) 
		cursor.execute(query, values)
		friend_id = cursor.fetchall()[0][0]

		# get user_id 
		user_email = flask_login.current_user.id 
		query = "SELECT user_id FROM Users WHERE email=%s"
		values = (user_email) 
		cursor.execute(query, values)
		user_id = cursor.fetchall()[0][0]

		values = (user_id, friend_id) # the values we will use from now on 

		# check if they are friends already 
		query = "SELECT * FROM Friends WHERE user_id = %s AND friend_id = %s"
		cursor.execute(query, values)
		already_friends = cursor.fetchone()
		if already_friends: 
			return render_template("hello.html", \
			  message="You are already friends with that person!")

		# insert into Friends table 
		query = "INSERT INTO Friends (user_id,friend_id) VALUES (%s,%s)"
		cursor.execute(query, values)
		conn.commit()

	return render_template('hello.html', message='Friend added!')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
