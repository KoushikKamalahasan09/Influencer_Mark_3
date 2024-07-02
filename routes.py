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
        if not user.type=='Admin':
            flash("You are not authorized to visit this page",category='delete')
            return redirect(url_for('login'))
        return func(*args, **kwargs)
    return wrapper

@app.route('/')
@login_required
def home():
    username=session['username']
    user = User.query.filter_by(username=username).first()
    if user.type=='Admin':
        return redirect(url_for('admin'))
    elif user.type=='Influencer':
        return render_template('influencer_home.html',user=user)
    else:
        return render_template('sponsor_home.html',user=user)
    
@app.route('/sponsor_home')
@login_required
def sponsor_home():
    return render_template('sponsor_home.html')

@app.route('/influencer_home')
@login_required
def influencer_home():
    return render_template('influencer_home.html')



@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.passhash, password):
        flash("Username or password is incorrect",category='delete')
        return redirect(url_for('login'))
    session['username'] = username
    return redirect(url_for('home'))

@app.route('/influencer_register')
def influencer_register():
    return render_template('influencer_register.html')

@app.route('/sponsor_register')
def sponsor_register():
    return render_template('sponsor_register.html')

@app.route('/sponsor_register', methods=['POST'])
def sponsor_register_post():
    name = request.form.get('name')
    username = request.form.get('username')
    password = request.form.get('password')
    confirm = request.form.get('confirm')

    # all not nullable inputs are not empty
    if not username or not password or not confirm:
        flash("Please fill all the mandatory fields")
        return redirect(url_for('sponsor_register'))

    # confirm and password should be same
    if password != confirm:
        flash("Both passwords don't match")
        return redirect(url_for('sponsor_register'))

    # username should be unique
    user = User.query.filter_by(username=username).first()
    if user:
        flash("Please choose another username, selected username is taken")
        return redirect(url_for('sponsor_register'))
    
    if len(username)<5:
        flash("Username must be at a minimum of 5 characters")
        return redirect(url_for('sponsor_register'))
    
    if len(password)<5:
        flash("Password must be at a minimum of 5 characters")
        return redirect(url_for('sponsor_register'))
    

    passhash = generate_password_hash(password)

    user = User(name=name, username=username, passhash=passhash,type='Sponsor')
    db.session.add(user)
    db.session.commit()
    flash("Registration Successful, Please login to continue" ,category="success")
    return redirect(url_for('login'))

@app.route('/influencer_register', methods=['POST'])
def influencer_register_post():
    name = request.form.get('name')
    username = request.form.get('username')
    password = request.form.get('password')
    confirm = request.form.get('confirm')

    # all not nullable inputs are not empty
    if not username or not password or not confirm:
        flash("Please fill all the mandatory fields")
        return redirect(url_for('Influencer_register'))

    # confirm and password should be same
    if password != confirm:
        flash("Both passwords don't match")
        return redirect(url_for('Influencer_register'))

    # username should be unique
    user = User.query.filter_by(username=username).first()
    if user:
        flash("Please choose another username, selected username is taken")
        return redirect(url_for('Influencer_register'))


    passhash = generate_password_hash(password)

    user = User(name=name, username=username, passhash=passhash,type='Influencer')
    db.session.add(user)
    db.session.commit()
    flash("Registration Successful, Please login to continue" ,category="success")
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    session.pop('username')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    username=session['username']
    user = User.query.filter_by(username=username).first()
    return render_template('profile.html',user=user)
    
@app.route('/users/<int:id>/delete', methods=['POST'])
@login_required
def delete_user(id):
    user = User.query.get(id)
    current_user = User.query.filter_by(username=session['username']).first()
    if not user:
        flash("Invalid User ID")
        return redirect(url_for('profile'))
    if user.username != session['username'] and not current_user.type=='Admin':
        flash("You are not authorized to perform this action")
        return redirect(url_for('profile'))
    if user.type=='Admin':
        flash("You cannot delete an admin")
        return redirect(url_for('profile'))

    db.session.delete(user)
    db.session.commit()
    flash("Delete succcessful")
    return redirect(url_for('profile'))


@app.route('/profile', methods=['POST'])
@login_required
def profile_post():
    nusername = request.form.get('username')
    password = request.form.get('password')
    npassword = request.form.get('npassword')
    username=session['username']
    user = User.query.filter_by(username=username).first()

    if password != "" and npassword != "":
        if check_password_hash(user.passhash, password):
            user.passhash = generate_password_hash(npassword)
            flash("Password changed successfully")
        else:
            flash("Entered current password is incorrect")

    if nusername != user.username and nusername != "":
        quser = User.query.filter_by(username=nusername).first()
        if quser:
            flash("Username is already taken, please choose any other username")
            return redirect(url_for('profile'))
        user.username = nusername
        session['username']=nusername
        flash(f"Username changed to {nusername}")

    db.session.commit()
    return redirect(url_for('profile'))

@app.route('/admin')
@admin_required
def admin():
    username=session['username']
    user = User.query.filter_by(username=username).first()
    users = User.query.all()
    return render_template('admin.html', users=users,user=user)


@app.route('/users')
@admin_required
def user_list():
    users = User.query.all()
    return render_template('admin_users.html', users=users)


#flash("sdyu",category='success or delete')