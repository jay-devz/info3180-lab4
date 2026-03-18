import os
from app import app, db, login_manager
from flask import render_template, request, redirect, url_for, flash, session, abort
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.utils import secure_filename
from app.models import UserProfile
from app.forms import LoginForm
from werkzeug.security import check_password_hash
from app.forms import UploadForm, LoginForm
from flask import send_from_directory


###
# Routing for your application.
###

@app.route('/')
def home():
    """Render website's home page."""
    return render_template('home.html')


@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html', name="Mary Jane")


@app.route('/upload', methods=['POST', 'GET'])
@login_required
def upload():
    form = UploadForm()

    if form.validate_on_submit():
        file = form.image.data
        filename = secure_filename(file.filename)
        
        # 1. Use app.root_path to get the directory where your 'app' folder is
        # 2. Go UP one level (..) to find the 'uploads' folder in the project root
        upload_path = os.path.join(app.root_path, '..', app.config['UPLOAD_FOLDER'], filename)

        file.save(upload_path)

        flash('File Saved', 'success')
        return redirect(url_for('home')) 

    # If it's a GET request or validation fails, show errors
    flash_errors(form)
    return render_template('upload.html', form=form)

@app.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()

    # 1. Change the if statement to validate the entire form
    if form.validate_on_submit():
        # 2. Get the username and password values from the form
        username = form.username.data
        password = form.password.data

        # 3. Query database for a user based on the username submitted
        user = db.session.execute(db.select(UserProfile).filter_by(username=username)).scalar()

        # 4. Compare the password hash
        if user is not None and check_password_hash(user.password, password):
            # 5. Gets user id, load into session
            login_user(user)

            # 6. Flash a success message
            flash('You have successfully logged in!', 'success')

            # 7. Redirect to the upload form
            return redirect(url_for("upload"))
        else:
            flash('Invalid username or password', 'danger')
            
    return render_template("login.html", form=form)

# user_loader callback. This callback is used to reload the user object from
# the user ID stored in the session
@login_manager.user_loader
def load_user(id):
    return db.session.execute(db.select(UserProfile).filter_by(id=id)).scalar()

###
# The functions below should be applicable to all Flask apps.
###

# Flash errors from the form if validation fails
def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
), 'danger')

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also to cache the rendered page for 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404

def get_uploaded_images(): #step 1: Helper function to list filenamesdm
    """Helper function to get uploaded images."""
    rootdir = os.getcwd()
    upload_path = os.path.join(rootdir, app.config['UPLOAD_FOLDER'])
    images = []
    for subdir, dirs, files in os.walk(upload_path):
        for file in files:
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                images.append(file)
    return images

# Step 2: Route to serve a specific image file from the folder
@app.route('/uploads/<filename>')
def get_image(filename):
    return send_from_directory(os.path.join(os.getcwd(), app.config['UPLOAD_FOLDER']), filename)

# Step 3 & 6: Route to display the gallery (protected by login)
@app.route('/files')
@login_required
def files():
    image_list = get_uploaded_images()
    return render_template('files.html', images=image_list)

@app.route('/logout')
@login_required
def logout():
    # 1. Use Flask-Login's logout_user method
    logout_user()
    
    # 2. Flash a message and redirect to home
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))