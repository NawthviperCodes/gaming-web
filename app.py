from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import os
import urllib.parse
import stripe
from dotenv import load_dotenv

# Load environment variables from .env (for local dev only)
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET_KEY', 'fallback-secret-key-for-dev')

# Stripe Config
stripe_keys = {
    'secret_key': os.getenv('STRIPE_SECRET_KEY'),
    'publishable_key': os.getenv('STRIPE_PUBLISHABLE_KEY')
}
stripe.api_key = stripe_keys['secret_key']

# PostgreSQL Config
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///local.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# -----------------------------
# Database Models
# -----------------------------

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    coins = db.Column(db.Float, default=0.0)
    sessions = db.relationship('GameSession', backref='user', lazy=True)

class Admin(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

class GameSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    game_name = db.Column(db.String(100), nullable=False)
    time_played = db.Column(db.Integer, default=0)  # in seconds
    cost = db.Column(db.Float, default=0.0)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

# -----------------------------
# Flask-Login Setup
# -----------------------------

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    if user:
        return user
    admin = Admin.query.get(int(user_id))
    if admin:
        return admin
    return None

# -----------------------------
# Routes
# -----------------------------

@app.route('/')
def index():
    if current_user.is_authenticated:
        if isinstance(current_user, Admin):
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Check if it's an admin first
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            login_user(admin)
            return redirect(url_for('admin_dashboard'))

        # Then check regular user
        user = User.query.filter_by(username=username, password=password).first()
        if user:
            login_user(user)
            return redirect(url_for('dashboard'))

        flash("Invalid username or password.")
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            login_user(admin)
            return redirect(url_for('admin_dashboard'))

        flash("Invalid admin credentials.")
        return redirect(url_for('admin_login'))

    return render_template('admin_login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    if isinstance(current_user, Admin):
        flash("❌ Access denied: Admins cannot access the user dashboard.")
        return redirect(url_for('admin_dashboard'))

    return render_template('dashboard.html', username=current_user.username, coins=current_user.coins)


@app.route('/admin')
@login_required
def admin_dashboard():
    if not isinstance(current_user, Admin):
        flash("❌ Access denied: Admins only.")
        return redirect(url_for('index'))

    total_revenue = sum(session.cost for session in GameSession.query.all())
    total_sessions = GameSession.query.count()
    users = User.query.all()

    user_data = []
    for user in users:
        total_time = sum(s.time_played for s in user.sessions)
        total_spent = sum(s.cost for s in user.sessions)
        user_data.append({
            'username': user.username,
            'total_time': total_time,
            'total_spent': total_spent
        })

    return render_template('admin.html',
                           total_revenue=total_revenue,
                           total_sessions=total_sessions,
                           users=user_data)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            flash("Username already exists!")
            return redirect(url_for('register'))
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration successful! Please log in.")
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/add_coins')
@login_required
def add_coins():
    amount = float(request.args.get('amount', 5.0))
    current_user.coins += amount * 10
    db.session.commit()
    flash(f"${amount:.2f} added to your account. New balance: ${current_user.coins:.2f}")
    return redirect(url_for('dashboard'))


# -----------------------------
# Initialize Database
# -----------------------------

with app.app_context():
    db.create_all()

    # Add sample games
    if not Game.query.all():
        games = ['Pong', 'Space Invaders', 'Tetris', 'Snake']
        for name in games:
            db.session.add(Game(name=name))
        db.session.commit()

# -----------------------------
# Run App
# -----------------------------

if __name__ == '__main__':
    app.run(debug=True)