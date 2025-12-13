from datetime import datetime, timedelta, timezone
from extensions import db


class User(db.Model):
    """Користувач системи."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default="applicant")  # applicant, expert, admin, super_admin
    is_blocked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, raw_password: str) -> None:
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, raw_password)


class PasswordResetToken(db.Model):
    """Токен для відновлення пароля."""
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


class Application(db.Model):
    """Заявка на авторське свідоцтво."""
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

    # Зв'язок з файлами
    files = db.relationship("ApplicationFile", backref="application", cascade="all, delete-orphan")

    # НОВЕ: Зв'язок з історією (сортування від нових до старих)
    history = db.relationship("ApplicationHistory", backref="application", cascade="all, delete-orphan",
                              order_by="desc(ApplicationHistory.created_at)")


class ApplicationFile(db.Model):
    """Файл, прикріплений до заявки."""
    __tablename__ = 'application_files'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)

    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class ApplicationHistory(db.Model):
    """Історія змін заявки."""
    __tablename__ = 'application_history'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey("applications.id"), nullable=False)

    # Хто зробив зміну
    changed_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    changed_by = db.relationship("User")

    # Тип події: 'created', 'edited', 'status_change'
    event_type = db.Column(db.String(50), nullable=False)

    # Знімок даних на момент зміни
    snapshot_title = db.Column(db.String(255), nullable=True)
    snapshot_description = db.Column(db.Text, nullable=True)
    snapshot_status = db.Column(db.String(50), nullable=True)
    snapshot_comment = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))