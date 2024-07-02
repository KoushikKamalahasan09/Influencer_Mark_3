from main import app
from flask import Flask, render_template, request, redirect, session, url_for, flash
from models import db, User, CampaignInfluencer, Campaign, SponsorProfile, InfluencerProfile
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime

# routes

def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("You need to login first")
            return redirect(url_for('login'))
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'username' not in session:
            flash("You need to login first")
            return redirect(url_for('login'))
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            session.pop('username')
            return redirect(url_for('login'))
        if not user.type == 'Admin':
            flash("You are not authorized to visit this page", category='delete')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

@app.route('/')
@login_required
def home():
    username = session['username']
    user = User.query.filter_by(username=username).first()
    if user.type == 'Admin':
        return redirect(url_for('admin_dashboard'))
    elif user.type == 'Influencer':
        return redirect(url_for('influencer_dashboard'))
    else:
        return redirect(url_for('sponsor_dashboard'))

@app.route('/sponsor_dashboard')
@login_required
def sponsor_dashboard():
    username = session['username']
    user = User.query.filter_by(username=username).first()
    campaigns = Campaign.query.filter_by(sponsor_id=user.user_id).all()
    return render_template('sponsor_dashboard.html', user=user, campaigns=campaigns)

@app.route('/influencer_dashboard')
@login_required
def influencer_dashboard():
    username = session['username']
    user = User.query.filter_by(username=username).first()
    campaigns = CampaignInfluencer.query.filter_by(influencer_id=user.user_id).all()
    return render_template('influencer_dashboard.html', user=user, campaigns=campaigns)

@app.route('/admin_dashboard')
@admin_required
def admin_dashboard():
    users = User.query.all()
    campaigns = Campaign.query.all()
    return render_template('admin_dashboard.html', users=users, campaigns=campaigns)

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.passhash, password):
        flash("Username or password is incorrect", category='delete')
        return redirect(url_for('login'))
    session['username'] = username
    return redirect(url_for('home'))

@app.route('/register/<user_type>')
def register(user_type):
    return render_template('register.html', user_type=user_type)

@app.route('/register/<user_type>', methods=['POST'])
def register_post(user_type):
    name = request.form.get('name')
    username = request.form.get('username')
    password = request.form.get('password')
    confirm = request.form.get('confirm')

    if not username or not password or not confirm:
        flash("Please fill all the mandatory fields")
        return redirect(url_for('register', user_type=user_type))

    if password != confirm:
        flash("Both passwords don't match")
        return redirect(url_for('register', user_type=user_type))

    user = User.query.filter_by(username=username).first()
    if user:
        flash("Please choose another username, selected username is taken")
        return redirect(url_for('register', user_type=user_type))

    if len(username) < 5:
        flash("Username must be at a minimum of 5 characters")
        return redirect(url_for('register', user_type=user_type))

    if len(password) < 5:
        flash("Password must be at a minimum of 5 characters")
        return redirect(url_for('register', user_type=user_type))

    passhash = generate_password_hash(password)
    user = User(name=name, username=username, passhash=passhash, type=user_type)
    db.session.add(user)
    db.session.commit()
    flash("Registration Successful, Please login to continue", category="success")
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    session.pop('username')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    username = session['username']
    user = User.query.filter_by(username=username).first()
    return render_template('profile.html', user=user)

@app.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.get(id)
    current_user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash("Invalid User ID")
        return redirect(url_for('profile'))
    if user.username != session['username'] and not current_user.type == 'Admin':
        flash("You are not authorized to perform this action")
        return redirect(url_for('profile'))
    if user.type == 'Admin':
        flash("You cannot delete an admin")
        return redirect(url_for('profile'))

    db.session.delete(user)
    db.session.commit()
    flash("Delete successful")
    return redirect(url_for('profile'))

@app.route('/profile', methods=['POST'])
@login_required
def profile_post():
    nusername = request.form.get('username')
    password = request.form.get('password')
    npassword = request.form.get('npassword')
    username = session['username']
    user = User.query.filter_by(username=username).first()

    if password and npassword:
        if check_password_hash(user.passhash, password):
            user.passhash = generate_password_hash(npassword)
            flash("Password changed successfully")
        else:
            flash("Entered current password is incorrect")

    if user.username != nusername:
        if User.query.filter_by(username=nusername).first():
            flash("This username is already taken")
        else:
            user.username = nusername
            session['username'] = nusername
            flash("Username changed successfully")

    db.session.add(user)
    db.session.commit()
    return redirect(url_for('profile'))

@app.route('/campaigns/create', methods=['GET', 'POST'])
@login_required
def create_campaign():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        budget = request.form.get('budget')
        username = session['username']
        user = User.query.filter_by(username=username).first()

        campaign = Campaign(title=title, description=description, budget=budget, sponsor_id=user.user_id)
        db.session.add(campaign)
        db.session.commit()

        flash('Campaign created successfully', 'success')
        return redirect(url_for('sponsor_dashboard'))

    return render_template('create_campaign.html')

@app.route('/campaigns/<int:campaign_id>/influencers', methods=['GET', 'POST'])
@login_required
def add_influencers_to_campaign(campaign_id):
    if request.method == 'POST':
        influencer_username = request.form.get('influencer_username')
        influencer = User.query.filter_by(username=influencer_username, type='Influencer').first()
        if not influencer:
            flash("Influencer not found", 'error')
            return redirect(url_for('add_influencers_to_campaign', campaign_id=campaign_id))

        campaign_influencer = CampaignInfluencer(campaign_id=campaign_id, influencer_id=influencer.user_id)
        db.session.add(campaign_influencer)
        db.session.commit()

        flash('Influencer added to campaign successfully', 'success')
        return redirect(url_for('sponsor_dashboard'))

    campaign = Campaign.query.get(campaign_id)
    return render_template('add_influencers_to_campaign.html', campaign=campaign)

@app.route('/campaigns/<int:campaign_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_campaign(campaign_id):
    campaign = Campaign.query.get(campaign_id)
    if request.method == 'POST':
        campaign.title = request.form.get('title')
        campaign.description = request.form.get('description')
        campaign.budget = request.form.get('budget')
        db.session.commit()

        flash('Campaign updated successfully', 'success')
        return redirect(url_for('sponsor_dashboard'))

    return render_template('edit_campaign.html', campaign=campaign)
