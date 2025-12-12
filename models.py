from datetime import datetime, timedelta, timezone
from extensions import db


class User(db.Model):
    """Рівень 1: Користувач (Власник)."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="applicant")
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, raw_password: str) -> None:
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, raw_password)


class Application(db.Model):
    """Рівень 2: Заявка (Master)."""
    __tablename__ = 'applications'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    short_description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default="draft")
    expert_comment = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    owner = db.relationship("User", backref="applications")


class Author(db.Model):
    """Рівень 3: Автор (Detail). Це додає необхідну глибину зв'язків."""
    __tablename__ = 'authors'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    contribution_percent = db.Column(db.Integer, default=100)  # Вклад у відсотках

    # Зв'язок з заявкою
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)
    application = db.relationship("Application", backref="authors")


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    used = db.Column(db.Boolean, default=False)
    user = db.relationship("User")

    @property
    def is_expired(self) -> bool:
        now_utc_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        return now_utc_naive > self.created_at + timedelta(hours=24)