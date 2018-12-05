#!/usr/bin/env python3

# Catalog Application: an application to display a catalog of items divided into categories.
# Authorized, authenticated users have the abilit to add, edit and delete categories and items to the catalog.
# users can login with through a third party login

# Created By: Fatima Alawami
# Creation date: 16-Nov-2018

from flask import Flask,render_template, jsonify,request, url_for,flash,redirect, make_response
from flask_bootstrap import Bootstrap
from flask import session as login_session
from sqlalchemy import create_engine, Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, load_only, sessionmaker
from catalogdb_setup import Base, Category, CategoryItem, User
from werkzeug import secure_filename
from datetime import datetime
from PIL import Image
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import os, random, string, httplib2, json,requests

UPLOAD_FOLDER = 'static/image'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
output_size = (300, 200)

app = Flask(__name__, static_url_path='/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

Bootstrap(app)

# client id for google login
CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Item Catalog Application"

# connect to the database
engine = create_engine('sqlite:///catalog.db',connect_args={'check_same_thread':False})
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)

session = DBSession()


#to check if the uploaded file is an image within the defined extensions
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/catalog/about')
def showAbout():
	return render_template('about.html')


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html',STATE=state)

def checkLogin():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None


#check if category name to be created or editted is unique
def uniqueCategory(Category_name):
    categories = session.query(Category).options(load_only(Category.name))
    for category in categories:
	    if Category_name.lower() == category.name.lower():
	       return False
    return True


#check if item title to be created or editted is unique
def uniqueItem(item_name):
    items = session.query(CategoryItem).options(load_only(CategoryItem.title))
    for item in items:
	    if item_name.lower() == item.title.lower():
	       return False
    return True


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    print login_session['access_token']

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

	# see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("You are now logged in as %s" % login_session['username'],'success')
    return output


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        # return response
        flash('You have logged off successfully','succcess')
        return redirect(url_for('showCatalog')) 
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON end point for the entire catalog catalog wise
@app.route('/catalog/JSON')
def catalogJSON():
    categories = session.query(Category).filter_by(status = 'A').all()
    if categories:
        # list to hold items
        catalog = []
        #prep data for json
        for category in categories:
            item_json = {
                 'name'         : category.name,
                 'image'        : category.image,
                 'id'           : category.id,
            }
            # comments / our embedded documents
            item_json['items'] = [] # list - will hold all comment dictionaries
            items = session.query(CategoryItem).filter_by(category_id = category.id ,status = 'A').all()
            # loop through idea comments
            for item in items:
                item_dict = {
                    'id'           : item.id,
                    'title'        : item.title,
                    'price'        : item.price,
                    'description'  : item.description,
                    'image'        : item.image
                }
                # ap
                item_json['items'].append(item_dict)
            # insert idea dictionary into public_ideas list
                catalog.append(item_json)
        # prepare dictionary for JSON return
                data = {
                'Category' : catalog
                }
        # jsonify (imported from Flask above)
        # will convert 'data' dictionary and set mime type to 'application/json'
        return jsonify(data)


# JSON end point for the a specific category
@app.route('/catalog/<string:category_name>/Category/JSON')
def categoryItemsJSON(category_name):
    category = session.query(Category).filter_by(name=category_name,status= 'A').one()
    items = session.query(CategoryItem).filter_by(
        status= 'A',category_id=category.id).all()
    return jsonify(CategoryItems=[i.serialize for i in items])


# JSON end point for the a specific item
@app.route('/catalog/<string:catgeory_name>/<string:item_name>/item/JSON')
def categoryItemJSON(catgeory_name, item_name):
    categoryItem = session.query(CategoryItem).filter_by(status= 'A',title=item_name).one()
    return jsonify(CategoryItem=categoryItem.serialize)

# main page of the application that display all the categories
@app.route('/')
@app.route('/catalog/')
def showCatalog():
    categories = session.query(Category).filter_by(status='A').all()
    return render_template('catalog.html',categories = categories)


# function to generate a random image name based on the datetime to avoid collesion
# it saves the image to the file system
def getFileName(file):
    randomname = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(12))
    ext = os.path.splitext(file.filename)[1]
    filename = secure_filename(randomname+ext)
    picture_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    i = Image.open(file)
    i.thumbnail(output_size)
    i.save(picture_path)
    return filename


# this function is for adding a new category to the catalog
@app.route('/catalog/new', methods=['GET','POST'])
def newCategory():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        #check if category name is inputted
        if request.form['name']:
            # check if categry exists
            if not uniqueCategory(request.form['name']):
                flash('Category already exists. Please Enter a unique name','info')
                return redirect(url_for('showCatalog'))
            #default image
            filename = 'default.jpg'
            # check if the post request has the file part, set default image
            #handle uploaded image, give it a unique name and save it to file system
            if 'file' in request.files:
                file = request.files['file']
                if allowed_file(request.files['file'].filename):
                    filename = getFileName(file)
                else: #for cases when upload file is not an image
                    flash('File extension is not supported. Only images are welcome :)', 'Info')
                    return redirect(url_for('showCatalog'))
            # store only the file name in the database
            newCategory = Category(name=request.form['name'], status = 'A', image = filename, user_id = login_session['user_id'])
            session.add(newCategory)
            session.commit()
            flash('Category was created successfully', 'success')
        else: # category name field is empty
            flash('Please enter the category name', 'danger')
        return redirect(url_for('showCatalog'))
    else: # GET request
        return render_template('newcategory.html', title='Add new Catgeory')


def removeFile(filename):
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
# check if a file exists on disk 
# if exists, delete it else show an error message
    if os.path.exists(image_path):
        try:
            os.remove(image_path)
            return True
        except OSError, e:
            flash ("Error: %s - %s." % (e.filename,e.strerror),'danger')
            return False
    else:  
        flash ("File was not found %s in system." % filename,'danger')
        return False


# this function is for modyfying existing category
@app.route('/catalog/<string:category_name>/edit', methods=['GET','POST'])
def editCategory(category_name):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    editted_category = session.query(Category).filter_by(name = category_name).one()
    if request.method == 'POST':
        # check if name provided is unique and issue a warning if it is not
        if request.form.get('name'):
            if request.form.get('name') != editted_category.name:
                if not uniqueCategory(request.form['name']):
                    flash('Category already exists. Please enter a new one', 'info')
                    return redirect(url_for('showCatalog'))
            editted_category.name = request.form['name']
        if 'file' in request.files:
            file = request.files['file']
            if allowed_file(request.files['file'].filename):
                # remove the current image from the file system if it is not the default image
                if editted_category.image != 'default.jpg':
                    removeFile(editted_category.image)
                filename = getFileName(file)
                editted_category.image = filename
            else: #for cases when upload file is not an image
                flash('File extension is not supported. Only images are welcome :)', 'info')
                return redirect(url_for('showCatalog'))
        session.add(editted_category)
        session.commit()
        flash('Category Successfully updated','success')
        return redirect(url_for('showCatalog'))
    else:
        return render_template('editCategory.html',category=editted_category)



# this function is for deleting existing category
@app.route('/catalog/<string:category_name>/delete',methods=['GET','POST'])
def deleteCategory(category_name):
    # return user to login page if not logged in. Deleting a category can only be done by authorized users
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))

    category_to_delete = session.query(Category).filter_by(name=category_name, status = 'A').one()
		#once form is submitted and the user logged in having the authority
		#deletion can be carried out
    if request.method == 'POST':
        # deletion is done by changing the status of the item record to X
        # it still won't show if category items are displayed but will still be in the database
        category_to_delete.status = 'X' 
        session.add(category_to_delete)
        session.commit()
        flash('Category was deleted successfuly','success')
        return redirect(url_for('showCatalog'))
    else:
		#before displaying the deleteCategory page we check if catgeory is empty or has items
		#and display the warning/confirmation message accordingly
		items = session.query(CategoryItem).filter_by(category_id=category_to_delete.id, status = 'A').all()
		if not items:
		    return render_template('deletecategory.html',category = category_to_delete)
		else:
		    flash('There are items in %s category. It cannot be deleted' %category_to_delete.name, 'danger')
		return redirect(url_for('showCatalog'))


# this function displays all items in a given category
@app.route('/catalog/<string:category_name>')
def showItems(category_name):
    category = session.query(Category).filter_by(name=category_name,status='A').one()
    items = session.query(CategoryItem).filter_by(category_id = category.id,status='A').all()
    if not items:
        flash('There are no items in this category yet.','info')
    return render_template('items.html',category_name= category_name, items = items)


# this function adds a new item to existing category
@app.route('/catalog/<string:category_name>/new', methods = ['GET','POST'])
def newItem(category_name):
    # return user to login page if not logged in. Deleting a category can only be done by authorized users
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))

    if request.method == 'POST':   
     #check if category name is inputted
	    if (request.form['title'] and request.form['price']): # check if the post request has the file part, set default image
		    if not uniqueItem(request.form['title']):
				flash('Item already exist. Please enter unique item name', 'info')
				return redirect(url_for('showItems',category_name=category_name))
		    filename = 'default.jpg'
		    if 'file' in request.files:
				file = request.files['file']
				if allowed_file(request.files['file'].filename):
				    filename = getFileName(file)
				else: #for cases when upload file is not an image
				    flash('File extension is not supported. Only images are welcome :)','info')
				    return redirect(url_for('showItems',category_name=category_name))
		    title = request.form['title']
		    price = request.form['price']
		    description = request.form['description']
		    category = session.query(Category).filter_by(name=category_name).one()
		    newItem = CategoryItem(title=title,category_id=category.id,description=description,price=price,status='A',image=filename, user_id = login_session['user_id'])
		    session.add(newItem)
		    session.commit()
		    flash('Item was created successfully','success')
	    else:
		    flash('Item title or price are missing','danger')
	    return redirect(url_for('showItems',category_name = category_name))
    else:
		return render_template('newitem.html',category_name = category_name)


# this function is for updating existing category item
@app.route('/catalog/<string:category_name>/<string:item_title>/edit',methods=['GET','POST'])
def editItem(category_name,item_title):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    editedItem = session.query(CategoryItem).filter_by(title=item_title,status='A').one()
    category = session.query(Category).filter_by(id= editedItem.category_id,status='A').one()
    categories = session.query(Category).filter_by(status='A').all()

    if request.method == 'POST':
        # if title is not empty and is different than the current one
        # check if it is unique and issue a warning if not
        if request.form['title']:
            if request.form.get('title') != editedItem.title:
                if not uniqueItem(request.form['title']):
				    flash('Item already exist. Please enter unique item name','info')
				    return redirect(url_for('showItems',category_name=category_name))
            editedItem.title = request.form['title']

        if request.form['description']:
            editedItem.description = request.form['description']
        if request.form['price']:
            editedItem.price = request.form['price']
        if 'file' in request.files:
            file = request.files['file']
            if allowed_file(request.files['file'].filename):
				filename = getFileName(file)
				editedItem.image = filename
            else: #for cases when upload file is not an image
				flash('File extension is not supported. Only images are welcome :)','info')
				return redirect(url_for('itemDetails',category_name=category.name,item_title=editedItem.title))
        if request.form['category']:
            editedItem.category_id = category.id
        session.add(editedItem)
        session.commit()
        flash('Item was Edited Successfully','success')
        return redirect(url_for('itemDetails',category_name=category.name,item_title=editedItem.title))
    else:
        return render_template('edititem.html',category_name=category.name,item=editedItem,categories=categories)


# this function is for deleting an item
@app.route('/catalog/<string:category_name>/<string:item_title>/delete',methods=['GET','POST'])
def deleteItem(category_name,item_title):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    item = session.query(CategoryItem).filter_by(title=item_title).one()
    if request.method == 'POST':
		item_to_delte = session.query(CategoryItem).filter_by(title=item_title).one()
		item_to_delte.status = 'X'
		session.add(item_to_delte)
		session.commit()
		flash('Item was deleted successfully.','success')
		return redirect(url_for('showItems',category_name=category_name))
    else:
		return render_template('deleteitem.html',category_name=category_name,item=item)


# this function displays the details of a given item
@app.route('/catalog/<string:category_name>/<string:item_title>/')
def itemDetails(category_name,item_title):
    item = session.query(CategoryItem).filter_by(title=item_title).one()
    category = session.query(Category).filter_by(id= item.category_id).one()
    return render_template('itemDetails.html',item=item, category_name= category.name)


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
