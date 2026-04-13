from app import db

if __name__ == "__main__":
    print("Initializing DB schema...")
    db.init_db()
    print("Done. Database created.")
