from datetime import datetime
from database import db

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='faculty')  # 'admin' or 'faculty'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    timetables = db.relationship('Timetable', backref='owner', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

class Timetable(db.Model):
    __tablename__ = 'timetables'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    academic_year = db.Column(db.String(20), nullable=True)
    division = db.Column(db.String(20), nullable=True)
    status = db.Column(db.String(20), default='success')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    entries = db.relationship('TimetableEntry', backref='timetable', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'userId': self.user_id,
            'academicYear': self.academic_year,
            'division': self.division,
            'status': self.status,
            'createdAt': self.created_at.isoformat(),
            'entryCount': len(self.entries) if self.entries else 0
        }

class TimetableEntry(db.Model):
    __tablename__ = 'timetable_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    timetable_id = db.Column(db.Integer, db.ForeignKey('timetables.id'), nullable=False)
    day = db.Column(db.String(20), nullable=False)
    slot_index = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    teacher = db.Column(db.String(100), nullable=False)
    batch = db.Column(db.String(20), nullable=True) # For labs

    def to_dict(self):
        return {
            'id': self.id,
            'day': self.day,
            'slotIndex': self.slot_index,
            'subject': self.subject,
            'teacher': self.teacher,
            'batch': self.batch
        }

class Branch(db.Model):
    __tablename__ = 'branches'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    config = db.Column(db.JSON, nullable=False) # Store full JSON config
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'config': self.config,
            'created_at': self.created_at.isoformat()
        }

class SmartInput(db.Model):
    __tablename__ = 'smart_inputs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branches.id'), nullable=True) # Optional link
    data = db.Column(db.JSON, nullable=False) # Store full input data
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'data': self.data,
            'created_at': self.created_at.isoformat()
        }
