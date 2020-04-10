from flask import render_template, redirect, url_for
from app.forms import LoginDashboardForm
from app import app

@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    form = LoginDashboardForm()
    if form.validate_on_submit():
        return redirect(url_for('dashboard'))
    return render_template('login_dashboard.html', title='Dashboard Login', form=form)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html', title='Dashboard')
