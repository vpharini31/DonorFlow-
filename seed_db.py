import csv
from app import create_app, db
from app.models import User, Home, Reward

def seed_data():
    """
    Seeds the database with home and admin data from a CSV file.
    """
    app = create_app()
    with app.app_context():
        # Clear existing data to prevent duplicates if run multiple times
        # Use with caution in a production environment
        print("Clearing existing data...")
        Home.query.delete()
        User.query.filter(User.role == 'home_admin').delete()
        # Also clear rewards to prevent duplicates
        Reward.query.delete()

        db.session.commit()

        print("Seeding new data from homes_dataset.csv...")
        try:
            with open('homes_dataset.csv', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    # Check if user already exists
                    existing_user = User.query.filter_by(username=row['admin_username']).first()
                    if existing_user:
                        print(f"Admin user '{row['admin_username']}' already exists. Skipping.")
                        continue

                    # Create the Home Admin User
                    admin_user = User(
                        username=row['admin_username'],
                        email=row['admin_email'],
                        phone_number=row['admin_phone_number'],
                        role='home_admin'
                    )
                    # Set a default password for all seeded admins
                    admin_user.set_password('password123')
                    
                    # Create the Home and associate it with the admin
                    new_home = Home(
                        name=row['name'],
                        address=row['address'],
                        description=row['description'],
                        occupant_count=int(row['occupant_count']),
                        contact_phone=row['contact_phone'],
                        payment_details=row['payment_details'],
                        req_grocery=row['req_grocery'],
                        req_clothes=row['req_clothes'],
                        req_stationary=row['req_stationary'],
                        req_medical=row['req_medical'],
                        admin=admin_user  # Link the home to the user
                    )
                    
                    db.session.add(admin_user)
                    db.session.add(new_home)
                    print(f"Added Home: '{row['name']}' with Admin: '{row['admin_username']}'")

            # Seed Rewards
            print("\nSeeding rewards...")
            rewards_data = [
                {'name': 'Bronze Star Donor', 'description': 'A digital badge to show your amazing support.', 'points_cost': 50, 'icon': 'bi-patch-check-fill text-warning'},
                {'name': 'Silver Heart Donor', 'description': 'A special silver-tier badge for your profile.', 'points_cost': 150, 'icon': 'bi-award-fill text-secondary'},
                {'name': 'Golden Kindness Badge', 'description': 'The gold standard of generosity! A premium digital badge.', 'points_cost': 300, 'icon': 'bi-gem text-primary'},
                {'name': 'Community Hero Certificate', 'description': 'A personalized digital certificate recognizing you as a community hero.', 'points_cost': 500, 'icon': 'bi-file-earmark-text-fill text-info'},
                {'name': 'Sponsor a Meal', 'description': 'Your points will be converted to sponsor a special meal for a small group.', 'points_cost': 750, 'icon': 'bi-cup-hot-fill text-danger'},
                {'name': 'Platinum Philanthropist', 'description': 'The ultimate recognition! Your name featured on our "Wall of Fame".', 'points_cost': 1000, 'icon': 'bi-shield-fill-check text-success'}
            ]

            for r_data in rewards_data:
                reward = Reward(**r_data)
                db.session.add(reward)
                print(f"Added Reward: '{r_data['name']}'")

                db.session.commit()
            print("\nDatabase seeding completed successfully!")
            print("All home admins have a default password: password123")

        except FileNotFoundError:
            print("Error: homes_dataset.csv not found. Please make sure the file is in the root directory.")
        except Exception as e:
            print(f"An error occurred: {e}")
            db.session.rollback()

if __name__ == '__main__':
    seed_data()
