from app import app, db, User, create_tables

with app.app_context():
    create_tables()
    users = User.query.all()
    print(f"Total users in database: {len(users)}")
    for user in users:
        print(f"ID: {user.id}, Username: {user.username}, Role: {user.role}")
