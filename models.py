from datetime import datetime, timedelta, timezone
from extensions import db


class User(db.Model):
    """Користувач системи."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Ролі: 'applicant', 'expert', 'admin'
    role = db.Column(db.String(50), default="applicant")

    # НОВЕ ПОЛЕ: Блокування користувача
    is_blocked = db.Column(db.Boolean, default=False)

    # Використовуємо lambda з timezone.utc замість datetime.utcnow
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, raw_password: str) -> None:
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, raw_password)


class PasswordResetToken(db.Model):
    """Токен для відновлення пароля."""
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    used = db.Column(db.Boolean, default=False)

    user = db.relationship("User")

    @property
    def is_expired(self) -> bool:
        # Порівнюємо поточний UTC час (приведений до naive format для сумісності з БД)
        # з часом створення токена + 24 години
        now_utc_naive = datetime.now(timezone.utc).replace(tzinfo=None)
        return now_utc_naive > self.created_at + timedelta(hours=24)


class Application(db.Model):
    """Заявка на авторське свідоцтво."""
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

    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    owner = db.relationship("User", backref="applications")