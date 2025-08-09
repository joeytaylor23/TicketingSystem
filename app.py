from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ticketing_system.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'uploads'))
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_LENGTH_MB', 16)) * 1024 * 1024  # 16 MB default

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'
mail = Mail(app)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')  # admin, technician, user
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Relationships
    created_tickets = db.relationship('Ticket', foreign_keys='Ticket.created_by_id', backref='creator', lazy='dynamic')
    assigned_tickets = db.relationship('Ticket', foreign_keys='Ticket.assigned_to_id', backref='assignee', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_technician(self):
        return self.role in ['admin', 'technician']

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    
    # Relationships
    tickets = db.relationship('Ticket', backref='category', lazy='dynamic')

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='open')  # open, in_progress, resolved, closed
    priority = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, urgent
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Foreign Keys
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    
    # Relationships
    activity_logs = db.relationship('ActivityLog', backref='ticket', lazy='dynamic', cascade='all, delete-orphan')

    # --- SLA helpers ---
    def get_sla_hours(self):
        priority_to_hours = {
            'low': 72,
            'medium': 48,
            'high': 24,
            'urgent': 8,
        }
        return priority_to_hours.get(self.priority, 48)

    def get_sla_due_at(self):
        return self.created_at + timedelta(hours=self.get_sla_hours()) if self.created_at else None

    def is_sla_active(self):
        return self.status in ['open', 'in_progress']

    def is_sla_breached(self):
        due = self.get_sla_due_at()
        if not due:
            return False
        if not self.is_sla_active():
            return False
        return datetime.now(timezone.utc) > due

    def get_sla_remaining_seconds(self):
        due = self.get_sla_due_at()
        if not due:
            return 0
        remaining = (due - datetime.now(timezone.utc)).total_seconds()
        return int(remaining)

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    action = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Foreign Keys
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    user = db.relationship('User', backref='activity_logs')

class Attachment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    stored_path = db.Column(db.String(500), nullable=False)
    content_type = db.Column(db.String(100))
    size_bytes = db.Column(db.Integer)
    uploaded_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Foreign Keys
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relationships
    ticket = db.relationship('Ticket', backref=db.backref('attachments', lazy='dynamic', cascade='all, delete-orphan'))
    uploaded_by = db.relationship('User')

# Utility functions
def send_notification_email(to_email, subject, body):
    """Send email notification"""
    try:
        if app.config['MAIL_USERNAME'] and app.config['MAIL_PASSWORD']:
            msg = Message(subject=subject, recipients=[to_email], body=body)
            mail.send(msg)
            return True
    except Exception as e:
        print(f"Failed to send email: {e}")
    return False

def log_activity(ticket_id, action, description, user_id=None):
    """Log activity for a ticket"""
    if user_id is None:
        user_id = current_user.id if current_user.is_authenticated else None
    
    if user_id:
        activity = ActivityLog(
            ticket_id=ticket_id,
            action=action,
            description=description,
            user_id=user_id
        )
        db.session.add(activity)
        db.session.commit()

def allowed_file(filename: str) -> bool:
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'txt', 'log'}
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in allowed_extensions

def check_and_handle_sla(ticket: 'Ticket') -> None:
    """If SLA is breached for this ticket, log once and notify admins/assignee."""
    try:
        if not ticket.is_sla_breached():
            return
        # Has this ticket already been escalated?
        already = ActivityLog.query.filter_by(ticket_id=ticket.id, action='SLA Escalated').first()
        if already:
            return
        # Log escalation
        log_activity(ticket.id, 'SLA Escalated', f'SLA breached for ticket {ticket.id}. Escalating.')
        # Notify admins and assigned technician
        recipients = []
        admins = User.query.filter_by(role='admin').all()
        recipients.extend([a.email for a in admins])
        if ticket.assignee:
            recipients.append(ticket.assignee.email)
        for email in set([r for r in recipients if r]):
            send_notification_email(
                email,
                f'SLA Breached: Ticket #{ticket.id} - {ticket.title}',
                'The SLA for this ticket has been breached. Please take immediate action.'
            )
    except Exception as e:
        print(f"SLA check error for ticket {ticket.id}: {e}")

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')
        
        # Validate role selection
        if role not in ['user', 'technician', 'admin']:
            role = 'user'
        
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('register.html')
        
        # Create new user
        user = User(username=username, email=email, role=role)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Get tickets based on user role
    if current_user.is_admin():
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    elif current_user.is_technician():
        tickets = Ticket.query.filter(
            (Ticket.assigned_to_id == current_user.id) | 
            (Ticket.assigned_to_id.is_(None))
        ).order_by(Ticket.created_at.desc()).all()
    else:
        tickets = Ticket.query.filter_by(created_by_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    
    # Get statistics
    total_tickets = len(tickets)
    open_tickets = len([t for t in tickets if t.status in ['open', 'in_progress']])
    closed_tickets = len([t for t in tickets if t.status in ['resolved', 'closed']])
    
    # Run SLA checks for visible tickets
    try:
        for t in tickets:
            if t.is_sla_active():
                check_and_handle_sla(t)
    except Exception as e:
        print(f"SLA dashboard check error: {e}")

    return render_template('dashboard.html', 
                         tickets=tickets, 
                         total_tickets=total_tickets,
                         open_tickets=open_tickets,
                         closed_tickets=closed_tickets)

@app.route('/create_ticket', methods=['GET', 'POST'])
@login_required
def create_ticket():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        priority = request.form['priority']
        category_id = request.form.get('category_id')
        
        ticket = Ticket(
            title=title,
            description=description,
            priority=priority,
            category_id=category_id if category_id else None,
            created_by_id=current_user.id
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        # Log activity
        log_activity(ticket.id, 'Created', f'Ticket created by {current_user.username}')
        
        # Send notification to technicians and admins
        technicians = User.query.filter(User.role.in_(['admin', 'technician'])).all()
        for tech in technicians:
            send_notification_email(
                tech.email,
                f'New Ticket Created: {title}',
                f'A new ticket has been created by {current_user.username}.\n\n'
                f'Title: {title}\n'
                f'Priority: {priority}\n'
                f'Description: {description}\n\n'
                f'Please log in to view and manage this ticket.'
            )
        
        flash('Ticket created successfully!')
        return redirect(url_for('dashboard'))
    
    categories = Category.query.all()
    return render_template('create_ticket.html', categories=categories)

@app.route('/ticket/<int:ticket_id>')
@login_required
def view_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check permissions
    if not current_user.is_technician() and ticket.created_by_id != current_user.id:
        flash('You do not have permission to view this ticket.')
        return redirect(url_for('dashboard'))
    
    activity_logs = ticket.activity_logs.order_by(ActivityLog.timestamp.desc()).all()
    # SLA check on view
    check_and_handle_sla(ticket)
    # Attachments
    attachments = ticket.attachments.order_by(Attachment.uploaded_at.desc()).all()
    technicians = User.query.filter(User.role.in_(['admin', 'technician'])).all()
    categories = Category.query.all()
    
    return render_template('view_ticket.html', 
                         ticket=ticket, 
                         activity_logs=activity_logs,
                         technicians=technicians,
                         categories=categories,
                         attachments=attachments)

@app.route('/update_ticket/<int:ticket_id>', methods=['POST'])
@login_required
def update_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    # Check permissions
    if not current_user.is_technician() and ticket.created_by_id != current_user.id:
        flash('You do not have permission to update this ticket.')
        return redirect(url_for('dashboard'))
    
    old_status = ticket.status
    old_assignee = ticket.assignee
    old_priority = ticket.priority
    
    # Update ticket fields
    if 'status' in request.form:
        ticket.status = request.form['status']
    
    if 'priority' in request.form and current_user.is_technician():
        ticket.priority = request.form['priority']
    
    if 'assigned_to_id' in request.form and current_user.is_technician():
        assigned_to_id = request.form['assigned_to_id']
        ticket.assigned_to_id = int(assigned_to_id) if assigned_to_id else None
    
    if 'category_id' in request.form and current_user.is_technician():
        category_id = request.form['category_id']
        ticket.category_id = int(category_id) if category_id else None
    
    db.session.commit()
    
    # Log changes
    changes = []
    if old_status != ticket.status:
        changes.append(f'Status changed from {old_status} to {ticket.status}')
        log_activity(ticket.id, 'Status Changed', f'Status updated to {ticket.status} by {current_user.username}')
    
    if old_assignee != ticket.assignee:
        assignee_name = ticket.assignee.username if ticket.assignee else 'Unassigned'
        changes.append(f'Assigned to {assignee_name}')
        log_activity(ticket.id, 'Assignment Changed', f'Ticket assigned to {assignee_name} by {current_user.username}')
    
    if old_priority != ticket.priority:
        changes.append(f'Priority changed to {ticket.priority}')
        log_activity(ticket.id, 'Priority Changed', f'Priority updated to {ticket.priority} by {current_user.username}')
    
    # Send notifications for significant changes
    if changes:
        # Notify ticket creator
        if ticket.creator.id != current_user.id:
            send_notification_email(
                ticket.creator.email,
                f'Ticket Updated: {ticket.title}',
                f'Your ticket has been updated.\n\n'
                f'Changes: {", ".join(changes)}\n\n'
                f'Updated by: {current_user.username}'
            )
        
        # Notify assigned technician
        if ticket.assignee and ticket.assignee.id != current_user.id:
            send_notification_email(
                ticket.assignee.email,
                f'Ticket Assigned: {ticket.title}',
                f'A ticket has been assigned to you.\n\n'
                f'Title: {ticket.title}\n'
                f'Priority: {ticket.priority}\n'
                f'Status: {ticket.status}\n'
                f'Assigned by: {current_user.username}'
            )
    
    flash('Ticket updated successfully!')
    return redirect(url_for('view_ticket', ticket_id=ticket_id))

@app.route('/ticket/<int:ticket_id>/upload', methods=['POST'])
@login_required
def upload_attachment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    # Permission check
    if not current_user.is_technician() and ticket.created_by_id != current_user.id:
        flash('You do not have permission to upload to this ticket.')
        return redirect(url_for('view_ticket', ticket_id=ticket_id))

    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('view_ticket', ticket_id=ticket_id))

    file = request.files['file']
    if file.filename == '':
        flash('No selected file')
        return redirect(url_for('view_ticket', ticket_id=ticket_id))

    if file and allowed_file(file.filename):
        from werkzeug.utils import secure_filename
        safe_name = secure_filename(file.filename)
        # Prefix with ticket and timestamp for uniqueness
        ts = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
        stored_name = f"t{ticket.id}_{ts}_{safe_name}"
        stored_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_name)
        file.save(stored_path)

        att = Attachment(
            filename=safe_name,
            stored_path=stored_path,
            content_type=file.mimetype,
            size_bytes=os.path.getsize(stored_path),
            ticket_id=ticket.id,
            uploaded_by_id=current_user.id,
        )
        db.session.add(att)
        db.session.commit()

        log_activity(ticket.id, 'Attachment Uploaded', f'{current_user.username} uploaded {safe_name}')
        flash('File uploaded successfully.')
    else:
        flash('Invalid file type. Allowed: png, jpg, jpeg, gif, pdf, txt, log')

    return redirect(url_for('view_ticket', ticket_id=ticket_id))

@app.route('/attachments/<int:attachment_id>/download')
@login_required
def download_attachment(attachment_id):
    att = Attachment.query.get_or_404(attachment_id)

    # Permission check: ticket creator or technician
    if not current_user.is_technician() and att.ticket.created_by_id != current_user.id:
        flash('You do not have permission to download this file.')
        return redirect(url_for('dashboard'))

    directory = os.path.dirname(att.stored_path)
    filename = os.path.basename(att.stored_path)
    return send_from_directory(directory, filename, as_attachment=True, download_name=att.filename)

@app.route('/attachments/<int:attachment_id>/delete', methods=['POST'])
@login_required
def delete_attachment(attachment_id):
    att = Attachment.query.get_or_404(attachment_id)
    ticket = att.ticket

    # Permission: technician/admin or ticket owner
    if not current_user.is_technician() and ticket.created_by_id != current_user.id:
        flash('You do not have permission to delete this file.')
        return redirect(url_for('view_ticket', ticket_id=ticket.id))

    try:
        if os.path.exists(att.stored_path):
            os.remove(att.stored_path)
    except Exception as e:
        print(f"Failed to remove file: {e}")

    db.session.delete(att)
    db.session.commit()
    log_activity(ticket.id, 'Attachment Deleted', f'{current_user.username} deleted {att.filename}')
    flash('Attachment deleted.')
    return redirect(url_for('view_ticket', ticket_id=ticket.id))

@app.route('/add_comment/<int:ticket_id>', methods=['POST'])
@login_required
def add_comment(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    comment = request.form['comment']
    
    # Check permissions
    if not current_user.is_technician() and ticket.created_by_id != current_user.id:
        flash('You do not have permission to comment on this ticket.')
        return redirect(url_for('dashboard'))
    
    # Log comment as activity
    log_activity(ticket.id, 'Comment Added', f'{current_user.username}: {comment}')
    
    # Notify relevant users
    recipients = []
    if ticket.creator.id != current_user.id:
        recipients.append(ticket.creator.email)
    if ticket.assignee and ticket.assignee.id != current_user.id:
        recipients.append(ticket.assignee.email)
    
    for email in set(recipients):  # Remove duplicates
        send_notification_email(
            email,
            f'New Comment on Ticket: {ticket.title}',
            f'A new comment has been added to your ticket.\n\n'
            f'Comment by {current_user.username}: {comment}\n\n'
            f'Ticket: {ticket.title}'
        )
    
    flash('Comment added successfully!')
    return redirect(url_for('view_ticket', ticket_id=ticket_id))

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin():
        flash('Access denied. Admin privileges required.')
        return redirect(url_for('dashboard'))
    
    users = User.query.all()
    categories = Category.query.all()

    # Basic analytics for charts (JSON endpoints also available if needed)
    priority_counts = {
        'urgent': Ticket.query.filter_by(priority='urgent').count(),
        'high': Ticket.query.filter_by(priority='high').count(),
        'medium': Ticket.query.filter_by(priority='medium').count(),
        'low': Ticket.query.filter_by(priority='low').count(),
    }
    status_counts = {
        'open': Ticket.query.filter_by(status='open').count(),
        'in_progress': Ticket.query.filter_by(status='in_progress').count(),
        'resolved': Ticket.query.filter_by(status='resolved').count(),
        'closed': Ticket.query.filter_by(status='closed').count(),
    }
    return render_template('admin.html', users=users, categories=categories, priority_counts=priority_counts, status_counts=status_counts)

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403

    try:
        range_param = request.args.get('range', 'week')
        days = 7 if range_param == 'week' else 30
        start_at = datetime.now(timezone.utc) - timedelta(days=days)

        # Ticket volume by day
        tickets_in_range = Ticket.query.filter(Ticket.created_at >= start_at).all()
        by_day = {}
        for t in tickets_in_range:
            day_str = t.created_at.date().isoformat()
            by_day[day_str] = by_day.get(day_str, 0) + 1
        # Fill missing days
        labels = []
        counts = []
        for i in range(days, -1, -1):
            d = (datetime.now(timezone.utc) - timedelta(days=i)).date().isoformat()
            labels.append(d)
            counts.append(by_day.get(d, 0))

        # Category counts in range
        category_stats = []
        for c in Category.query.all():
            count = Ticket.query.filter(Ticket.category_id == c.id, Ticket.created_at >= start_at).count()
            category_stats.append({'name': c.name, 'count': count})

        # Avg resolution time (tickets resolved/closed in range by update time)
        done = Ticket.query.filter(Ticket.status.in_(['resolved', 'closed']), Ticket.updated_at >= start_at).all()
        avg_resolution_hours = 0
        res_by_day_sum = {}
        res_by_day_count = {}
        if done:
            total_hours = 0
            for t in done:
                hours = max(0, (t.updated_at - t.created_at).total_seconds()) / 3600
                total_hours += hours
                day_key = t.updated_at.date().isoformat()
                res_by_day_sum[day_key] = res_by_day_sum.get(day_key, 0) + hours
                res_by_day_count[day_key] = res_by_day_count.get(day_key, 0) + 1
            avg_resolution_hours = total_hours / len(done)

        # Technician performance (tickets resolved/closed in range)
        tech_perf = {}
        for t in done:
            tech_id = t.assigned_to_id
            if tech_id is None:
                continue
            if tech_id not in tech_perf:
                u = User.query.get(tech_id)
                tech_perf[tech_id] = {
                    'user_id': tech_id,
                    'username': (u.username if u else f'User {tech_id}'),
                    'closed_count': 0,
                    'total_hours': 0.0,
                }
            tech_perf[tech_id]['closed_count'] += 1
            tech_perf[tech_id]['total_hours'] += max(0, (t.updated_at - t.created_at).total_seconds()) / 3600

        tech_list = []
        for v in tech_perf.values():
            avg_h = v['total_hours'] / v['closed_count'] if v['closed_count'] else 0
            tech_list.append({
                'username': v['username'],
                'closed_count': v['closed_count'],
                'avg_resolution_hours': avg_h,
            })

        # SLA breaches by day (based on ActivityLog 'SLA Escalated')
        sla_logs = ActivityLog.query.filter(
            ActivityLog.action == 'SLA Escalated',
            ActivityLog.timestamp >= start_at
        ).all()
        sla_by_day = {}
        for log in sla_logs:
            day_key = log.timestamp.date().isoformat()
            sla_by_day[day_key] = sla_by_day.get(day_key, 0) + 1

        # Build aligned day labels for trend series
        trend_labels = []
        res_avg_series = []
        sla_counts_series = []
        for i in range(days, -1, -1):
            day = (datetime.now(timezone.utc) - timedelta(days=i)).date().isoformat()
            trend_labels.append(day)
            # average resolution hours that day
            if res_by_day_count.get(day, 0) > 0:
                res_avg_series.append(round(res_by_day_sum.get(day, 0) / res_by_day_count.get(day, 1), 2))
            else:
                res_avg_series.append(0)
            sla_counts_series.append(sla_by_day.get(day, 0))

        return jsonify({
            'range': range_param,
            'volume_by_day': { 'labels': labels, 'counts': counts },
            'category_counts': category_stats,
            'avg_resolution_hours': round(avg_resolution_hours, 2),
            'technician_performance': tech_list,
            'resolution_trend': { 'labels': trend_labels, 'avg_hours': res_avg_series },
            'sla_breaches_by_day': { 'labels': trend_labels, 'counts': sla_counts_series },
        })
    except Exception as e:
        return jsonify({'error': f'Analytics failed: {str(e)}'}), 500

@app.route('/admin/create_category', methods=['POST'])
@login_required
def create_category():
    if not current_user.is_admin():
        flash('Access denied.')
        return redirect(url_for('dashboard'))
    
    name = request.form['name']
    description = request.form.get('description', '')
    
    if Category.query.filter_by(name=name).first():
        flash('Category already exists.')
    else:
        category = Category(name=name, description=description)
        db.session.add(category)
        db.session.commit()
        flash('Category created successfully!')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/update_user_role/<int:user_id>', methods=['POST'])
@login_required
def update_user_role(user_id):
    if not current_user.is_admin():
        flash('Access denied.')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    new_role = request.form['role']
    
    if new_role in ['user', 'technician', 'admin']:
        user.role = new_role
        db.session.commit()
        flash(f'User role updated to {new_role}.')
    else:
        flash('Invalid role specified.')
    
    return redirect(url_for('admin_panel'))

@app.route('/admin/export_data')
@login_required
def export_data():
    if not current_user.is_admin():
        flash('Access denied.')
        return redirect(url_for('dashboard'))
    
    try:
        import csv
        import io
        from flask import make_response
        
        # Create CSV data
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Export tickets data
        writer.writerow(['Ticket ID', 'Title', 'Status', 'Priority', 'Created By', 'Assigned To', 'Category', 'Created Date', 'Updated Date'])
        
        tickets = Ticket.query.all()
        for ticket in tickets:
            writer.writerow([
                ticket.id,
                ticket.title,
                ticket.status,
                ticket.priority,
                ticket.creator.username,
                ticket.assignee.username if ticket.assignee else 'Unassigned',
                ticket.category.name if ticket.category else 'None',
                ticket.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                ticket.updated_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        # Create response
        response = make_response(output.getvalue())
        response.headers['Content-Disposition'] = f'attachment; filename=medsupport_tickets_{datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")}.csv'
        response.headers['Content-type'] = 'text/csv'
        
        return response
        
    except Exception as e:
        flash(f'Export failed: {str(e)}')
        return redirect(url_for('admin_panel'))

@app.route('/admin/generate_report')
@login_required
def generate_report():
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Generate comprehensive system report
        total_tickets = Ticket.query.count()
        total_users = User.query.count()
        
        # Ticket statistics
        open_tickets = Ticket.query.filter(Ticket.status.in_(['open', 'in_progress'])).count()
        closed_tickets = Ticket.query.filter(Ticket.status.in_(['resolved', 'closed'])).count()
        
        # Priority breakdown
        urgent_tickets = Ticket.query.filter_by(priority='urgent').count()
        high_tickets = Ticket.query.filter_by(priority='high').count()
        medium_tickets = Ticket.query.filter_by(priority='medium').count()
        low_tickets = Ticket.query.filter_by(priority='low').count()
        
        # User role breakdown
        admins = User.query.filter_by(role='admin').count()
        technicians = User.query.filter_by(role='technician').count()
        users = User.query.filter_by(role='user').count()
        
        # Recent activity (last 7 days)
        from datetime import timedelta
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        recent_tickets = Ticket.query.filter(Ticket.created_at >= week_ago).count()
        recent_activity = ActivityLog.query.filter(ActivityLog.timestamp >= week_ago).count()
        
        # Category breakdown
        categories = Category.query.all()
        category_stats = []
        for category in categories:
            category_stats.append({
                'name': category.name,
                'count': category.tickets.count()
            })
        
        # Average resolution time (simplified)
        resolved_tickets = Ticket.query.filter(Ticket.status.in_(['resolved', 'closed'])).all()
        avg_resolution_hours = 0
        if resolved_tickets:
            total_hours = 0
            for ticket in resolved_tickets:
                hours = (ticket.updated_at - ticket.created_at).total_seconds() / 3600
                total_hours += hours
            avg_resolution_hours = total_hours / len(resolved_tickets)
        
        report_data = {
            'generated_at': datetime.now(timezone.utc).isoformat(),
            'system_overview': {
                'total_tickets': total_tickets,
                'total_users': total_users,
                'open_tickets': open_tickets,
                'closed_tickets': closed_tickets,
                'avg_resolution_hours': round(avg_resolution_hours, 2)
            },
            'weekly': {
                'new_tickets': Ticket.query.filter(Ticket.created_at >= week_ago).count(),
            },
            'priority_breakdown': {
                'urgent': urgent_tickets,
                'high': high_tickets,
                'medium': medium_tickets,
                'low': low_tickets
            },
            'user_roles': {
                'admins': admins,
                'technicians': technicians,
                'users': users
            },
            'recent_activity': {
                'new_tickets_last_week': recent_tickets,
                'total_activities_last_week': recent_activity
            },
            'categories': category_stats
        }
        
        return jsonify(report_data)
        
    except Exception as e:
        return jsonify({'error': f'Report generation failed: {str(e)}'}), 500

@app.route('/admin/system_health')
@login_required
def system_health():
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        import os
        import psutil
        
        # Database health
        db_status = 'healthy'
        try:
            db.session.execute('SELECT 1')
            db_status = 'healthy'
        except Exception:
            db_status = 'error'
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        
        # Try different disk paths for Windows compatibility
        disk = None
        try:
            disk = psutil.disk_usage('C:')
        except:
            try:
                disk = psutil.disk_usage('/')
            except:
                # Fallback with default values
                disk = type('DiskUsage', (), {
                    'percent': 0,
                    'used': 0,
                    'total': 1
                })()
        
        # Application health
        total_tickets = Ticket.query.count()
        total_users = User.query.count()
        
        # Check for any urgent issues
        urgent_tickets = Ticket.query.filter_by(priority='urgent', status='open').count()
        
        health_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': 'healthy' if db_status == 'healthy' and cpu_percent < 80 else 'warning',
            'database': {
                'status': db_status,
                'total_tickets': total_tickets,
                'total_users': total_users
            },
            'system_resources': {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_used_gb': round(memory.used / (1024**3), 2),
                'memory_total_gb': round(memory.total / (1024**3), 2),
                'disk_percent': disk.percent,
                'disk_used_gb': round(disk.used / (1024**3), 2),
                'disk_total_gb': round(disk.total / (1024**3), 2)
            },
            'application_metrics': {
                'urgent_open_tickets': urgent_tickets,
                'total_categories': Category.query.count(),
                'recent_activity_count': ActivityLog.query.filter(
                    ActivityLog.timestamp >= datetime.now(timezone.utc) - timedelta(hours=24)
                ).count()
            }
        }
        
        return jsonify(health_data)
        
    except Exception as e:
        import traceback
        print(f"System health error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': f'Health check failed: {str(e)}'}), 500

@app.route('/admin/clear_cache', methods=['POST'])
@login_required
def clear_cache():
    if not current_user.is_admin():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Clear old activity logs (older than 90 days)
        from datetime import timedelta
        ninety_days_ago = datetime.now(timezone.utc) - timedelta(days=90)
        
        old_logs = ActivityLog.query.filter(ActivityLog.timestamp < ninety_days_ago).all()
        log_count = len(old_logs)
        
        for log in old_logs:
            db.session.delete(log)
        
        # Clear any temporary data or sessions (if implemented)
        # This is a placeholder for additional cache clearing logic
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Cache cleared successfully. Removed {log_count} old activity logs.',
            'cleared_items': {
                'old_activity_logs': log_count
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Cache clearing failed: {str(e)}'}), 500

# Initialize database
def init_db():
    """Initialize database with sample data"""
    db.create_all()
    
    # Create default categories if they don't exist
    default_categories = [
        ('Hardware', 'Hardware-related issues'),
        ('Software', 'Software-related issues'),
        ('Network', 'Network and connectivity issues'),
        ('Account', 'User account and access issues'),
        ('Other', 'Other miscellaneous issues')
    ]
    
    for name, description in default_categories:
        if not Category.query.filter_by(name=name).first():
            category = Category(name=name, description=description)
            db.session.add(category)
    
    # Create default admin user if no users exist
    if not User.query.first():
        admin = User(
            username='admin',
            email='admin@example.com',
            role='admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # Create a technician user
        tech = User(
            username='technician',
            email='tech@example.com',
            role='technician'
        )
        tech.set_password('tech123')
        db.session.add(tech)
        
        # Create a regular user
        user = User(
            username='user',
            email='user@example.com',
            role='user'
        )
        user.set_password('user123')
        db.session.add(user)
    
    db.session.commit()

if __name__ == '__main__':
    with app.app_context():
        init_db()
    # Production settings
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)