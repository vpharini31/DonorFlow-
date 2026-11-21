# app/cli.py
import os
import csv
import click
from app import db
from app.models import User, Home, Donation, VolunteerOpportunity
from sqlalchemy import text

def register_commands(app):
    @app.cli.command("import-homes")
    @click.argument("csv_file")
    def import_homes(csv_file):
        """Imports homes from a CSV file into the database."""
        if not os.path.exists(csv_file):
            print(f"Error: File '{csv_file}' not found.")
            return

        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Check if home already exists to avoid duplicates
                existing_home = Home.query.filter_by(name=row['name']).first()
                if existing_home:
                    continue

                home = Home(
                    name=row['name'], address=row['address'], description=row['description'],
                    latitude=float(row['latitude']), longitude=float(row['longitude']),
                    occupant_count=int(row['occupant_count']),
                    req_grocery=row.get('req_grocery'),
                    req_clothes=row.get('req_clothes'),
                    req_stationary=row.get('req_stationary'),
                    req_medical=row.get('req_medical'),
                    is_verified=True) # Trusted import
                db.session.add(home)
        
        db.session.commit()
        print("Homes have been successfully imported.")

    @app.cli.command("seed-db")
    def seed_db():
        """Populates the database with dummy data for demonstration."""
        # Create a Home Admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', email='admin@example.com', phone_number='9876543210', role='home_admin')
            admin.set_password('password')
            db.session.add(admin)
            print("Created Admin: admin / password")
        
        # Create a Donor
        donor = User.query.filter_by(username='donor').first()
        if not donor:
            donor = User(username='donor', email='donor@example.com', phone_number='1234567890', role='donor')
            donor.set_password('password')
            db.session.add(donor)
            print("Created Donor: donor / password")

        db.session.commit() # Commit users to get IDs

        # Create a Home
        home = Home.query.filter_by(name='Sunshine Orphanage').first()
        if not home:
            home = Home(
                name='Sunshine Orphanage',
                address='123 Sunshine Lane, Happy City',
                description='A home for children providing education and care.',
                occupant_count=45,
                contact_phone='9876543210',
                payment_details='sunshine@upi',
                req_grocery='Rice, Dal, Oil',
                req_stationary='Notebooks, Pencils',
                admin=admin,
                is_verified=True
            )
            db.session.add(home)
            print("Created Home: Sunshine Orphanage")

        # Create a Volunteer Opportunity
        if home:
            op = VolunteerOpportunity(
                title='Weekend Math Tutor',
                description='Teach basic math to children aged 10-12.',
                skills_required='Math, Patience',
                time_commitment='2 hours / weekend',
                home=home
            )
            db.session.add(op)
            
        db.session.commit()
        print("Database seeded successfully!")

    @app.cli.command("verify-home")
    @click.argument("home_name")
    def verify_home(home_name):
        """Verifies a home, making it visible to donors."""
        home = Home.query.filter_by(name=home_name).first()
        if home:
            home.is_verified = True
            db.session.commit()
            print(f"Success: Home '{home.name}' has been verified and is now visible to donors.")
        else:
            print(f"Error: Home '{home_name}' not found.")

    @app.cli.command("list-pending")
    def list_pending():
        """Lists all homes waiting for verification."""
        homes = Home.query.filter_by(is_verified=False).all()
        if not homes:
            print("No homes are currently pending verification.")
        else:
            print(f"Found {len(homes)} homes pending verification:")
            for home in homes:
                print(f" - Name: '{home.name}' | Contact: {home.contact_phone} | Admin: {home.admin.username}")

    @app.cli.command("fix-schema")
    def fix_schema():
        """Manually adds missing columns to the database schema."""
        with db.engine.connect() as conn:
            # Add is_verified
            try:
                conn.execute(text("ALTER TABLE home ADD COLUMN is_verified BOOLEAN DEFAULT 0"))
                print("Added 'is_verified' column.")
            except Exception:
                print("'is_verified' column already exists or could not be added.")

            # Add latitude (if missing from previous steps)
            try:
                conn.execute(text("ALTER TABLE home ADD COLUMN latitude FLOAT"))
                print("Added 'latitude' column.")
            except Exception:
                print("'latitude' column already exists or could not be added.")

            # Add longitude (if missing from previous steps)
            try:
                conn.execute(text("ALTER TABLE home ADD COLUMN longitude FLOAT"))
                print("Added 'longitude' column.")
            except Exception:
                print("'longitude' column already exists or could not be added.")
            
            # Add amount to donation
            try:
                conn.execute(text("ALTER TABLE donation ADD COLUMN amount FLOAT"))
                print("Added 'amount' column to donation table.")
            except Exception:
                print("'amount' column already exists or could not be added.")
            
            # Add transaction_id to donation
            try:
                conn.execute(text("ALTER TABLE donation ADD COLUMN transaction_id VARCHAR(100)"))
                print("Added 'transaction_id' column to donation table.")
            except Exception:
                print("'transaction_id' column already exists or could not be added.")
            
            conn.commit()
        print("Schema update complete.")

    @app.cli.command("create-superuser")
    @click.argument("username")
    @click.argument("password")
    def create_superuser(username, password):
        """Creates a superuser account for the platform owner."""
        if User.query.filter_by(username=username).first():
            print(f"Error: User '{username}' already exists.")
            return
        user = User(username=username, email=f"{username}@admin.local", phone_number="0000000000", role='superuser')
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Superuser '{username}' created successfully.")