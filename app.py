from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import urllib.parse
import stripe
from dotenv import load_dotenv
import os

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
        return redirect(url_for('dashboard'))
    return render_template('index.html')

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

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username, password=password).first()
        if admin:
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
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
        else:
            flash("Invalid admin credentials.")
    return render_template('admin_login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Prevent admins from accessing the user dashboard
    if isinstance(current_user, Admin):
        flash("❌ Access denied: Admins only.")
        return redirect(url_for('admin_dashboard'))

    games = Game.query.all()
    return render_template('dashboard.html', username=current_user.username, coins=current_user.coins, games=games)

@app.route('/help-center')
def help_center():
    return render_template('help_center.html')

@app.route('/faq')
def faq():
    return render_template('faq.html')

@app.route('/contact-us')
def contact_us():
    return render_template('contact_us.html')

@app.route('/terms-of-service')
def terms_of_service():
    return render_template('terms_of_service.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/tournaments')
def tournaments():
    return render_template('tournaments.html')

@app.route('/leaderboard')
def leaderboard():
    # Fetch top players based on coins or other metrics
    users = User.query.order_by(User.coins.desc()).all()
    return render_template('leaderboard.html', users=users)

@app.route('/game')
@login_required
def play_game():
    # Prevent admins from playing games
    if isinstance(current_user, Admin):
        flash("❌ Access denied: Admins only.")
        return redirect(url_for('admin_dashboard'))

    game_name = request.args.get('name', 'Unknown Game')
    return render_template('game.html', game_name=game_name)

@app.route('/end_session')
@login_required
def end_session():
    # Prevent admins from ending sessions
    if isinstance(current_user, Admin):
        flash("❌ Access denied: Admins only.")
        return redirect(url_for('admin_dashboard'))

    try:
        time_played = int(request.args.get('time', 10))
    except ValueError:
        time_played = 10
    cost = round(time_played * 0.05, 2)
    if current_user.coins >= cost:
        current_user.coins -= cost
        new_session = GameSession(game_name="Unknown Game", time_played=time_played, cost=cost, user_id=current_user.id)
        db.session.add(new_session)
        db.session.commit()
        flash(f"You played for {time_played}s. Deducted ${cost:.2f}. Remaining balance: ${current_user.coins:.2f}")
    else:
        flash("Not enough coins to play this session.")
    return redirect(url_for('dashboard'))

@app.route('/admin')
@login_required
def admin_dashboard():
    # Ensure only admins can access this route
    if not isinstance(current_user, Admin):
        flash("❌ Access denied: Admins only.")
        return redirect(url_for('index'))

    total_revenue = sum(session.cost for session in GameSession.query.all())
    total_sessions = GameSession.query.count()
    users = User.query.all()
    games = Game.query.all()

    user_data = []
    for user in users:
        total_time = sum(s.time_played for s in user.sessions)
        total_spent = sum(s.cost for s in user.sessions)
        user_data.append({
            'username': user.username,
            'total_time': total_time,
            'total_spent': total_spent
        })

    return render_template('admin.html', total_revenue=total_revenue, total_sessions=total_sessions, users=user_data, games=games)

@app.route('/admin/add_game', methods=['POST'])
@login_required
def add_game():
    # Ensure only admins can add games
    if not isinstance(current_user, Admin):
        flash("Access denied.")
        return redirect(url_for('index'))

    game_name = request.form['game_name']
    if Game.query.filter_by(name=game_name).first():
        flash("Game already exists.")
        return redirect(url_for('admin_dashboard'))

    new_game = Game(name=game_name)
    db.session.add(new_game)
    db.session.commit()
    flash(f"Game '{game_name}' added.")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_game/<int:game_id>')
@login_required
def delete_game(game_id):
    # Ensure only admins can delete games
    if not isinstance(current_user, Admin):
        flash("Access denied.")
        return redirect(url_for('index'))

    game = Game.query.get_or_404(game_id)
    db.session.delete(game)
    db.session.commit()
    flash(f"Game '{game.name}' deleted.")
    return redirect(url_for('admin_dashboard'))

@app.route('/add_coins')
@login_required
def add_coins():
    amount = float(request.args.get('amount', 5.0))
    current_user.coins += amount * 10
    db.session.commit()
    flash(f"${amount:.2f} added to your account. New balance: ${current_user.coins:.2f}")
    return redirect(url_for('dashboard'))

@app.route('/topup', methods=['GET', 'POST'])
@login_required
def topup():
    return render_template('payment.html')

@app.route('/topup/<float:amount>')
@login_required
def topup_amount(amount):
    coin_amount = int(amount * 10)
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{coin_amount} Coins',
                    },
                    'unit_amount': int(amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('topup', _external=True),
            metadata={'user_id': current_user.id, 'coins': coin_amount}
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(f"Payment error: {str(e)}")
        return redirect(url_for('dashboard'))

@app.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    try:
        amount = float(request.form['amount'])
        if amount <= 0:
            flash("Invalid amount. Please enter a positive value.")
            return redirect(url_for('dashboard'))
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': f'{amount * 10} Coins',
                    },
                    'unit_amount': int(amount * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=url_for('payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('dashboard', _external=True),
            metadata={'user_id': current_user.id, 'coins': amount * 10}
        )
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(f"Error processing payment: {str(e)}")
        return redirect(url_for('dashboard'))

@app.route('/payment/success')
@login_required
def payment_success():
    session_id = request.args.get('session_id')
    session_data = stripe.checkout.Session.retrieve(session_id)
    user_id = int(session_data.metadata.user_id)
    coins = int(session_data.metadata.coins)
    user = User.query.get(user_id)
    user.coins += coins
    db.session.commit()
    flash(f"{coins} coins added to your account!")
    return redirect(url_for('dashboard'))

# -----------------------------
# Initialize Database
# -----------------------------

with app.app_context():
    db.create_all()
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