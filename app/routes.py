from flask import render_template, redirect, url_for, flash, request, make_response, Response
from flask_login import current_user, login_required, login_user, logout_user
from app.forms import LoginDashboardForm, NewPostForm, ContactForm, CommentForm, EditPostForm
from app.models import User, Post, Comment, Stats
from app.email import send_email
from datetime import date
from config import Config
from feedgen.feed import FeedGenerator
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from app import app, db

import io

@app.before_request #Update database for each new visit. Problem: takes in account my own visits
def before_request():
        visits = Stats.query.filter_by(day_visits = date.today()).first()
        if visits is None:
            new_day_visits = Stats()
            db.session.add(new_day_visits)
            db.session.commit()
        else:
            visits.visits += 1
            db.session.commit()
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = LoginDashboardForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.data.password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('register.html', form=form)
@app.route('/')
@app.route('/index')
def index(): #Render 5 posts on the index page, ordered by descendant timestamps
    posts = Post.query.order_by(Post.timestamp.desc()).limit(5)
    return render_template('index.html', title='Home', posts=posts)

@app.route('/post/<id>', methods=['GET', 'POST'])
def post(id): #View for full post, since the blog and index view only display title + description
    post = Post.query.filter_by(id=id).first()
    page = request.args.get('page', 1, type=int)
    comments = Comment.query.filter_by(post_id=id).order_by(Comment.timestamp.desc()).paginate(
        page, app.config['COMMENTS_PER_POST'], False)
    next_page = url_for('post', id=id, page=comments.next_num) if comments.has_next else None
    prev_page = url_for('post', id=id, page=comments.prev_num) if comments.has_prev else None
    form = CommentForm()
    if form.validate_on_submit(): #Post a new comment
        comment = Comment(email = form.email.data, name = form.name.data, comment = form.comment.data, post_id=id)
        db.session.add(comment)
        db.session.commit()
        stat_comment = Stats.query.filter_by(day_comments = date.today()).first()
        if stat_comment is None: #Probably will never happen since need visit first
            new_stat = Stats()
            db.session.add(new_stat)
            db.session.commit()
        else:
            stat_comment.comments += 1
            db.session.commit()
        flash('Your comment has been added.')
        return redirect(url_for('post', id=id))
    return render_template('post.html', title=post.title, form=form, post=post,
     comments=comments.items, next_page=next_page, prev_page=prev_page)

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
    stats = Stats.query.filter_by(day_comments = date.today()).first() #Query for stats of the day
    if form.validate_on_submit(): #Adding new post
        new_post = Post(title=form.title.data, description=form.description.data,
            body=form.body.data, user_id=current_user.id)
        db.session.add(new_post)
        db.session.commit()
        flash("New post has been posted")
        return redirect(url_for('dashboard'))
    return render_template('dashboard.html', title='Dashboard', form=form, stats = stats)

@app.route('/all_posts')
@login_required
def all_posts(): #In dashboard, display all blog posts with pagination and update/delete options
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('all_posts', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('all_posts', page=posts.prev_num) if posts.has_prev else None
    return render_template('all_posts.html', title='All posts', posts=posts.items,
        next_url=next_url, prev_url=prev_url)

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
def contact(): #Send email through contact page. Config in config.py
    form = ContactForm()
    if form.validate_on_submit():
        html_body = '<p>' + form.message.data + '</p>'
        send_email(form.subject.data, form.email.data, app.config['ADMINS'],
            form.message.data, html_body)
        flash('Your message has been sent.')
        return redirect(url_for('index'))
    return render_template('contact.html', title='Contact', form=form)

@app.route('/blog') #Display blog posts, paginated, following an env variable value
def blog():
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    next_url = url_for('blog', page=posts.next_num) if posts.has_next else None
    prev_url = url_for('blog', page=posts.prev_num) if posts.has_prev else None
    return render_template('blog.html', title='Blog', posts=posts.items,
        next_url=next_url, prev_url=prev_url)

@app.route('/update/<id>', methods = ['GET', 'POST']) #Simple update function for the posts
@login_required
def update(id):
    post = Post.query.filter_by(id=id).first()
    form = EditPostForm()
    if form.validate_on_submit(): #Update when submit button is clicked
        post.title = form.title.data
        post.description = form.description.data
        post.body = form.body.data
        db.session.commit()
        flash('Changes have been saved')
        return redirect(url_for('all_posts'))
    elif request.method == 'GET': #Load the form with the data of the post we are trying to update
        form.title.data = post.title
        form.description.data = post.description
        form.body.data = post.body
    return render_template('update.html', title='Update post', form=form)

@app.route('/rss') #Create a RSS feed based on the posts
def rss():
    fg = FeedGenerator()
    fg.title('RSS Feed for the blog')
    fg.description('Your regular RSS Feed to follow the blog')
    fg.link(href='{{url_for("index")}}')

    posts = Post.query.order_by(Post.timestamp.desc()).all()

    for post in posts:
        fe = fg.add_entry()
        fe.title(post.title)
        fe.link(href='{{ url_for("post", id=post.id) }}')
        fe.description(post.description)

    response = make_response(fg.rss_str())
    response.headers.set('Content-type', 'application/rss+xml')
    return response

@app.route('/comments_graph') #Create a .png graph using matplotlib to show the number of comments
def comments_graph():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    stats = Stats.query.all()
    x_points = [stat.day_comments.strftime("%m-%d-%Y") for stat in stats]
    y_points = [stat.comments for stat in stats]
    axis.plot(x_points, y_points, 'bo')

    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/png")

@app.route('/visits_graph') #Same function, but this time we aim at showcasing the number of visits
def visits_graph():
    fig = Figure()
    axis = fig.add_subplot(1, 1, 1)
    stats = Stats.query.all()
    x_points = [stat.day_visits.strftime("%m-%d-%Y") for stat in stats]
    y_points = [stat.visits for stat in stats]
    axis.plot(x_points, y_points, 'bo')

    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')
