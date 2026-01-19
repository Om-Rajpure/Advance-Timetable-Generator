from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    users = User.query.all()
    print("Existing users:")
    for u in users:
        print(f"ID: {u.id}, Username: {u.username}, Role: {u.role}")
        
    if not any(u.role == 'admin' for u in users):
        print("Creating admin user...")
        admin = User(username='admin', role='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
        print("Admin user created: admin / admin123")
    
    if not any(u.username == 'testuser' for u in users):
        print("Creating test user...")
        test = User(username='testuser', role='user', password_hash=generate_password_hash('test1234'))
        db.session.add(test)
        db.session.commit()
        print("Test user created: testuser / test1234")
