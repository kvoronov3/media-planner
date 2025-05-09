from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Platform(db.Model):
    __tablename__ = 'platforms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    average_ctr = db.Column(db.Float, default=0.0)

class MediaPlan(db.Model):
    __tablename__ = 'media_plans'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    budget = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)  # "Мужчины", "Женщины", "Оба пола"
    age_groups = db.Column(db.String(200), nullable=False)  # Например, "До 18,18-25"
    income_level = db.Column(db.String(20), nullable=False)  # "Низкий", "Средний", "Высокий"
    campaign_cycle = db.Column(db.String(50))
    platforms = db.relationship('MediaPlanPlatform', backref='media_plan', lazy=True, cascade='all, delete-orphan')

class MediaPlanPlatform(db.Model):
    __tablename__ = 'media_plan_platforms'
    id = db.Column(db.Integer, primary_key=True)
    media_plan_id = db.Column(db.Integer, db.ForeignKey('media_plans.id'), nullable=False)
    platform_id = db.Column(db.Integer, db.ForeignKey('platforms.id'), nullable=False)
    budget = db.Column(db.Float, nullable=False)
    impressions = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    platform = db.relationship('Platform', backref='media_plan_platforms')