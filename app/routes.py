# app/routes.py
# app/routes.py
import logging
import io
import csv
import qrcode
from flask import render_template, flash, redirect, url_for, request, Blueprint, send_file, current_app, jsonify, make_response
from flask_login import current_user, login_user, logout_user, login_required
from app import db
from app.models import User, Home, Donation, Reward, Notification, VolunteerOpportunity, volunteer_applications
from app.forms import LoginForm, UserRegistrationForm, HomeAdminRegistrationForm, HomeUpdateForm, MoneyDonationForm, InKindDonationForm, VolunteerOpportunityForm
from sqlalchemy import or_
from sqlalchemy import func
from functools import wraps
from datetime import datetime, timedelta
from urllib.parse import quote_plus

bp = Blueprint('routes', __name__)

def role_required(role):
    """Decorator to restrict access to a route to a specific role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated or current_user.role != role:
                flash('Access denied for this page.', 'danger')
                # Redirect to the appropriate dashboard based on role
                if current_user.is_authenticated:
                    if current_user.role == 'home_admin':
                        return redirect(url_for('routes.home_dashboard'))
                    else:
                        return redirect(url_for('routes.index'))
                return redirect(url_for('routes.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def init_app(app):
    app.register_blueprint(bp)

    @app.context_processor
    def inject_notifications():
        if current_user.is_authenticated:
            unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
            latest_notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).limit(5).all()
            return dict(unread_notifications=unread_notifications, latest_notifications=latest_notifications)
        return dict(unread_notifications=0, latest_notifications=[])

@bp.route('/')
@bp.route('/index')
@login_required
def index():
    """Donor dashboard. Redirects home admins away."""
    if current_user.role == 'home_admin':
        return redirect(url_for('routes.home_dashboard'))
    if current_user.role == 'superuser':
        return redirect(url_for('routes.superuser_dashboard'))
    
    search_query = request.args.get('search', '')
    if search_query:
        search_term = f"%{search_query}%"
        all_homes = Home.query.filter(
            Home.is_verified == True,
            or_(
                Home.name.ilike(search_term),
                Home.address.ilike(search_term)
            )
        ).all()
    else:
        all_homes = Home.query.filter_by(is_verified=True).all()
        
    return render_template('index.html', title='Donor Dashboard', all_homes=all_homes, search_query=search_query)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Unified login for both user roles."""
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter((User.username == form.username.data) | (User.email == form.username.data)).first()
        
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password.', 'danger')
            return redirect(url_for('routes.login'))
        
        login_user(user, remember=form.remember_me.data)
        
        # Redirect based on role
        if user.role == 'home_admin':
            return redirect(url_for('routes.home_dashboard'))
        elif user.role == 'superuser':
            return redirect(url_for('routes.superuser_dashboard'))
        else:
            return redirect(url_for('routes.index'))
            
    return render_template('login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('routes.login'))

@bp.route('/register')
def register():
    """Main registration hub page."""
    return render_template('register.html', title='Register')

@bp.route('/register/user', methods=['GET', 'POST'])
def register_user():
    """Handles registration for new donors."""
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    form = UserRegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            role='donor'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Welcome! You are now a registered donor.', 'success')
        login_user(user)
        return redirect(url_for('routes.index'))
    return render_template('register_user.html', title='User Registration', form=form)

@bp.route('/register/home', methods=['GET', 'POST'])
def register_home():
    """Handles registration for new home admins and their homes."""
    if current_user.is_authenticated:
        return redirect(url_for('routes.index'))
    form = HomeAdminRegistrationForm()
    if form.validate_on_submit():
        # Create the Home Admin User
        user = User(
            username=form.username.data,
            email=form.email.data,
            phone_number=form.phone_number.data,
            role='home_admin'
        )
        user.set_password(form.password.data)
        home = Home(
            name=form.home_name.data,
            address=form.home_address.data,
            description=form.home_description.data,
            occupant_count=form.home_occupant_count.data,
            contact_phone=form.home_contact_phone.data,
            payment_details=form.home_payment_details.data,
            admin=user  # This links the home to the user
        )
        db.session.commit()
        
        flash('Account created! Your home profile is currently pending verification by the platform administrator.', 'warning')
        login_user(user)
        return redirect(url_for('routes.home_dashboard'))
    return render_template('register_home.html', title='Home Admin Registration', form=form)

@bp.route('/home/<int:home_id>')
def home_detail(home_id):
    """Shows details for a specific home, including requirements."""
    home = Home.query.get_or_404(home_id)
    
    # Prevent donors from seeing unverified homes
    if not home.is_verified and (not current_user.is_authenticated or current_user.role != 'home_admin' or home.admin_id != current_user.id):
        flash('This home is currently under verification and cannot be viewed.', 'warning')
        return redirect(url_for('routes.index'))
        
    money_form = MoneyDonationForm()
    inkind_form = InKindDonationForm()
    return render_template('home_detail.html', title=home.name, home=home, money_form=money_form, inkind_form=inkind_form)

@bp.route('/donate/money', methods=['POST'])
@login_required
@role_required('donor')
def donate_money():
    """Handles monetary donations with transaction ID validation."""
    form = MoneyDonationForm()
    if form.validate_on_submit():
        # Check for duplicate transaction ID
        if Donation.query.filter_by(transaction_id=form.transaction_id.data).first():
            flash('This Transaction ID has already been recorded.', 'danger')
            return redirect(request.referrer or url_for('routes.index'))

        home_id = form.home_id.data
        home = Home.query.get_or_404(home_id)
        desc = form.description.data or "Monetary Donation"
        donation = Donation(description=desc, amount=form.amount.data, transaction_id=form.transaction_id.data, donor=current_user, home=home)
        db.session.add(donation)
        db.session.commit()
        
        flash(f"Thank you! Your donation of ₹{form.amount.data} has been recorded. Please wait for admin confirmation.", 'success')
        return redirect(url_for('routes.impact_tracker'))
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(request.referrer or url_for('routes.index'))

@bp.route('/donate/inkind', methods=['POST'])
@login_required
@role_required('owner')
def donate_inkind():
    """Handles in-kind donations."""
    form = InKindDonationForm()
    if form.validate_on_submit():
        home_id = form.home_id.data
        home = Home.query.get_or_404(home_id)
        donation = Donation(description=form.description.data, amount=0, donor=current_user, home=home)
        db.session.add(donation)
        db.session.commit()
        
        flash("Thank you! Your in-kind donation has been recorded.", 'success')
        return redirect(url_for('routes.impact_tracker'))
    
    for field, errors in form.errors.items():
        for error in errors:
            flash(f"Error in {getattr(form, field).label.text}: {error}", 'danger')
    return redirect(request.referrer or url_for('routes.index'))

@bp.route('/leaderbard')
@login_required
@role_required('donor')
def leaderboard():
    """Shows the leaderboard of top donors, excluding home admins."""
    top_donors = User.query.filter_by(role='donor').order_by(User.points.desc()).limit(10).all()
    return render_template('leaderboard.html', title='Leaderboard', donors=top_donors)

@bp.route('/user/<username>')
@login_required
def user_profile(username):
    """Shows a user's public profile page."""
    user = User.query.filter_by(username=username).first_or_404()
    if user.role != 'donor':
        # We don't want to show profiles for home admins
        from flask import abort
        abort(404)
    
    donations = Donation.query.filter_by(donor=user).order_by(Donation.timestamp.desc()).limit(5).all()
    total_donated = db.session.query(func.sum(Donation.amount)).filter_by(donor_id=user.id).scalar() or 0
    
    return render_template('user_profile.html', title=f"{user.username}'s Profile", user=user, donations=donations, total_donated=total_donated)

@bp.route('/impact')
@login_required
@role_required('donor')
def impact_tracker():
    """Shows a donor their personal donation history."""
    donations = Donation.query.filter_by(donor=current_user).order_by(Donation.timestamp.desc()).all()
    total_donated = sum(d.amount or 0 for d in donations)
    return render_template('impact_tracker.html', title='My Impact', donations=donations, total_donated=total_donated)

@bp.route('/rewards', methods=['GET', 'POST'])
@login_required
@role_required('donor')
def rewards():
    """Displays rewards and handles redemption."""
    if request.method == 'POST':
        reward_id = request.form.get('reward_id')
        reward = Reward.query.get(reward_id)
        if reward and current_user.points >= reward.points_cost:
            current_user.points -= reward.points_cost
            current_user.redeemed.append(reward)
            db.session.commit()
            flash(f'Congratulations! You have successfully redeemed "{reward.name}"!', 'success')
        elif not reward:
            flash('Invalid reward selected.', 'danger')
        else:
            flash('You do not have enough points to redeem this reward.', 'danger')
        return redirect(url_for('routes.rewards'))
        
    all_rewards = Reward.query.order_by(Reward.points_cost).all()
    return render_template('rewards.html', title='Rewards Store', rewards=all_rewards)

@bp.route('/home/dashboard')
@login_required
@role_required('home_admin')
def home_dashboard():
    """Dashboard for the logged-in home administrator."""
    home = current_user.home
    if not home:
        flash('No home is associated with this admin account.', 'danger')
        return redirect(url_for('routes.logout'))
    donations = Donation.query.filter_by(home=home).order_by(Donation.timestamp.desc()).all()
    total_received = sum(d.amount or 0 for d in donations)
    return render_template('home_dashboard.html', title='Home Dashboard', home=home, donations=donations, total_received=total_received)

@bp.route('/home/edit', methods=['GET', 'POST'])
@login_required
@role_required('home_admin')
def home_edit():
    """Allows a home admin to edit their home's details and requirements."""
    home = current_user.home
    if not home:
        flash('No home is associated with this admin account.', 'danger')
        return redirect(url_for('routes.home_dashboard'))
    
    form = HomeUpdateForm(obj=home)
    if form.validate_on_submit():
        form.populate_obj(home)
        flash('Your home details have been updated successfully!', 'success')
        db.session.commit()
        return redirect(url_for('routes.home_dashboard'))
    
    return render_template('home_edit.html', title='Edit Home Details', form=form, home=home)

@bp.route('/donation/<int:donation_id>/confirm', methods=['POST'])
@login_required
@role_required('home_admin')
def confirm_donation(donation_id):
    """Allows a home admin to confirm receipt of a donation."""
    donation = Donation.query.get_or_404(donation_id)
    
    # Ensure the admin is confirming for their own home
    if donation.home.admin_id != current_user.id:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('routes.home_dashboard'))

    if not donation.confirmed:
        donation.confirmed = True
        donation.confirmed_on = datetime.utcnow()
        donation.thank_you_message = request.form.get('thank_you_message')
        
        # Create a notification for the donor
        message = f"Your donation of '{donation.description}' to {donation.home.name} has been received and confirmed. Thank you!"
        
        # Award points upon confirmation
        donation.donor.points += 10
        notification = Notification(message=message, user_id=donation.donor_id, link=url_for('routes.impact_tracker'))
        db.session.add(notification)

        db.session.commit()
        flash(f"Donation from {donation.donor.username} confirmed successfully.", 'success')
    
    return redirect(url_for('routes.home_dashboard'))

@bp.route('/donation/<int:donation_id>/reject', methods=['POST'])
@login_required
@role_required('home_admin')
def reject_donation(donation_id):
    """Allows a home admin to reject a donation (e.g., fake transaction ID)."""
    donation = Donation.query.get_or_404(donation_id)
    
    # Ensure the admin is confirming for their own home
    if donation.home.admin_id != current_user.id:
        flash('You do not have permission to perform this action.', 'danger')
        return redirect(url_for('routes.home_dashboard'))

    if not donation.confirmed:
        # Create a notification for the donor explaining the rejection
        message = f"Your donation of '{donation.description}' to {donation.home.name} was rejected. The Transaction ID could not be verified."
        notification = Notification(message=message, user_id=donation.donor_id, link=url_for('routes.impact_tracker'))
        db.session.add(notification)
        
        db.session.delete(donation)
        db.session.commit()
        flash(f"Donation from {donation.donor.username} has been rejected and removed.", 'warning')
    
    return redirect(url_for('routes.home_dashboard'))

@bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notifications_read():
    """Marks all of the user's unread notifications as read."""
    try:
        Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
        db.session.commit()
        return ({'status': 'success'}, 200)
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error marking notifications as read for user {current_user.id}: {e}")
        return ({'status': 'error', 'message': 'Could not update notifications.'}, 500)

# --- Volunteer Feature Routes ---

@bp.route('/volunteer')
@login_required
@role_required('donor')
def volunteer_opportunities():
    """Displays a list of all open volunteer opportunities."""
    opportunities = VolunteerOpportunity.query.filter_by(status='open').order_by(VolunteerOpportunity.posted_on.desc()).all()
    return render_template('volunteer_opportunities.html', title='Volunteer Opportunities', opportunities=opportunities)

@bp.route('/volunteer/<int:opportunity_id>/apply', methods=['POST'])
@login_required
@role_required('donor')
def apply_for_opportunity(opportunity_id):
    """Handles a donor's application for a volunteer role."""
    opportunity = VolunteerOpportunity.query.get_or_404(opportunity_id)
    if opportunity in current_user.applied_opportunities:
        flash('You have already applied for this opportunity.', 'info')
    else:
        current_user.applied_opportunities.append(opportunity)
        db.session.commit()
        flash(f'Your application for "{opportunity.title}" has been sent! The home will be in touch.', 'success')
    return redirect(url_for('routes.volunteer_opportunities'))

@bp.route('/home/volunteer/new', methods=['GET', 'POST'])
@login_required
@role_required('home_admin')
def create_volunteer_opportunity():
    """Allows a home admin to create a new volunteer opportunity."""
    form = VolunteerOpportunityForm()
    if form.validate_on_submit():
        opportunity = VolunteerOpportunity(
            title=form.title.data,
            description=form.description.data,
            skills_required=form.skills_required.data,
            time_commitment=form.time_commitment.data,
            home=current_user.home
        )
        db.session.add(opportunity)
        db.session.commit()
        flash('New volunteer opportunity has been posted successfully!', 'success')
        return redirect(url_for('routes.home_dashboard'))
    return render_template('create_volunteer_opportunity.html', title='Post New Volunteer Opportunity', form=form)

@bp.route('/home/volunteer/<int:opportunity_id>/edit', methods=['GET', 'POST'])
@login_required
@role_required('home_admin')
def edit_volunteer_opportunity(opportunity_id):
    """Allows a home admin to edit their volunteer opportunity."""
    opportunity = VolunteerOpportunity.query.get_or_404(opportunity_id)
    if opportunity.home_id != current_user.home.id:
        flash('You do not have permission to edit this opportunity.', 'danger')
        return redirect(url_for('routes.home_dashboard'))

    form = VolunteerOpportunityForm(obj=opportunity)
    if form.validate_on_submit():
        opportunity.title = form.title.data
        opportunity.description = form.description.data
        opportunity.skills_required = form.skills_required.data
        opportunity.time_commitment = form.time_commitment.data
        db.session.commit()
        flash('The volunteer opportunity has been updated.', 'success')
        return redirect(url_for('routes.home_dashboard'))
    
    return render_template('edit_volunteer_opportunity.html', title='Edit Volunteer Opportunity', form=form)

@bp.route('/home/volunteer/<int:opportunity_id>/close', methods=['POST'])
@login_required
@role_required('home_admin')
def close_volunteer_opportunity(opportunity_id):
    """Allows a home admin to close a volunteer opportunity."""
    opportunity = VolunteerOpportunity.query.get_or_404(opportunity_id)
    if opportunity.home_id == current_user.home.id:
        opportunity.status = 'closed'
        db.session.commit()
        flash(f'The opportunity "{opportunity.title}" has been closed.', 'success')
    return redirect(url_for('routes.home_dashboard'))

@bp.route('/home/applications')
@login_required
@role_required('home_admin')
def view_applications():
    """Shows a home admin all applicants for their volunteer opportunities."""
    # This query is a bit more complex to get all applications for a home's opportunities
    applications = db.session.query(volunteer_applications).join(
        VolunteerOpportunity, volunteer_applications.c.opportunity_id == VolunteerOpportunity.id
    ).filter(
        VolunteerOpportunity.home_id == current_user.home.id
    ).order_by(volunteer_applications.c.applied_on.desc()).all()

    # We need to get the user and opportunity objects for the template
    application_details = []
    for app in applications:
        user = User.query.get(app.user_id)
        opportunity = VolunteerOpportunity.query.get(app.opportunity_id)
        application_details.append({
            'user': user,
            'opportunity': opportunity,
            'status': app.status,
            'applied_on': app.applied_on
        })
    return render_template('view_applications.html', title='Volunteer Applicants', applications=application_details)

@bp.route('/home/application/<int:user_id>/<int:opportunity_id>/update', methods=['POST'])
@login_required
@role_required('home_admin')
def update_application_status(user_id, opportunity_id):
    """Updates the status of a volunteer application (accept/reject)."""
    new_status = request.form.get('status')
    if new_status not in ['accepted', 'rejected']:
        flash('Invalid status update.', 'danger')
        return redirect(url_for('routes.view_applications'))

    # The statement to update the table
    stmt = volunteer_applications.update().where(
        volunteer_applications.c.user_id == user_id,
        volunteer_applications.c.opportunity_id == opportunity_id
    ).values(status=new_status)

    db.session.execute(stmt)

    # Create a notification for the volunteer
    user = User.query.get(user_id)
    opportunity = VolunteerOpportunity.query.get(opportunity_id)
    
    # Ensure the admin has permission for this opportunity
    if opportunity.home_id != current_user.home.id:
        flash('You do not have permission to modify this application.', 'danger')
        db.session.rollback()
        return redirect(url_for('routes.view_applications'))

    if new_status == 'accepted':
        message = f"Great news! Your application for '{opportunity.title}' has been accepted. The home will contact you soon."
        flash(f"You have accepted {user.username}'s application.", 'success')
    else: # rejected
        message = f"Update on your application for '{opportunity.title}': The position has been filled. Thank you for your interest!"
        flash(f"You have rejected {user.username}'s application.", 'info')

    notification = Notification(message=message, user_id=user_id, link=url_for('routes.volunteer_opportunities'))
    db.session.add(notification)
    db.session.commit()
    return redirect(url_for('routes.view_applications'))

@bp.route('/qr_code/<int:home_id>')
def generate_qr(home_id):
    """Generates a QR code for the home's payment details."""
    home = Home.query.get_or_404(home_id)
    
    if not home.payment_details:
        return "No payment details provided", 404
        
    # Construct UPI URL: upi://pay?pa=<upi_id>&pn=<name>&cu=INR
    # We encode the name to handle spaces correctly
    upi_url = f"upi://pay?pa={home.payment_details.strip()}&pn={quote_plus(home.name)}&cu=INR"
    
    img = qrcode.make(upi_url)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@bp.route('/superuser')
@login_required
@role_required('superuser')
def superuser_dashboard():
    """Dashboard for the superuser to manage homes."""
    pending_homes = Home.query.filter_by(is_verified=False).all()
    return render_template('superuser_dashboard.html', title='Superuser Dashboard', homes=pending_homes)

@bp.route('/superuser/verify/<int:home_id>', methods=['POST'])
@login_required
@role_required('superuser')
def verify_home_web(home_id):
    """Verifies a home via the web interface."""
    home = Home.query.get_or_404(home_id)
    home.is_verified = True
    db.session.commit()
    flash(f"Home '{home.name}' has been verified successfully.", 'success')
    return redirect(url_for('routes.superuser_dashboard'))

@bp.route('/superuser/reject/<int:home_id>', methods=['POST'])
@login_required
@role_required('superuser')
def reject_home_web(home_id):
    """Rejects and deletes a home via the web interface."""
    home = Home.query.get_or_404(home_id)
    name = home.name
    
    # Clean up related data to prevent foreign key errors
    VolunteerOpportunity.query.filter_by(home_id=home.id).delete()
    Donation.query.filter_by(home_id=home.id).delete()
    
    db.session.delete(home)
    db.session.commit()
    flash(f"Home '{name}' has been rejected and deleted.", 'danger')
    return redirect(url_for('routes.superuser_dashboard'))

@bp.route('/superuser/stats')
@login_required
@role_required('superuser')
def superuser_stats():
    """Returns JSON statistics for the superuser dashboard."""
    verified_count = Home.query.filter_by(is_verified=True).count()
    pending_count = Home.query.filter_by(is_verified=False).count()
    return jsonify({
        'verified': verified_count,
        'pending': pending_count
    })

@bp.route('/superuser/export_homes')
@login_required
@role_required('superuser')
def export_homes_csv():
    """Exports a list of all homes to CSV."""
    homes = Home.query.all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Name', 'Address', 'Contact', 'Occupants', 'Verified', 'Admin Username', 'Admin Email'])
    for home in homes:
        cw.writerow([home.id, home.name, home.address, home.contact_phone, home.occupant_count, home.is_verified, home.admin.username, home.admin.email])
    
    output = make_response(si.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=homes_report.csv"
    output.headers["Content-type"] = "text/csv"
    return output

@bp.route('/donation/<int:donation_id>/receipt')
@login_required
@role_required('donor')
def view_receipt(donation_id):
    """Generates a printable receipt for a confirmed donation."""
    donation = Donation.query.get_or_404(donation_id)
    if donation.donor_id != current_user.id:
        flash('You do not have permission to view this receipt.', 'danger')
        return redirect(url_for('routes.impact_tracker'))
    
    if not donation.confirmed:
        flash('Receipts are only available for confirmed donations.', 'warning')
        return redirect(url_for('routes.impact_tracker'))
    
    return render_template('receipt.html', donation=donation)
