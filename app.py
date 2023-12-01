from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from PIL import Image
import os
import secrets
from flask import jsonify
from flask_cors import CORS


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://new_user:password@94.228.123.59/thefoxxstuff2'
app.config['UPLOAD_FOLDER'] = 'uploads'
db = SQLAlchemy(app)
CORS(app)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    image = db.Column(db.String(100), nullable=False)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_random_filename():
    # Generate a random filename with exactly 6 characters
    characters = "abcdefghijklmnopqrstuvwxyz0123456789"
    random_string = ''.join(secrets.choice(characters) for i in range(6))
    return random_string

def save_thumbnail(image_path, thumbnail_path):
    # Open the image using Pillow
    image = Image.open(image_path)

    # Resize the image to create a thumbnail
    thumbnail_size = (800, 800)  # Adjust the size as needed
    image.thumbnail(thumbnail_size)

    # Convert and save the thumbnail in WebP format
    image.convert("RGB").save(thumbnail_path, "WEBP")

@app.route('/')
def index():
    posts = Post.query.all()
    return render_template('index.html', posts=posts)

@app.route('/add_post', methods=['GET', 'POST'])
def add_post():
    if request.method == 'POST':
        title = request.form['title']

        if 'image' not in request.files:
            return redirect(request.url)

        image = request.files['image']

        if image.filename == '':
            return redirect(request.url)

        if image and allowed_file(image.filename):
            # Generate a random filename
            random_filename = generate_random_filename()
            original_filename = secure_filename(random_filename + ".jpg")
            thumbnail_filename = secure_filename(random_filename + "_thumb.webp")

            # Save the original image
            original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
            image.save(original_path)

            # Save the thumbnail
            thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
            save_thumbnail(original_path, thumbnail_path)

            new_post = Post(title=title, image=original_filename)
            db.session.add(new_post)
            db.session.commit()

            return redirect(url_for('index'))

    return render_template('add_post.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/thumbnails/<filename>')
def thumbnail_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    post = Post.query.get(id)

    if request.method == 'POST':
        post.title = request.form['title']

        # Handle image update
        if 'image' in request.files:
            image = request.files['image']
            if image.filename != '' and allowed_file(image.filename):
                # Delete the old image and thumbnail files
                old_image_path = os.path.join(app.config['UPLOAD_FOLDER'], post.image)
                old_thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], post.image.split(".")[0] + "_thumb.webp")
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)
                if os.path.exists(old_thumbnail_path):
                    os.remove(old_thumbnail_path)

                # Generate new filenames
                random_filename = generate_random_filename()
                original_filename = secure_filename(random_filename + ".jpg")
                thumbnail_filename = secure_filename(random_filename + "_thumb.webp")

                # Save the new original image
                original_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
                image.save(original_path)

                # Save the new thumbnail
                thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], thumbnail_filename)
                save_thumbnail(original_path, thumbnail_path)

                post.image = original_filename

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit_post.html', post=post)

@app.route('/delete_post/<int:id>')
def delete_post(id):
    post = Post.query.get(id)

    # Delete the associated image and thumbnail files
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], post.image)
    thumbnail_path = os.path.join(app.config['UPLOAD_FOLDER'], post.image.split(".")[0] + "_thumb.webp")

    if os.path.exists(image_path):
        os.remove(image_path)
    if os.path.exists(thumbnail_path):
        os.remove(thumbnail_path)

    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('index'))

@app.template_filter('basename')
def basename(value):
    return os.path.basename(value)

@app.route('/api/posts')
def get_posts():
    posts = Post.query.all()
    post_list = [
        {'id': post.id, 'title': post.title, 'image': post.image}
        for post in posts
    ]
    return jsonify({'posts': post_list})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0')
