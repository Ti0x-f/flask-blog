from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_required, login_user, logout_user
from app.forms import LoginDashboardForm, NewPostForm, ContactForm
from app.models import User, Post
from app.email import send_email
from config import Config
from app import app, db

@app.route('/')
@app.route('/index')
def index(): #Render 5 posts on the index page, ordered by descendant timestamps
    posts = Post.query.order_by(Post.timestamp.desc()).limit(5)
    return render_template('index.html', title='Home', posts=posts)

@app.route('/post/<id>')
def post(id): #View for full post, since the blog and index view only display title + description
    post = Post.query.filter_by(id=id).first()
    return render_template('post.html', title=post.title, post=post)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginDashboardForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('admin'))
        login_user(user)
        return redirect(url_for('dashboard'))
    return render_template('login_dashboard.html', title='Dashboard Login', form=form)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    form = NewPostForm()
    if form.validate_on_submit(): #Adding new post
        new_post = Post(title=form.title.data, description=form.description.data,
            body=form.body.data)
        db.session.add(new_post)
        db.session.commit()
        flash("New post has been posted")
        return redirect(url_for('dashboard'))
    return render_template('dashboard.html', title='Dashboard', form=form)

@app.route('/all_posts')
@login_required
def all_posts(): #In dashboard, display all blog posts with pagination and update/delete options
    posts = Post.query.all()
    return render_template('all_posts.html', title='All posts', posts=posts)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/delete_post/<id>')
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()
    db.session.delete(post)
    db.session.commit()
    return redirect(url_for('all_posts'))

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        html_body = '<p>' + form.message.data + '</p>'
        send_email(form.subject.data, form.email.data, app.config['ADMINS'],
            form.message.data, html_body)
        flash('Your message has been sent.')
        return redirect(url_for('index'))
    return render_template('contact.html', title='Contact', form=form)
