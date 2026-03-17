from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from model import predict_comment

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///comments.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ----------------- DATABASE MODELS -----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(200))
    is_admin = db.Column(db.Boolean, default=False)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(500))
    result = db.Column(db.String(200))
    language = db.Column(db.String(10))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

# ----------------- INIT DB -----------------
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username='admin').first():
        admin = User(
            email='admin@example.com',
            username='admin',
            password=generate_password_hash('admin123', method='pbkdf2:sha256'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

# ----------------- LOGIN -----------------
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# ----------------- ROUTES -----------------

@app.route("/register", methods=['GET','POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash("Username already exists!")
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash("Email already registered!")
            return redirect(url_for('register'))

        new_user = User(
            email=email,
            username=username,
            password=generate_password_hash(password, method='pbkdf2:sha256'),
            is_admin=False
        )
        db.session.add(new_user)
        db.session.commit()

        flash("Registration successful! Please login.")
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route("/login", methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials!")

    return render_template('login.html')


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ✅ HOME (FIXED)
@app.route("/", methods=["GET","POST"])
@login_required
def home():
    result = None

    if request.method == "POST":
        comment_text = request.form["comment"]
        result = predict_comment(comment_text)

        language = 'ko' if any(c in comment_text for c in ['너','바보','ㅋㅋ']) else 'en'

        new_comment = Comment(
            text=comment_text,
            result=result,
            language=language,
            user_id=current_user.id
        )
        db.session.add(new_comment)
        db.session.commit()

    all_comments = Comment.query.filter_by(user_id=current_user.id).order_by(Comment.timestamp.desc()).all()

    return render_template(
        "index.html",
        result=result,
        comments=all_comments,
        user=current_user
    )


# ✅ DELETE ROUTE (so your HTML works without change)
@app.route("/delete_comment/<int:id>")
@login_required
def delete_comment(id):
    comment = db.session.get(Comment, id)

    if comment:
        # allow only owner or admin
        if comment.user_id == current_user.id or current_user.is_admin:
            db.session.delete(comment)
            db.session.commit()

    return redirect(url_for('home'))


# ----------------- RUN -----------------
if __name__ == "__main__":
    app.run(debug=True)
