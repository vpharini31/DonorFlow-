# DonorFlow 🤝

A comprehensive, community-driven web application built with Flask that connects generous donors, volunteers, and care homes (orphanages, elder care, and shelters) in one unified platform.

---

## 🌟 Key Features

### 🏡 Care Home Administration
- **Profile & Needs Management:** Homes can manage descriptions, occupant counts, contact details, and specify real-time needs across groceries, clothing, stationery, and medical supplies.
- **Verification System:** Trust is maintained through verification before homes appear publicly in the donor discovery feed.
- **Donation Tracking & Confirmations:** View incoming monetary and in-kind donation submissions, verify transaction IDs, and send personalized thank-you messages to donors.

### 💖 Donors & Contributions
- **Browse & Search Homes:** Explore verified homes with location details, contact numbers, and urgent requirements.
- **Direct UPI QR Code Payments:** Automatically generates dynamic UPI QR codes for seamless and direct payments to homes.
- **In-Kind Donations:** Pledge goods and essential items directly matching what each home requests.
- **Donation Receipts & History:** View past donations, confirmation status, and printable transaction receipts.

### 🙋 Volunteer Opportunities
- **Job Postings:** Care homes can post volunteer roles with required skills and time commitments.
- **Application Portal:** Donors and community members can apply for volunteer positions.
- **Applicant Review:** Home admins can review and update application status (`pending`, `accepted`, `rejected`).

### 🏆 Gamification & Rewards
- **Points System:** Earn donor points with each confirmed contribution.
- **Digital Badges & Rewards:** Redeem earned points for tier badges (*Bronze Star*, *Silver Heart*, *Community Hero*, etc.).
- **Leaderboard:** Showcase top community contributors to foster engagement and generosity.

### 🛡️ Multi-Tier Roles & Permissions
- **Donor:** Discover homes, donate, volunteer, and track personal impact.
- **Home Admin:** Manage home profile, requirements, volunteer postings, and donations.
- **Superuser:** Platform oversight to review, list, and verify newly registered homes.

---

## 🛠️ Tech Stack

- **Backend:** Python 3, Flask
- **ORM & Database:** SQLAlchemy, Flask-SQLAlchemy, SQLite (production-ready for PostgreSQL/MySQL via `DATABASE_URL`)
- **Authentication:** Flask-Login, Werkzeug Security
- **Forms & Validation:** Flask-WTF, WTForms
- **Database Migrations:** Flask-Migrate (Alembic)
- **Utilities:** `qrcode[pil]` (Dynamic QR code generation), Python Logging
- **Frontend:** Jinja2 templates, HTML5, CSS3, Bootstrap 5, Bootstrap Icons

---

## 📁 Project Structure

```text
charity_app/
├── app/
│   ├── static/           # Static assets (CSS, images)
│   ├── templates/        # Jinja2 HTML templates
│   ├── __init__.py       # Application factory & setup
│   ├── cli.py            # Custom Flask CLI management commands
│   ├── forms.py          # WTForms form models & validation
│   ├── models.py         # SQLAlchemy database models
│   └── routes.py         # Application views and endpoints
├── migrations/           # Alembic database migration scripts
├── config.py             # Configuration classes & environment setup
├── homes_dataset.csv     # Sample dataset of care homes
├── requirements.txt      # Python dependencies
├── run.py                # Development server runner
├── seed_db.py            # Database seeding utility
└── README.md             # Project documentation
```

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have **Python 3.10+** and **Git** installed on your system.

### 2. Clone the Repository
```bash
git clone https://github.com/vpharini31/DonorFlow-.git
cd DonorFlow-
```

### 3. Create and Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```
*(If PowerShell restricts scripts, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first)*

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Initialize & Seed the Database
Populate initial homes, rewards, and default admin accounts:
```bash
python seed_db.py
```

### 6. Run the Application
```bash
python run.py
```

The web application will be accessible at:
👉 **`http://127.0.0.1:5000`**

---

## 🧑‍💻 CLI Commands

The application includes convenient CLI management utilities registered under Flask:

- **Seed sample data:**
  ```bash
  flask seed-db
  ```
- **Create a platform superuser:**
  ```bash
  flask create-superuser <username> <password>
  ```
- **List homes pending verification:**
  ```bash
  flask list-pending
  ```
- **Verify a home:**
  ```bash
  flask verify-home "<Home Name>"
  ```
- **Import homes from CSV:**
  ```bash
  flask import-homes homes_dataset.csv
  ```

---

## 🔑 Default Test Accounts

After running `python seed_db.py`, the following demo accounts are available:

| Role | Username | Password |
|---|---|---|
| **Home Admin** | `sunshine_admin` | `password123` |
| **Home Admin** | `golden_admin` | `password123` |
| **Donor** | `donor` (via `flask seed-db`) | `password` |

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome! Feel free to check the issues page or submit a Pull Request.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
