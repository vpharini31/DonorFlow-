# app/cli.py
import os
import csv
import click
from app import db
from app.models import Home

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
                    req_medical=row.get('req_medical'))
                db.session.add(home)
        
        db.session.commit()
        print("Homes have been successfully imported.")