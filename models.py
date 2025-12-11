from datetime import datetime, timedelta

from app import db


class User(db.Model):
    """Користувач системи."""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="applicant")  # applicant / expert / admin
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw_password: str) -> None:
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, raw_password)


class PasswordResetToken(db.Model):
    """Токен для відновлення пароля (спрощений варіант для навчального проєкту)."""
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)

    user = db.relationship("User")

    @property
    def is_expired(self) -> bool:
        # Токен діє 24 години
        return datetime.utcnow() > self.created_at + timedelta(hours=24)


class Application(db.Model):
    """Заявка на авторське свідоцтво."""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    short_description = db.Column(db.Text, nullable=False)

    status = db.Column(db.String(50), nullable=False, default="draft")
    # Можливі значення:
    # draft         – чорнетка
    # submitted     – подано на розгляд
    # under_review  – на розгляді (епік 3)
    # needs_changes – потребує доопрацювання
    # rejected      – відхилено
    # approved      – схвалено
    # cancelled     – скасовано заявником

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    owner = db.relationship("User", backref="applications")