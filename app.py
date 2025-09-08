from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv
import uuid
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import hashlib
import time

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Permission System
PERMISSIONS = {
    # User Management
    'manage_users': 'Create, edit, and delete user accounts',
    'view_users': 'View list of all users',

    # Inventory Management
    'manage_inventory': 'Add, edit, and delete inventory items',
    'view_inventory': 'View inventory items and stock levels',

    # Sales Operations
    'process_sales': 'Process customer sales and transactions',
    'view_sales': 'View sales data and reports',

    # Dashboard Access
    'view_dashboard': 'Access main dashboard with metrics',

    # Profile Management
    'manage_own_profile': 'Change own password and settings',

    # System Administration
    'system_admin': 'Full system administration access',
}

# Role-based permissions
ROLE_PERMISSIONS = {
    'admin': [
        'manage_users', 'view_users',
        'manage_inventory', 'view_inventory',
        'process_sales', 'view_sales',
        'view_dashboard',
        'manage_own_profile',
        'system_admin'
    ],
    'cashier': [
        'view_inventory',
        'process_sales', 'view_sales',
        'view_dashboard',
        'manage_own_profile'
    ]
}

def has_permission(user, permission):
    """Check if user has a specific permission"""
    if not user or not user.is_authenticated:
        return False

    user_permissions = ROLE_PERMISSIONS.get(user.role, [])
    return permission in user_permissions

def get_user_permissions(user):
    """Get all permissions for a user"""
    if not user or not user.is_authenticated:
        return []

    return ROLE_PERMISSIONS.get(user.role, [])

def get_role_permissions(role):
    """Get all permissions for a role"""
    return ROLE_PERMISSIONS.get(role, [])

def get_all_permissions():
    """Get all available permissions"""
    return PERMISSIONS

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'cashier'
    secret_question = db.Column(db.String(200), nullable=True)
    secret_answer = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def has_permission(self, permission):
        """Check if user has a specific permission"""
        return has_permission(self, permission)

    def get_permissions(self):
        """Get all permissions for this user"""
        return get_user_permissions(self)

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship with items
    items = db.relationship('Item', backref='category', lazy=True)

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    barcode = db.Column(db.String(50), unique=True, nullable=False)
    sold_quantity = db.Column(db.Integer, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def status(self):
        """Determine item status based on quantity"""
        if self.quantity == 0:
            return "Out of Stock"
        elif self.quantity <= 5:
            return "Low Stock"
        else:
            return "In Stock"

    @property
    def is_expired(self):
        """Check if item is expired"""
        if self.expiry_date:
            return self.expiry_date < datetime.now(timezone.utc).date()
        return False

    @property
    def days_until_expiry(self):
        """Calculate days until expiry"""
        if self.expiry_date:
            today = datetime.now(timezone.utc).date()
            delta = self.expiry_date - today
            return delta.days
        return None

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    discount_percent = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    final_amount = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)
    receipt_number = db.Column(db.String(20), unique=True, nullable=False)
    cash_received = db.Column(db.Float, nullable=True)
    change_amount = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship('User', backref=db.backref('sales', lazy=True))
    items = db.relationship('SaleItem', backref='sale', lazy=True)

class SaleItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)

    item = db.relationship('Item', backref=db.backref('sale_items', lazy=True))

class Branding(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # App Branding
    app_name = db.Column(db.String(100), nullable=False, default='POS System')
    app_subtitle = db.Column(db.String(200), nullable=True, default='Professional Point of Sale')

    # Business Information
    business_name = db.Column(db.String(200), nullable=True)
    business_address = db.Column(db.String(500), nullable=True)
    business_phone = db.Column(db.String(50), nullable=True)
    business_email = db.Column(db.String(100), nullable=True)
    tax_id = db.Column(db.String(50), nullable=True)

    # Theme Colors
    primary_color = db.Column(db.String(7), nullable=False, default='#6366f1')  # Hex color
    secondary_color = db.Column(db.String(7), nullable=False, default='#8b5cf6')
    accent_color = db.Column(db.String(7), nullable=False, default='#10b981')
    background_color = db.Column(db.String(7), nullable=False, default='#ffffff')
    text_color = db.Column(db.String(7), nullable=False, default='#1f2937')

    # Logo and Assets
    logo_url = db.Column(db.String(500), nullable=True)
    favicon_url = db.Column(db.String(500), nullable=True)

    # Typography
    font_family = db.Column(db.String(100), nullable=False, default='Inter')

    # Footer Text
    footer_text = db.Column(db.String(500), nullable=True, default='Thank you for your business!')

    # Receipt Settings
    receipt_return_policy = db.Column(db.String(500), nullable=True, default='For exchanges/returns, present this receipt within 30 days.')

    # Receipt Labels and Text
    receipt_header_title = db.Column(db.String(100), nullable=True, default='RECEIPT')
    receipt_number_label = db.Column(db.String(50), nullable=True, default='Receipt #:')
    date_label = db.Column(db.String(50), nullable=True, default='Date:')
    cashier_label = db.Column(db.String(50), nullable=True, default='Cashier:')
    payment_method_label = db.Column(db.String(50), nullable=True, default='Payment Method:')
    cash_received_label = db.Column(db.String(50), nullable=True, default='Cash Received:')
    change_label = db.Column(db.String(50), nullable=True, default='Change:')
    currency_symbol = db.Column(db.String(10), nullable=True, default='AFA')
    item_header = db.Column(db.String(50), nullable=True, default='Item')
    quantity_header = db.Column(db.String(50), nullable=True, default='Qty')
    amount_header = db.Column(db.String(50), nullable=True, default='Amount')
    subtotal_label = db.Column(db.String(50), nullable=True, default='Subtotal:')
    discount_label = db.Column(db.String(50), nullable=True, default='Discount')
    total_label = db.Column(db.String(50), nullable=True, default='TOTAL:')
    records_message = db.Column(db.String(200), nullable=True, default='Please keep this receipt for your records.')
    powered_by_label = db.Column(db.String(50), nullable=True, default='Powered by')
    version_text = db.Column(db.String(20), nullable=True, default='v1.0')

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))



class LoginAttempt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.String(500), nullable=True)
    attempt_time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    success = db.Column(db.Boolean, default=False)
    failure_reason = db.Column(db.String(100), nullable=True)
    captcha_required = db.Column(db.Boolean, default=False)
    captcha_solved = db.Column(db.Boolean, default=False)
    session_id = db.Column(db.String(100), nullable=True)
    location = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<LoginAttempt {self.id}: {self.username}@{self.ip_address} - {"Success" if self.success else "Failed"}>'

class BlockedIP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(45), unique=True, nullable=False)
    blocked_until = db.Column(db.DateTime, nullable=True)
    block_reason = db.Column(db.String(200), nullable=True)
    failed_attempts = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<BlockedIP {self.ip_address}: blocked until {self.blocked_until}>'

    @property
    def is_blocked(self):
        """Check if IP is currently blocked"""
        if self.blocked_until is None:
            return False

        # Ensure both datetimes are offset-aware for comparison
        now = datetime.now(timezone.utc)
        blocked_until = self.blocked_until

        # If blocked_until is offset-naive, make it offset-aware
        if blocked_until.tzinfo is None:
            blocked_until = blocked_until.replace(tzinfo=timezone.utc)

        return now < blocked_until

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Nullable for system events
    username = db.Column(db.String(80), nullable=False)  # Store username for historical reference
    action = db.Column(db.String(100), nullable=False)  # Action performed (login, logout, create, update, delete, etc.)
    action_category = db.Column(db.String(50), nullable=False)  # Category: auth, sales, inventory, system, security, etc.
    resource_type = db.Column(db.String(50), nullable=False)  # Type of resource (user, item, sale, category, etc.)
    resource_id = db.Column(db.Integer, nullable=True)  # ID of the affected resource
    resource_name = db.Column(db.String(200), nullable=True)  # Name/title of the affected resource
    details = db.Column(db.Text, nullable=True)  # Additional details about the action
    old_value = db.Column(db.Text, nullable=True)  # Previous value for change tracking
    new_value = db.Column(db.Text, nullable=True)  # New value for change tracking
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4/IPv6 address
    user_agent = db.Column(db.String(500), nullable=True)  # Browser/client information
    session_id = db.Column(db.String(100), nullable=True)  # Session identifier
    terminal_id = db.Column(db.String(50), nullable=True)  # Terminal/device identifier
    location = db.Column(db.String(100), nullable=True)  # Physical location if applicable
    status = db.Column(db.String(20), nullable=False, default='success')  # success, error, warning
    error_message = db.Column(db.Text, nullable=True)  # Error details if applicable
    severity = db.Column(db.String(20), nullable=False, default='info')  # info, warning, error, critical
    compliance_flag = db.Column(db.Boolean, default=False)  # Flag for compliance-related events
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    retention_date = db.Column(db.DateTime, nullable=True)  # When this log can be archived/deleted

    # Relationship with user (nullable)
    user = db.relationship('User', backref=db.backref('activity_logs', lazy=True), foreign_keys=[user_id])

    def __repr__(self):
        return f'<ActivityLog {self.id}: {self.username} - {self.action} - {self.resource_type}>'

    @property
    def timestamp(self):
        """Return formatted timestamp"""
        return self.created_at.strftime('%Y-%m-%d %H:%M:%S')

    @property
    def action_description(self):
        """Return human-readable action description"""
        descriptions = {
            'login': 'Logged in',
            'logout': 'Logged out',
            'login_failed': 'Failed login attempt',
            'password_change': 'Changed password',
            'profile_update': 'Updated profile',
            'user_create': 'Created user',
            'user_update': 'Updated user',
            'user_delete': 'Deleted user',
            'item_create': 'Created item',
            'item_update': 'Updated item',
            'item_delete': 'Deleted item',
            'category_create': 'Created category',
            'category_update': 'Updated category',
            'category_delete': 'Deleted category',
            'sale_create': 'Completed sale',
            'sale_view': 'Viewed sale',
            'inventory_view': 'Viewed inventory',
            'report_view': 'Viewed reports',
            'backup_create': 'Created backup',
            'backup_download': 'Downloaded backup',
            'backup_restore': 'Restored backup',
            'backup_schedule_update': 'Updated backup schedule',
            'backup_auto_created': 'Automatic backup created',
            'branding_update': 'Updated branding',
            'permission_change': 'Changed permissions',
            'system_error': 'System error occurred',
            'security_alert': 'Security alert'
        }
        return descriptions.get(self.action, self.action.replace('_', ' ').title())

# Forms
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[('cashier', 'Cashier'), ('admin', 'Admin')],
                      validators=[DataRequired()])
    submit = SubmitField('Add User')

class ItemForm(FlaskForm):
    name = StringField('Item Name', validators=[DataRequired()])
    buying_price = FloatField('Buying Price', validators=[DataRequired(), NumberRange(min=0)])
    selling_price = FloatField('Selling Price', validators=[DataRequired(), NumberRange(min=0)])
    quantity = IntegerField('Quantity', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Add Item')

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Security Functions
def get_client_ip():
    """Get the real client IP address"""
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    else:
        return request.remote_addr

def is_ip_blocked(ip_address):
    """Check if IP is blocked"""
    blocked_ip = BlockedIP.query.filter_by(ip_address=ip_address).first()
    if blocked_ip and blocked_ip.is_blocked:
        return True, blocked_ip.block_reason
    return False, None

def block_ip(ip_address, reason, duration_minutes=15):
    """Block an IP address for a specified duration"""
    blocked_ip = BlockedIP.query.filter_by(ip_address=ip_address).first()
    if not blocked_ip:
        blocked_ip = BlockedIP(ip_address=ip_address, block_reason=reason, failed_attempts=0)
        db.session.add(blocked_ip)

    blocked_ip.blocked_until = datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)
    # Ensure failed_attempts is not None before incrementing
    if blocked_ip.failed_attempts is None:
        blocked_ip.failed_attempts = 0
    blocked_ip.failed_attempts += 1
    blocked_ip.block_reason = reason
    db.session.commit()

    # Log the IP block
    log_activity(user=None, action='ip_blocked', action_category='security',
                resource_type='ip_address', resource_name=ip_address,
                details=f'IP address {ip_address} blocked for {duration_minutes} minutes due to: {reason}',
                severity='warning', compliance_flag=True)

def record_login_attempt(username, ip_address, success=False, failure_reason=None):
    """Record a login attempt"""
    user_agent = request.headers.get('User-Agent', '')[:500]
    session_id = session.get('session_id', str(uuid.uuid4())[:8])

    attempt = LoginAttempt(
        username=username,
        ip_address=ip_address,
        user_agent=user_agent,
        success=success,
        failure_reason=failure_reason,
        session_id=session_id
    )
    db.session.add(attempt)
    db.session.commit()

def get_recent_failed_attempts(username, ip_address, minutes=15):
    """Get recent failed login attempts for user/IP combination"""
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    # Failed attempts for this username
    user_attempts = LoginAttempt.query.filter(
        LoginAttempt.username == username,
        LoginAttempt.success == False,
        LoginAttempt.attempt_time >= cutoff_time
    ).count()

    # Failed attempts from this IP
    ip_attempts = LoginAttempt.query.filter(
        LoginAttempt.ip_address == ip_address,
        LoginAttempt.success == False,
        LoginAttempt.attempt_time >= cutoff_time
    ).count()

    return user_attempts, ip_attempts

def should_require_captcha(username, ip_address):
    """Determine if CAPTCHA should be required"""
    user_attempts, ip_attempts = get_recent_failed_attempts(username, ip_address, minutes=10)

    # Require CAPTCHA after 3 failed attempts for user or 5 for IP
    return user_attempts >= 3 or ip_attempts >= 5

def get_progressive_delay(attempt_count):
    """Calculate progressive delay based on attempt count"""
    if attempt_count <= 3:
        return 0  # No delay for first 3 attempts
    elif attempt_count <= 5:
        return 2  # 2 second delay
    elif attempt_count <= 10:
        return 5  # 5 second delay
    else:
        return 10  # 10 second delay for many attempts

def validate_password_strength(password):
    """Validate password strength requirements"""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one number"

    # Check for common weak passwords
    weak_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein', 'welcome']
    if password.lower() in weak_passwords:
        return False, "This password is too common and easily guessed"

    return True, "Password is strong"

def generate_captcha_text():
    """Generate a simple CAPTCHA text"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def hash_captcha_text(text):
    """Hash CAPTCHA text for storage"""
    return hashlib.sha256(text.encode()).hexdigest()

def verify_captcha(session_captcha_hash, user_input):
    """Verify CAPTCHA input"""
    if not session_captcha_hash or not user_input:
        return False

    user_hash = hashlib.sha256(user_input.upper().encode()).hexdigest()
    return user_hash == session_captcha_hash

# Context processor to make branding available globally
@app.context_processor
def inject_branding():
    """Make branding settings available to all templates"""
    try:
        branding_settings = Branding.query.first()

        if not branding_settings:
            # Return default branding if none exists
            return {
                'branding': {
                    'app_name': 'POS System',
                    'app_subtitle': 'Professional Point of Sale',
                    'business_name': None,
                    'business_address': None,
                    'business_phone': None,
                    'business_email': None,
                    'tax_id': None,
                    'primary_color': '#6366f1',
                    'secondary_color': '#8b5cf6',
                    'accent_color': '#10b981',
                    'background_color': '#ffffff',
                    'text_color': '#1f2937',
                    'font_family': 'Inter',
                    'logo_url': None,
                    'favicon_url': None,
                    'footer_text': 'Thank you for your business!',
                    'receipt_return_policy': 'For exchanges/returns, present this receipt within 30 days.',
                    'receipt_header_title': 'RECEIPT',
                    'receipt_number_label': 'Receipt #:',
                    'date_label': 'Date:',
                    'cashier_label': 'Cashier:',
                    'payment_method_label': 'Payment Method:',
                    'payment_method_value': 'Cash',
                    'cash_received_label': 'Cash Received:',
                    'change_label': 'Change:',
                    'currency_symbol': 'AFA',
                    'item_header': 'Item',
                    'quantity_header': 'Qty',
                    'amount_header': 'Amount',
                    'subtotal_label': 'Subtotal:',
                    'discount_label': 'Discount',
                    'total_label': 'TOTAL:',
                    'records_message': 'Please keep this receipt for your records.',
                    'powered_by_label': 'Powered by',
                    'version_text': 'v1.0'
                }
            }

        return {
            'branding': {
                'app_name': branding_settings.app_name,
                'app_subtitle': branding_settings.app_subtitle,
                'business_name': branding_settings.business_name,
                'business_address': branding_settings.business_address,
                'business_phone': branding_settings.business_phone,
                'business_email': branding_settings.business_email,
                'tax_id': branding_settings.tax_id,
                'primary_color': branding_settings.primary_color,
                'secondary_color': branding_settings.secondary_color,
                'accent_color': branding_settings.accent_color,
                'background_color': branding_settings.background_color,
                'text_color': branding_settings.text_color,
                'font_family': branding_settings.font_family,
                'logo_url': branding_settings.logo_url,
                'favicon_url': branding_settings.favicon_url,
                'footer_text': branding_settings.footer_text,
                'receipt_return_policy': getattr(branding_settings, 'receipt_return_policy', 'For exchanges/returns, present this receipt within 30 days.'),
                'receipt_header_title': getattr(branding_settings, 'receipt_header_title', 'RECEIPT'),
                'receipt_number_label': getattr(branding_settings, 'receipt_number_label', 'Receipt #:'),
                'date_label': getattr(branding_settings, 'date_label', 'Date:'),
                'cashier_label': getattr(branding_settings, 'cashier_label', 'Cashier:'),
                'payment_method_label': getattr(branding_settings, 'payment_method_label', 'Payment Method:'),
                'payment_method_value': getattr(branding_settings, 'payment_method_value', 'Cash'),
                'cash_received_label': getattr(branding_settings, 'cash_received_label', 'Cash Received:'),
                'change_label': getattr(branding_settings, 'change_label', 'Change:'),
                'currency_symbol': getattr(branding_settings, 'currency_symbol', 'AFA'),
                'item_header': getattr(branding_settings, 'item_header', 'Item'),
                'quantity_header': getattr(branding_settings, 'quantity_header', 'Qty'),
                'amount_header': getattr(branding_settings, 'amount_header', 'Amount'),
                'subtotal_label': getattr(branding_settings, 'subtotal_label', 'Subtotal:'),
                'discount_label': getattr(branding_settings, 'discount_label', 'Discount'),
                'total_label': getattr(branding_settings, 'total_label', 'TOTAL:'),
                'records_message': getattr(branding_settings, 'records_message', 'Please keep this receipt for your records.'),
                'powered_by_label': getattr(branding_settings, 'powered_by_label', 'Powered by'),
                'version_text': getattr(branding_settings, 'version_text', 'v1.0')
            }
        }
    except Exception as e:
        # If there's an error (likely due to missing column), return default branding
        print(f"Error loading branding settings: {e}")
        return {
            'branding': {
                'app_name': 'POS System',
                'app_subtitle': 'Professional Point of Sale',
                'business_name': None,
                'business_address': None,
                'business_phone': None,
                'business_email': None,
                'tax_id': None,
                'primary_color': '#6366f1',
                'secondary_color': '#8b5cf6',
                'accent_color': '#10b981',
                'background_color': '#ffffff',
                'text_color': '#1f2937',
                'font_family': 'Inter',
                'logo_url': None,
                'favicon_url': None,
                'footer_text': 'Thank you for your business!',
                'receipt_return_policy': 'For exchanges/returns, present this receipt within 30 days.',
                'receipt_header_title': 'RECEIPT',
                'receipt_number_label': 'Receipt #:',
                'date_label': 'Date:',
                'cashier_label': 'Cashier:',
                'payment_method_label': 'Payment Method:',
                'payment_method_value': 'Cash',
                'cash_received_label': 'Cash Received:',
                'change_label': 'Change:',
                'currency_symbol': 'AFA',
                'item_header': 'Item',
                'quantity_header': 'Qty',
                'amount_header': 'Amount',
                'subtotal_label': 'Subtotal:',
                'discount_label': 'Discount',
                'total_label': 'TOTAL:',
                'records_message': 'Please keep this receipt for your records.',
                'powered_by_label': 'Powered by',
                'version_text': 'v1.0'
            }
        }

# Routes
@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # Get client IP and check if blocked
    client_ip = get_client_ip()
    is_blocked, block_reason = is_ip_blocked(client_ip)

    if is_blocked:
        # Log blocked attempt
        log_activity(user=None, action='login_blocked', action_category='security',
                    resource_type='ip_address', resource_name=client_ip,
                    details=f'Login attempt blocked from IP {client_ip}: {block_reason}',
                    status='error', severity='warning', compliance_flag=True)

        flash(f'Access denied. Your IP address has been blocked due to suspicious activity.', 'error')
        return render_template('login.html', form=LoginForm(), blocked=True)

    form = LoginForm()

    # Check if CAPTCHA is required
    username = form.username.data if form.username.data else request.args.get('username', '')
    require_captcha = should_require_captcha(username, client_ip)

    # Handle CAPTCHA verification
    if require_captcha and request.method == 'POST':
        captcha_input = request.form.get('captcha', '')
        captcha_hash = session.get('captcha_hash')

        if not verify_captcha(captcha_hash, captcha_input):
            # Record failed CAPTCHA attempt
            record_login_attempt(username, client_ip, success=False, failure_reason='Invalid CAPTCHA')
            flash('Invalid CAPTCHA. Please try again.', 'error')

            # Generate new CAPTCHA
            captcha_text = generate_captcha_text()
            session['captcha_hash'] = hash_captcha_text(captcha_text)
            session['captcha_text'] = captcha_text  # For debugging

            return render_template('login.html', form=form, require_captcha=True,
                                 captcha_text=captcha_text, username=username)

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        # Get recent failed attempts for progressive delay
        user_attempts, ip_attempts = get_recent_failed_attempts(form.username.data, client_ip, minutes=15)
        delay_seconds = get_progressive_delay(max(user_attempts, ip_attempts))

        # Apply progressive delay
        if delay_seconds > 0:
            time.sleep(delay_seconds)

        if user and user.check_password(form.password.data):
            # Successful login
            record_login_attempt(form.username.data, client_ip, success=True)

            # Clear CAPTCHA session on successful login
            session.pop('captcha_hash', None)
            session.pop('captcha_text', None)

            login_user(user)

            # Set session variables
            session['session_id'] = str(uuid.uuid4())[:8]
            session['terminal_id'] = f'TERM-{uuid.uuid4().hex[:8].upper()}'

            # Log successful login with enhanced details
            log_activity(user=user, action='login', action_category='auth', resource_type='user',
                        resource_id=user.id, resource_name=user.username,
                        details=f'User {user.username} logged in successfully from IP {client_ip}',
                        severity='info', compliance_flag=True,
                        additional_data={
                            'ip_address': client_ip,
                            'user_agent': request.headers.get('User-Agent'),
                            'terminal_id': session.get('terminal_id')
                        })

            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))

        else:
            # Failed login attempt
            failure_reason = 'Invalid username or password'
            record_login_attempt(form.username.data, client_ip, success=False, failure_reason=failure_reason)

            # Check if we should block the IP
            user_attempts, ip_attempts = get_recent_failed_attempts(form.username.data, client_ip, minutes=15)

            # Block IP after 10 failed attempts in 15 minutes
            if user_attempts >= 10 or ip_attempts >= 15:
                block_ip(client_ip, f'Multiple failed login attempts ({max(user_attempts, ip_attempts)} total)',
                        duration_minutes=30)
                flash('Too many failed attempts. Your IP has been temporarily blocked.', 'error')
                return render_template('login.html', form=form, blocked=True)

            # Log failed login attempt with enhanced details
            log_activity(user=None, action='login_failed', action_category='auth', resource_type='user',
                        resource_name=form.username.data,
                        details=f'Failed login attempt for username: {form.username.data} from IP {client_ip}',
                        status='error', error_message=failure_reason,
                        severity='warning', compliance_flag=True,
                        additional_data={
                            'ip_address': client_ip,
                            'user_agent': request.headers.get('User-Agent'),
                            'attempt_count': max(user_attempts, ip_attempts)
                        })

            # Determine if CAPTCHA should be shown
            require_captcha = should_require_captcha(form.username.data, client_ip)

            if require_captcha:
                # Generate CAPTCHA
                captcha_text = generate_captcha_text()
                session['captcha_hash'] = hash_captcha_text(captcha_text)
                session['captcha_text'] = captcha_text  # For debugging

                flash('Invalid username or password. Please complete the CAPTCHA to continue.', 'error')
                return render_template('login.html', form=form, require_captcha=True,
                                     captcha_text=captcha_text, username=form.username.data)
            else:
                flash('Invalid username or password', 'error')

    # Generate CAPTCHA if required for GET request
    captcha_text = None
    if require_captcha:
        captcha_text = generate_captcha_text()
        session['captcha_hash'] = hash_captcha_text(captcha_text)
        session['captcha_text'] = captcha_text

    return render_template('login.html', form=form, require_captcha=require_captcha,
                         captcha_text=captcha_text, username=username)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    # Log logout before actually logging out
    log_activity(user=current_user, action='logout', action_category='auth', resource_type='user',
                resource_id=current_user.id, resource_name=current_user.username,
                details=f'User {current_user.username} logged out', severity='info', compliance_flag=True)
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Calculate dashboard metrics
    now = datetime.now(timezone.utc)

    # Sales metrics
    daily_sales = db.session.query(db.func.sum(Sale.final_amount)).filter(
        db.func.date(Sale.created_at) == now.date()
    ).scalar() or 0

    # Calculate date ranges in Python
    week_ago = now - timedelta(days=7)
    weekly_sales = db.session.query(db.func.sum(Sale.final_amount)).filter(
        Sale.created_at >= week_ago
    ).scalar() or 0

    # For monthly sales, use string formatting for SQLite compatibility
    monthly_sales = db.session.query(db.func.sum(Sale.final_amount)).filter(
        db.func.strftime('%Y-%m', Sale.created_at) == now.strftime('%Y-%m')
    ).scalar() or 0

    total_profit = db.session.query(db.func.sum(Sale.profit)).scalar() or 0

    # Transaction counts
    daily_transactions = Sale.query.filter(
        db.func.date(Sale.created_at) == now.date()
    ).count()

    # Inventory metrics
    total_items = db.session.query(db.func.count(Item.id)).scalar()
    out_of_stock = db.session.query(db.func.count(Item.id)).filter(Item.quantity == 0).scalar()
    low_stock = db.session.query(db.func.count(Item.id)).filter(Item.quantity > 0, Item.quantity <= 5).scalar()

    # Top selling items
    top_items = Item.query.order_by(Item.sold_quantity.desc()).limit(5).all()

    # Recent sales
    recent_sales = Sale.query.order_by(Sale.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                         daily_sales=daily_sales,
                         weekly_sales=weekly_sales,
                         monthly_sales=monthly_sales,
                         total_profit=total_profit,
                         total_transactions=Sale.query.count(),
                         total_items=total_items,
                         out_of_stock=out_of_stock,
                         low_stock=low_stock,
                         top_items=top_items,
                         recent_sales=recent_sales)

@app.route('/sales')
@login_required
def sales():
    items = Item.query.all()
    return render_template('sales.html', items=items)

@app.route('/categories', methods=['GET', 'POST'])
@login_required
def categories():
    # Check if user can manage inventory
    if not has_permission(current_user, 'manage_inventory'):
        flash('Access denied. You do not have permission to manage inventory.', 'error')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()

        if not name:
            flash('Category name is required.', 'error')
        else:
            # Check if category already exists
            existing = Category.query.filter_by(name=name).first()
            if existing:
                flash('Category with this name already exists.', 'error')
            else:
                category = Category(name=name, description=description)
                db.session.add(category)
                db.session.commit()
                flash('Category added successfully!', 'success')
                return redirect(url_for('categories'))

    categories_list = Category.query.order_by(Category.created_at.desc()).all()
    return render_template('categories.html', categories=categories_list)

@app.route('/api/categories/<int:category_id>', methods=['PUT'])
@login_required
def update_category(category_id):
    if not has_permission(current_user, 'manage_inventory'):
        return jsonify({'error': 'Access denied. You do not have permission to manage inventory.'}), 403

    category = Category.query.get_or_404(category_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    if 'name' in data and data['name'].strip():
        # Check if name already exists for another category
        existing = Category.query.filter(Category.name == data['name'].strip(), Category.id != category_id).first()
        if existing:
            return jsonify({'error': 'Category with this name already exists'}), 400
        category.name = data['name'].strip()

    if 'description' in data:
        category.description = data['description'].strip() if data['description'] else None

    db.session.commit()
    return jsonify({'success': True, 'message': 'Category updated successfully'})

@app.route('/api/categories/<int:category_id>', methods=['DELETE'])
@login_required
def delete_category(category_id):
    if not has_permission(current_user, 'manage_inventory'):
        return jsonify({'error': 'Access denied. You do not have permission to manage inventory.'}), 403

    category = Category.query.get_or_404(category_id)

    # Check if category has items
    if category.items:
        return jsonify({'error': 'Cannot delete category that has items. Please reassign or delete the items first.'}), 400

    db.session.delete(category)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Category deleted successfully'})

@app.route('/api/add_common_categories', methods=['POST'])
@login_required
def add_common_categories():
    if not has_permission(current_user, 'manage_inventory'):
        return jsonify({'error': 'Access denied. You do not have permission to manage inventory.'}), 403

    # Define most common categories
    common_categories = [
        {'name': 'Beverages', 'description': 'Drinks, juices, soft drinks, and beverages'},
        {'name': 'Snacks', 'description': 'Chips, cookies, candies, and snack foods'},
        {'name': 'Dairy', 'description': 'Milk, cheese, yogurt, and dairy products'},
        {'name': 'Bakery', 'description': 'Bread, cakes, pastries, and baked goods'},
        {'name': 'Fruits & Vegetables', 'description': 'Fresh fruits and vegetables'},
        {'name': 'Meat & Poultry', 'description': 'Meat, chicken, fish, and poultry products'},
        {'name': 'Frozen Foods', 'description': 'Frozen meals, ice cream, and frozen products'},
        {'name': 'Canned Goods', 'description': 'Canned foods, soups, and preserved items'},
        {'name': 'Household', 'description': 'Cleaning supplies, detergents, and household items'},
        {'name': 'Personal Care', 'description': 'Soap, shampoo, toiletries, and personal care products'},
        {'name': 'Electronics', 'description': 'Electronic devices, accessories, and gadgets'},
        {'name': 'Clothing', 'description': 'Clothes, apparel, and fashion items'},
        {'name': 'Stationery', 'description': 'Books, pens, paper, and office supplies'},
        {'name': 'Pharmacy', 'description': 'Medicines, health products, and pharmaceuticals'},
        {'name': 'Sports & Fitness', 'description': 'Sports equipment, gym accessories, and fitness products'}
    ]

    added_count = 0
    skipped_count = 0

    for category_data in common_categories:
        # Check if category already exists (case-insensitive)
        existing = Category.query.filter(Category.name.ilike(category_data['name'])).first()
        if not existing:
            category = Category(
                name=category_data['name'],
                description=category_data['description']
            )
            db.session.add(category)
            added_count += 1
        else:
            skipped_count += 1

    db.session.commit()

    # Log the action
    log_activity(user=current_user, action='add_common_categories', action_category='inventory',
                resource_type='category', details=f'Added {added_count} common categories, skipped {skipped_count} existing ones')

    if added_count > 0:
        message = f'Successfully added {added_count} common categories!'
        if skipped_count > 0:
            message += f' ({skipped_count} categories already existed)'
    else:
        message = f'All common categories already exist in your system.'

    return jsonify({
        'success': True,
        'message': message,
        'added_count': added_count,
        'skipped_count': skipped_count
    })

@app.route('/inventory', methods=['GET', 'POST'])
@login_required
def inventory():
    # Check if user can view inventory
    if not has_permission(current_user, 'view_inventory'):
        flash('Access denied. You do not have permission to view inventory.', 'error')
        return redirect(url_for('dashboard'))

    form = ItemForm()
    if request.method == 'POST':
        # Check if user can manage inventory for POST operations
        if not has_permission(current_user, 'manage_inventory'):
            flash('Access denied. You do not have permission to manage inventory.', 'error')
            return redirect(url_for('inventory'))

        if form.validate_on_submit():
            # Generate unique barcode
            barcode = str(int(datetime.now(timezone.utc).timestamp() * 1000000))

            # Get form data
            category_id = request.form.get('category_id')
            expiry_date_str = request.form.get('expiry_date')

            item = Item(
                name=form.name.data,
                buying_price=form.buying_price.data,
                selling_price=form.selling_price.data,
                quantity=form.quantity.data,
                barcode=barcode,
                category_id=int(category_id) if category_id else None,
                expiry_date=datetime.strptime(expiry_date_str, '%Y-%m-%d').date() if expiry_date_str else None
            )
            db.session.add(item)
            db.session.commit()

            # Log item creation
            log_activity(user=current_user, action='item_create', resource_type='item',
                        resource_id=item.id, resource_name=item.name,
                        details=f'Created item: {item.name} with barcode {item.barcode}')

            flash('Item added successfully!', 'success')
            return redirect(url_for('inventory'))

    items = Item.query.options(db.joinedload(Item.category)).all()
    categories = Category.query.all()
    return render_template('inventory.html', items=items, form=form, categories=categories)

@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

@app.route('/users', methods=['GET', 'POST'])
@login_required
def users():
    print(f"DEBUG: User {current_user.username} with role {current_user.role} accessing users page")

    # Check if user has permission to manage users
    if not has_permission(current_user, 'manage_users'):
        print(f"DEBUG: Access denied for user {current_user.username} with role {current_user.role}")
        flash('Access denied. You do not have permission to manage users.', 'error')
        return redirect(url_for('dashboard'))

    form = UserForm()

    if request.method == 'POST' and form.validate_on_submit():
        print("DEBUG: Processing POST request for new user")
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists!', 'error')
        else:
            user = User(
                username=form.username.data,
                role=form.role.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()

            # Log user creation
            log_activity(user=current_user, action='user_create', resource_type='user',
                        resource_id=user.id, resource_name=user.username,
                        details=f'Created new user: {user.username} with role {user.role}')

            flash('User added successfully!', 'success')
            return redirect(url_for('users'))

    users_list = User.query.all()
    print(f"DEBUG: Found {len(users_list)} users in database")
    print("DEBUG: Rendering users template")

    return render_template('users_new.html', users=users_list, form=form)

@app.route('/permissions')
@login_required
def permissions():
    # Only admins can view permissions
    if not has_permission(current_user, 'system_admin'):
        flash('Access denied. Only system administrators can view permissions.', 'error')
        return redirect(url_for('dashboard'))

    # Get all users
    users = User.query.all()

    # Get user permissions
    user_permissions = {}
    for user in users:
        user_permissions[user.id] = get_user_permissions(user)

    return render_template('permissions.html',
                         roles=list(ROLE_PERMISSIONS.keys()),
                         permissions=get_all_permissions(),
                         role_permissions=ROLE_PERMISSIONS,
                         users=users,
                         user_permissions=user_permissions)

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'change_password':
            current_password = request.form.get('current_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')

            # Validate current password
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
                return redirect(url_for('profile'))

            # Validate new password strength
            is_strong, strength_message = validate_password_strength(new_password)
            if not is_strong:
                flash(f'Password is too weak: {strength_message}', 'error')
                return redirect(url_for('profile'))

            # Check if passwords match
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return redirect(url_for('profile'))

            # Update password
            current_user.set_password(new_password)
            db.session.commit()

            # Log password change
            log_activity(user=current_user, action='password_change', action_category='auth',
                        resource_type='user', resource_id=current_user.id, resource_name=current_user.username,
                        details='User changed their password', severity='info', compliance_flag=True)

            flash('Password changed successfully!', 'success')

        elif action == 'set_secret_question':
            secret_question = request.form.get('secret_question')
            secret_answer = request.form.get('secret_answer')

            if not secret_question or not secret_answer:
                flash('Please fill in both secret question and answer.', 'error')
                return redirect(url_for('profile'))

            current_user.secret_question = secret_question
            current_user.secret_answer = secret_answer.lower().strip()
            db.session.commit()
            flash('Secret question and answer set successfully!', 'success')

        return redirect(url_for('profile'))

    return render_template('profile.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        secret_answer = request.form.get('secret_answer')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        user = User.query.filter_by(username=username).first()

        if not user:
            flash('User not found.', 'error')
            return redirect(url_for('forgot_password'))

        if not user.secret_question or not user.secret_answer:
            flash('No secret question set for this user. Please contact administrator.', 'error')
            return redirect(url_for('forgot_password'))

        if user.secret_answer != secret_answer.lower().strip():
            flash('Incorrect answer to secret question.', 'error')
            return redirect(url_for('forgot_password'))

        if len(new_password) < 6:
            flash('New password must be at least 6 characters long.', 'error')
            return redirect(url_for('forgot_password'))

        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('forgot_password'))

        user.set_password(new_password)
        db.session.commit()
        flash('Password reset successfully! You can now login with your new password.', 'success')
        return redirect(url_for('login'))

    return render_template('forgot_password.html')

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        # Validate current password
        if not current_user.check_password(current_password):
            flash('Current password is incorrect.', 'error')
            return redirect(url_for('dashboard'))

        # Validate new password
        if len(new_password) < 6:
            flash('New password must be at least 6 characters long.', 'error')
            return redirect(url_for('dashboard'))

        # Check if passwords match
        if new_password != confirm_password:
            flash('New passwords do not match.', 'error')
            return redirect(url_for('dashboard'))

        # Update password
        current_user.set_password(new_password)
        db.session.commit()

        flash('Password changed successfully!', 'success')
        return redirect(url_for('dashboard'))

    return redirect(url_for('dashboard'))

# API Routes
@app.route('/api/add_item', methods=['POST'])
@login_required
def add_item():
    if not has_permission(current_user, 'manage_inventory'):
        flash('Access denied. You do not have permission to manage inventory.', 'error')
        return redirect(url_for('inventory'))

    form = ItemForm()
    if form.validate_on_submit():
        # Generate unique barcode
        barcode = str(int(datetime.now(timezone.utc).timestamp() * 1000000))

        item = Item(
            name=form.name.data,
            buying_price=form.buying_price.data,
            selling_price=form.selling_price.data,
            quantity=form.quantity.data,
            barcode=barcode
        )
        db.session.add(item)
        db.session.commit()
        flash('Item added successfully!', 'success')
    else:
        flash('Error adding item. Please check the form.', 'error')

    return redirect(url_for('inventory'))

@app.route('/api/add_user', methods=['POST'])
@login_required
def add_user():
    if not has_permission(current_user, 'manage_users'):
        return jsonify({'error': 'Access denied. You do not have permission to manage users.'}), 403

    form = UserForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('Username already exists!', 'error')
        else:
            user = User(
                username=form.username.data,
                role=form.role.data
            )
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            flash('User added successfully!', 'success')
    else:
        flash('Error adding user. Please check the form.', 'error')

    return redirect(url_for('users'))

@app.route('/api/complete_sale', methods=['POST'])
@login_required
def complete_sale():
    data = request.get_json()

    if not data or 'items' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    items_data = data['items']
    discount_percent = data.get('discount_percent', 0)
    cash_received = data.get('cash_received', 0)
    change_amount = data.get('change_amount', 0)

    # Validate items and stock
    total_amount = 0
    sale_items = []

    for item_data in items_data:
        item = Item.query.filter_by(barcode=item_data['barcode']).first()
        if not item:
            return jsonify({'error': f'Item not found: {item_data["name"]}'} ), 400

        if item.quantity < item_data['quantity']:
            return jsonify({'error': f'Insufficient stock for {item.name}'} ), 400

        # Calculate totals
        item_total = item.selling_price * item_data['quantity']
        total_amount += item_total

        sale_items.append({
            'item': item,
            'quantity': item_data['quantity'],
            'unit_price': item.selling_price,
            'total_price': item_total
        })

    # Calculate discount and final amount
    discount_amount = total_amount * (discount_percent / 100)
    final_amount = total_amount - discount_amount

    # Calculate profit
    profit = 0
    for sale_item in sale_items:
        item = sale_item['item']
        profit += (item.selling_price - item.buying_price) * sale_item['quantity']

    # Generate unique receipt number
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')
    receipt_number = f"RCP-{timestamp}-{current_user.id:03d}"

    # Create sale record
    sale = Sale(
        user_id=current_user.id,
        total_amount=total_amount,
        discount_percent=discount_percent,
        discount_amount=discount_amount,
        final_amount=final_amount,
        profit=profit,
        receipt_number=receipt_number,
        cash_received=cash_received,
        change_amount=change_amount
    )
    db.session.add(sale)
    db.session.flush()  # Get sale ID

    # Create sale items and update inventory
    for sale_item in sale_items:
        item = sale_item['item']
        quantity = sale_item['quantity']

        # Create sale item record
        sale_item_record = SaleItem(
            sale_id=sale.id,
            item_id=item.id,
            quantity=quantity,
            unit_price=sale_item['unit_price'],
            total_price=sale_item['total_price']
        )
        db.session.add(sale_item_record)

        # Update inventory
        item.quantity -= quantity
        item.sold_quantity += quantity

    db.session.commit()

    # Log the sale completion with detailed context
    log_activity(user=current_user, action='sale_create', action_category='sales', resource_type='sale',
                resource_id=sale.id, resource_name=receipt_number,
                details=f'Completed customer transaction with receipt generation',
                additional_data={
                    'total_amount': f'{final_amount:.2f} AFA',
                    'items_count': len(items_data),
                    'profit': f'{profit:.2f} AFA',
                    'discount_applied': f'{discount_amount:.2f} AFA'
                })

    return jsonify({
        'success': True,
        'sale_id': sale.id,
        'receipt_number': receipt_number,
        'total': final_amount,
        'message': f'Sale completed successfully! Total: {final_amount:.2f} AFA'
    })

@app.route('/api/items')
@login_required
def get_items():
    items = Item.query.all()
    return jsonify([{
        'id': item.id,
        'name': item.name,
        'buying_price': item.buying_price,
        'selling_price': item.selling_price,
        'quantity': item.quantity,
        'barcode': item.barcode,
        'sold_quantity': item.sold_quantity
    } for item in items])

@app.route('/api/top_sold_items')
@login_required
def get_top_sold_items():
    # Get top 10 sold items ordered by sold_quantity descending
    top_items = Item.query.filter(Item.sold_quantity > 0).order_by(Item.sold_quantity.desc()).limit(10).all()

    return jsonify({
        'success': True,
        'items': [{
            'id': item.id,
            'name': item.name,
            'selling_price': item.selling_price,
            'barcode': item.barcode,
            'sold_quantity': item.sold_quantity
        } for item in top_items]
    })

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
@login_required
def delete_item(item_id):
    if not has_permission(current_user, 'manage_inventory'):
        return jsonify({'error': 'Access denied. You do not have permission to manage inventory.'}), 403

    item = Item.query.get_or_404(item_id)

    # Log item deletion before deleting
    log_activity(user=current_user, action='item_delete', resource_type='item',
                resource_id=item.id, resource_name=item.name,
                details=f'Deleted item: {item.name} with barcode {item.barcode}')

    db.session.delete(item)
    db.session.commit()
    return jsonify({'success': True, 'message': 'Item deleted successfully'})

@app.route('/api/items/<int:item_id>', methods=['PUT'])
@login_required
def update_item(item_id):
    if not has_permission(current_user, 'manage_inventory'):
        return jsonify({'error': 'Access denied. You do not have permission to manage inventory.'}), 403

    item = Item.query.get_or_404(item_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Track changes for logging
    changes = []
    if 'name' in data and data['name'] != item.name:
        changes.append(f"name: '{item.name}' -> '{data['name']}'")
        item.name = data['name']
    if 'buying_price' in data and float(data['buying_price']) != item.buying_price:
        changes.append(f"buying_price: {item.buying_price} -> {data['buying_price']}")
        item.buying_price = float(data['buying_price'])
    if 'selling_price' in data and float(data['selling_price']) != item.selling_price:
        changes.append(f"selling_price: {item.selling_price} -> {data['selling_price']}")
        item.selling_price = float(data['selling_price'])
    if 'quantity' in data and int(data['quantity']) != item.quantity:
        changes.append(f"quantity: {item.quantity} -> {data['quantity']}")
        item.quantity = int(data['quantity'])
    if 'category_id' in data:
        new_category_id = int(data['category_id']) if data['category_id'] else None
        if new_category_id != item.category_id:
            changes.append(f"category_id: {item.category_id} -> {new_category_id}")
            item.category_id = new_category_id
    if 'expiry_date' in data:
        new_expiry = datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data['expiry_date'] else None
        if new_expiry != item.expiry_date:
            changes.append(f"expiry_date: {item.expiry_date} -> {new_expiry}")
            item.expiry_date = new_expiry

    db.session.commit()

    # Log item update if there were changes
    if changes:
        log_activity(user=current_user, action='item_update', resource_type='item',
                    resource_id=item.id, resource_name=item.name,
                    details=f'Updated item {item.name}: {", ".join(changes)}')

    return jsonify({'success': True, 'message': 'Item updated successfully'})

@app.route('/api/add_sample_items', methods=['POST'])
@login_required
def add_sample_items():
    if not has_permission(current_user, 'manage_inventory'):
        return jsonify({'error': 'Access denied. You do not have permission to manage inventory.'}), 403
    sample_items = [
        {'name': 'Apple', 'buy': 50, 'sell': 80, 'qty': 100},
        {'name': 'Banana', 'buy': 30, 'sell': 50, 'qty': 150},
        {'name': 'Orange', 'buy': 40, 'sell': 70, 'qty': 120},
        {'name': 'Milk 1L', 'buy': 120, 'sell': 150, 'qty': 50},
        {'name': 'Bread', 'buy': 25, 'sell': 40, 'qty': 80},
        {'name': 'Rice 1kg', 'buy': 80, 'sell': 110, 'qty': 60},
        {'name': 'Chicken 1kg', 'buy': 200, 'sell': 280, 'qty': 30},
        {'name': 'Eggs (12)', 'buy': 60, 'sell': 90, 'qty': 40},
        {'name': 'Sugar 1kg', 'buy': 70, 'sell': 95, 'qty': 70},
        {'name': 'Tea 100g', 'buy': 150, 'sell': 200, 'qty': 25}
    ]

    added_count = 0
    for item_data in sample_items:
        # Check if item already exists
        existing = Item.query.filter_by(name=item_data['name']).first()
        if not existing:
            barcode = str(int(datetime.now(timezone.utc).timestamp() * 1000000) + added_count)
            item = Item(
                name=item_data['name'],
                buying_price=item_data['buy'],
                selling_price=item_data['sell'],
                quantity=item_data['qty'],
                barcode=barcode
            )
            db.session.add(item)
            added_count += 1

    db.session.commit()
    return jsonify({'success': True, 'message': f'Added {added_count} sample items successfully'})

@app.route('/api/import_item', methods=['POST'])
@login_required
def import_item():
    """Import a single item with automatic barcode generation"""
    if not has_permission(current_user, 'manage_inventory'):
        return jsonify({'error': 'Access denied. You do not have permission to manage inventory.'}), 403

    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    # Validate required fields
    if not data.get('name'):
        return jsonify({'error': 'Item name is required'}), 400

    try:
        # Generate barcode if not provided
        barcode = data.get('barcode')
        if not barcode:
            barcode = str(int(datetime.now(timezone.utc).timestamp() * 1000000))

        # Check if barcode already exists
        existing_item = Item.query.filter_by(barcode=barcode).first()
        if existing_item:
            return jsonify({'error': f'Barcode {barcode} already exists for item: {existing_item.name}'}), 400

        # Check if item name already exists
        existing_name = Item.query.filter_by(name=data['name']).first()
        if existing_name:
            return jsonify({'error': f'Item with name "{data["name"]}" already exists'}), 400

        # Get category if provided
        category_id = None
        if data.get('category'):
            category = Category.query.filter_by(name=data['category']).first()
            if category:
                category_id = category.id
            else:
                # Create new category if it doesn't exist
                new_category = Category(name=data['category'])
                db.session.add(new_category)
                db.session.flush()
                category_id = new_category.id

        # Create new item
        item = Item(
            name=data['name'],
            buying_price=float(data.get('buying_price', 0)),
            selling_price=float(data.get('selling_price', 0)),
            quantity=int(data.get('quantity', 0)),
            barcode=barcode,
            category_id=category_id,
            expiry_date=datetime.strptime(data['expiry_date'], '%Y-%m-%d').date() if data.get('expiry_date') else None
        )

        db.session.add(item)
        db.session.commit()

        # Log the import
        log_activity(user=current_user, action='item_import', action_category='inventory',
                    resource_type='item', resource_id=item.id, resource_name=item.name,
                    details=f'Imported item via CSV: {item.name} with barcode {item.barcode}')

        return jsonify({
            'success': True,
            'message': f'Item "{item.name}" imported successfully',
            'item': {
                'id': item.id,
                'name': item.name,
                'barcode': item.barcode
            }
        })

    except ValueError as e:
        return jsonify({'error': f'Invalid data format: {str(e)}'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Error importing item: {str(e)}'}), 500

@app.route('/api/sales')
@login_required
def get_sales():
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    query = Sale.query

    if from_date:
        query = query.filter(Sale.created_at >= from_date)
    if to_date:
        query = query.filter(Sale.created_at <= to_date + ' 23:59:59')

    sales = query.order_by(Sale.created_at.desc()).all()

    return jsonify([{
        'id': sale.id,
        'date': sale.created_at.isoformat(),
        'total_amount': sale.total_amount,
        'discount_percent': sale.discount_percent,
        'discount_amount': sale.discount_amount,
        'final_amount': sale.final_amount,
        'profit': sale.profit,
        'user': sale.user.username,
        'items': [{
            'name': item.item.name,
            'quantity': item.quantity,
            'unit_price': item.unit_price,
            'buying_price': item.item.buying_price,
            'total_price': item.total_price
        } for item in sale.items]
    } for sale in sales])

@app.route('/api/check_user', methods=['POST'])
def check_user():
    data = request.get_json()
    username = data.get('username')

    if not username:
        return jsonify({'error': 'Username required'}), 400

    user = User.query.filter_by(username=username).first()

    if not user:
        return jsonify({'found': False})

    return jsonify({
        'found': True,
        'has_secret_question': bool(user.secret_question),
        'secret_question': user.secret_question
    })

@app.route('/api/users')
@login_required
def get_users():
    if not has_permission(current_user, 'view_users'):
        return jsonify({'error': 'Access denied. You do not have permission to view users.'}), 403

    users = User.query.all()
    return jsonify([{
        'id': user.id,
        'username': user.username,
        'role': user.role,
        'created_at': user.created_at.isoformat(),
        'secret_question': bool(user.secret_question)
    } for user in users])

@app.route('/api/users/<int:user_id>', methods=['GET', 'PUT'])
@login_required
def get_or_update_user(user_id):
    if not has_permission(current_user, 'manage_users'):
        return jsonify({'error': 'Access denied. You do not have permission to manage users.'}), 403

    user = User.query.get_or_404(user_id)

    if request.method == 'GET':
        # Return user data for editing
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'created_at': user.created_at.isoformat(),
                'has_secret_question': bool(user.secret_question)
            }
        })

    elif request.method == 'PUT':
        # Update user
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Update user fields
        if 'username' in data and data['username'] != user.username:
            # Check if username already exists
            existing = User.query.filter_by(username=data['username']).first()
            if existing:
                return jsonify({'error': 'Username already exists'}), 400
            user.username = data['username']

        if 'role' in data:
            user.role = data['role']

        if 'password' in data and data['password']:
            if len(data['password']) < 6:
                return jsonify({'error': 'Password must be at least 6 characters'}), 400
            user.set_password(data['password'])

        db.session.commit()
        return jsonify({'success': True, 'message': 'User updated successfully'})

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    if not has_permission(current_user, 'manage_users'):
        return jsonify({'error': 'Access denied. You do not have permission to manage users.'}), 403

    user = User.query.get_or_404(user_id)

    # Prevent deleting self
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400

    # Prevent deleting the last admin
    admin_count = User.query.filter_by(role='admin').count()
    if user.role == 'admin' and admin_count <= 1:
        return jsonify({'error': 'Cannot delete the last admin user'}), 400

    db.session.delete(user)
    db.session.commit()
    return jsonify({'success': True, 'message': 'User deleted successfully'})

@app.route('/api/users/<int:user_id>/permissions', methods=['GET', 'PUT'])
@login_required
def manage_user_permissions(user_id):
    if not has_permission(current_user, 'system_admin'):
        return jsonify({'error': 'Access denied. Only system administrators can manage permissions.'}), 403

    user = User.query.get_or_404(user_id)

    if request.method == 'GET':
        # Return current user permissions
        user_permissions = get_user_permissions(user)
        return jsonify({
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'permissions': user_permissions,
            'all_permissions': get_all_permissions()
        })

    elif request.method == 'PUT':
        # Update user permissions
        data = request.get_json()

        if not data or 'permissions' not in data:
            return jsonify({'error': 'Permissions data required'}), 400

        new_permissions = data['permissions']

        # Validate permissions
        all_permissions = list(get_all_permissions().keys())
        for perm in new_permissions:
            if perm not in all_permissions:
                return jsonify({'error': f'Invalid permission: {perm}'}), 400

        # Update user's role based on permissions
        # This is a simplified approach - in a real system you might want more complex logic
        if 'system_admin' in new_permissions:
            user.role = 'admin'
        elif 'manage_inventory' in new_permissions or 'manage_users' in new_permissions:
            user.role = 'admin'  # If they have management permissions, make them admin
        else:
            user.role = 'cashier'  # Default to cashier if no management permissions

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Permissions updated for {user.username}',
            'user': {
                'id': user.id,
                'username': user.username,
                'role': user.role,
                'permissions': get_user_permissions(user)
            }
        })

@app.route('/api/permissions/update_role', methods=['POST'])
@login_required
def update_role_permissions():
    if not has_permission(current_user, 'system_admin'):
        return jsonify({'error': 'Access denied. Only system administrators can manage permissions.'}), 403

    data = request.get_json()

    if not data or 'role' not in data or 'permissions' not in data:
        return jsonify({'error': 'Role and permissions data required'}), 400

    role = data['role']
    permissions = data['permissions']

    # Validate role
    if role not in ROLE_PERMISSIONS:
        return jsonify({'error': f'Invalid role: {role}'}), 400

    # Validate permissions
    all_permissions = list(get_all_permissions().keys())
    for perm in permissions:
        if perm not in all_permissions:
            return jsonify({'error': f'Invalid permission: {perm}'}), 400

    # Update role permissions
    ROLE_PERMISSIONS[role] = permissions

    # Update all users with this role to have the new permissions
    users = User.query.filter_by(role=role).all()
    updated_count = len(users)

    return jsonify({
        'success': True,
        'message': f'Role {role} permissions updated. {updated_count} users affected.',
        'role': role,
        'permissions': permissions
    })

@app.route('/print_barcode/<int:item_id>')
@login_required
def print_barcode(item_id):
    if not has_permission(current_user, 'view_inventory'):
        flash('Access denied. You do not have permission to view inventory.', 'error')
        return redirect(url_for('inventory'))

    item = Item.query.get_or_404(item_id)
    return render_template('barcode_print.html', item=item)

@app.route('/print_barcodes', methods=['POST'])
@login_required
def print_barcodes():
    if not has_permission(current_user, 'view_inventory'):
        flash('Access denied. You do not have permission to view inventory.', 'error')
        return redirect(url_for('inventory'))

    data = request.get_json()
    if not data or 'item_ids' not in data:
        return jsonify({'error': 'No items selected'}), 400

    item_ids = data['item_ids']
    if not item_ids:
        return jsonify({'error': 'No items selected'}), 400

    # Get selected items
    items = Item.query.filter(Item.id.in_(item_ids)).all()

    if not items:
        return jsonify({'error': 'No valid items found'}), 400

    return render_template('bulk_barcode_print.html', items=items)

@app.route('/print_receipt/<int:sale_id>')
@login_required
def print_receipt(sale_id):
    if not has_permission(current_user, 'view_sales'):
        flash('Access denied. You do not have permission to view sales.', 'error')
        return redirect(url_for('dashboard'))

    sale = Sale.query.get_or_404(sale_id)

    # Get payment information from the sale record
    cash_received = sale.cash_received
    change_amount = sale.change_amount

    # Get branding settings with error handling
    try:
        branding_settings = Branding.query.first()
        if not branding_settings:
            # Create default branding if none exists
            branding_settings = Branding()
    except Exception as e:
        print(f"Error querying branding table: {e}")
        # Create a default branding object when SQLAlchemy fails
        branding_settings = type('Branding', (), {
            'app_name': 'POS System',
            'app_subtitle': 'Professional Point of Sale',
            'business_name': 'Azizi SuperStore',
            'business_address': 'سرای علاوالدین، کابل، افغانستان',
            'business_phone': '+93799996645',
            'business_email': 'info@azizi.af',
            'tax_id': 'AF-123456789',
            'primary_color': '#6366f1',
            'secondary_color': '#8b5cf6',
            'accent_color': '#10b981',
            'background_color': '#ffffff',
            'text_color': '#1f2937',
            'logo_url': 'https://azizi.af/logo.png',
            'favicon_url': 'https://azizi.af/favicon.ico',
            'font_family': 'Inter',
            'footer_text': 'Thank you for shopping with us!',
            'receipt_return_policy': 'For exchanges/returns, present this receipt within 30 days with original packaging.'
        })()

    return render_template('receipt.html', sale=sale, cash_received=cash_received, change_amount=change_amount, branding=branding_settings)

@app.route('/receipt/<receipt_number>')
@login_required
def get_receipt_by_number(receipt_number):
    if not has_permission(current_user, 'view_sales'):
        flash('Access denied. You do not have permission to view sales.', 'error')
        return redirect(url_for('dashboard'))

    sale = Sale.query.filter_by(receipt_number=receipt_number).first_or_404()

    # Get payment information from the sale record
    cash_received = sale.cash_received
    change_amount = sale.change_amount

    # Get branding settings with error handling
    try:
        branding_settings = Branding.query.first()
        if not branding_settings:
            # Create default branding if none exists
            branding_settings = Branding()
    except Exception as e:
        print(f"Error querying branding table: {e}")
        # Create a default branding object when SQLAlchemy fails
        branding_settings = type('Branding', (), {
            'app_name': 'POS System',
            'app_subtitle': 'Professional Point of Sale',
            'business_name': 'Azizi SuperStore',
            'business_address': 'سرای علاوالدین، کابل، افغانستان',
            'business_phone': '+93799996645',
            'business_email': 'info@azizi.af',
            'tax_id': 'AF-123456789',
            'primary_color': '#6366f1',
            'secondary_color': '#8b5cf6',
            'accent_color': '#10b981',
            'background_color': '#ffffff',
            'text_color': '#1f2937',
            'logo_url': 'https://azizi.af/logo.png',
            'favicon_url': 'https://azizi.af/favicon.ico',
            'font_family': 'Inter',
            'footer_text': 'Thank you for shopping with us!',
            'receipt_return_policy': 'For exchanges/returns, present this receipt within 30 days with original packaging.'
        })()

    return render_template('receipt.html', sale=sale, cash_received=cash_received, change_amount=change_amount, branding=branding_settings)

@app.route('/low_stock')
@login_required
def low_stock():
    if not has_permission(current_user, 'view_inventory'):
        flash('Access denied. You do not have permission to view inventory.', 'error')
        return redirect(url_for('dashboard'))

    # Get items with low stock (quantity <= 5 and > 0)
    low_stock_items = Item.query.filter(Item.quantity > 0, Item.quantity <= 5).order_by(Item.quantity.asc()).all()

    # Get out of stock items
    out_of_stock_items = Item.query.filter_by(quantity=0).order_by(Item.name.asc()).all()

    return render_template('low_stock.html',
                         low_stock_items=low_stock_items,
                         out_of_stock_items=out_of_stock_items)



@app.route('/user_guide')
@login_required
def user_guide():
    return render_template('user_guide.html')

@app.route('/admin_guide')
@login_required
def admin_guide():
    # Only admins can access admin guide
    if not has_permission(current_user, 'system_admin'):
        flash('Access denied. Only system administrators can view the admin guide.', 'error')
        return redirect(url_for('dashboard'))

    return render_template('admin_guide.html')

@app.route('/developer_guide')
@login_required
def developer_guide():
    # Only admins can access developer guide
    if not has_permission(current_user, 'system_admin'):
        flash('Access denied. Only system administrators can view the developer guide.', 'error')
        return redirect(url_for('dashboard'))

    return render_template('developer_guide.html')



@app.route('/api/unblock_ip/<ip_address>', methods=['POST'])
@login_required
def unblock_ip(ip_address):
    if not has_permission(current_user, 'system_admin'):
        return jsonify({'error': 'Access denied'}), 403

    blocked_ip = BlockedIP.query.filter_by(ip_address=ip_address).first()
    if blocked_ip:
        db.session.delete(blocked_ip)
        db.session.commit()

        # Log the unblock action
        log_activity(user=current_user, action='ip_unblocked', action_category='security',
                    resource_type='ip_address', resource_name=ip_address,
                    details=f'IP address {ip_address} was manually unblocked by administrator',
                    severity='info', compliance_flag=True)

        return jsonify({'success': True, 'message': f'IP {ip_address} has been unblocked'})
    else:
        return jsonify({'error': 'IP address not found in blocked list'}), 404

# Enhanced Security Monitor API Endpoints
@app.route('/api/security_events')
@login_required
def get_security_events():
    if not has_permission(current_user, 'system_admin'):
        return jsonify({'error': 'Access denied'}), 403

    # Get recent security events (last 5 minutes)
    cutoff_time = datetime.now(timezone.utc) - timedelta(minutes=5)

    recent_attempts = LoginAttempt.query.filter(
        LoginAttempt.attempt_time >= cutoff_time
    ).order_by(LoginAttempt.attempt_time.desc()).all()

    events = []
    for attempt in recent_attempts:
        if attempt.success:
            events.append({
                'type': 'successful_login',
                'title': 'Successful Login',
                'message': f'User {attempt.username} logged in successfully from {attempt.ip_address}',
                'severity': 'low',
                'timestamp': attempt.attempt_time.isoformat(),
                'ip_address': attempt.ip_address,
                'username': attempt.username
            })
        else:
            events.append({
                'type': 'failed_login',
                'title': 'Failed Login Attempt',
                'message': f'Failed login attempt for user {attempt.username} from {attempt.ip_address}',
                'severity': 'medium',
                'timestamp': attempt.attempt_time.isoformat(),
                'ip_address': attempt.ip_address,
                'username': attempt.username
            })

    return jsonify({'new_events': events})

@app.route('/api/security_dashboard_data')
@login_required
def get_security_dashboard_data():
    if not has_permission(current_user, 'system_admin'):
        return jsonify({'error': 'Access denied'}), 403

    # Get data for the last 7 days
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=7)

    # Login attempts over time
    login_data = db.session.query(
        db.func.date(LoginAttempt.attempt_time).label('date'),
        db.func.count(db.case((LoginAttempt.success == True, 1))).label('successful'),
        db.func.count(db.case((LoginAttempt.success == False, 1))).label('failed')
    ).filter(
        LoginAttempt.attempt_time >= start_date
    ).group_by(db.func.date(LoginAttempt.attempt_time)).all()

    # Format dates and data for charts
    dates = []
    successful_logins = []
    failed_attempts = []

    for row in login_data:
        dates.append(row.date.strftime('%Y-%m-%d'))
        successful_logins.append(row.successful)
        failed_attempts.append(row.failed)

    # Geolocation data (simplified - in real implementation you'd use IP geolocation service)
    geolocation_data = db.session.query(
        LoginAttempt.ip_address,
        db.func.count(LoginAttempt.id).label('count')
    ).filter(
        LoginAttempt.attempt_time >= start_date
    ).group_by(LoginAttempt.ip_address).order_by(db.desc('count')).limit(10).all()

    countries = []
    geo_counts = []
    for row in geolocation_data:
        # Simplified country detection - in production use a proper geolocation service
        countries.append(f"IP: {row.ip_address}")
        geo_counts.append(row.count)

    # Current metrics
    current_stats = get_security_stats(hours=24)

    return jsonify({
        'loginAttempts': {
            'labels': dates,
            'successful': successful_logins,
            'failed': failed_attempts
        },
        'geolocation': {
            'countries': countries,
            'counts': geo_counts
        },
        'metrics': {
            'totalAttempts': current_stats['total_attempts'],
            'successfulLogins': current_stats['successful_logins'],
            'failedAttempts': current_stats['failed_attempts'],
            'blockedIPs': current_stats['currently_blocked'],
            'successRate': f"{current_stats['success_rate']:.1f}%"
        }
    })

@app.route('/api/security_data')
@login_required
def get_security_data():
    if not has_permission(current_user, 'system_admin'):
        return jsonify({'error': 'Access denied'}), 403

    # Get filter parameters
    date_from = request.args.get('dateFrom')
    date_to = request.args.get('dateTo')
    severity = request.args.get('severity')
    ip_address = request.args.get('ipAddress')
    username = request.args.get('username')

    # Build query
    query = LoginAttempt.query

    if date_from:
        query = query.filter(LoginAttempt.attempt_time >= date_from)
    if date_to:
        query = query.filter(LoginAttempt.attempt_time <= date_to + ' 23:59:59')
    if ip_address:
        query = query.filter(LoginAttempt.ip_address == ip_address)
    if username:
        query = query.filter(LoginAttempt.username == username)

    # Apply severity filtering based on success/failure patterns
    if severity:
        if severity == 'high':
            # High severity: multiple failed attempts from same IP
            query = query.filter(LoginAttempt.success == False)
        elif severity == 'medium':
            # Medium severity: failed attempts
            query = query.filter(LoginAttempt.success == False)
        elif severity == 'low':
            # Low severity: successful logins
            query = query.filter(LoginAttempt.success == True)

    attempts = query.order_by(LoginAttempt.attempt_time.desc()).limit(1000).all()

    return jsonify({
        'attempts': [{
            'id': attempt.id,
            'username': attempt.username,
            'ip_address': attempt.ip_address,
            'success': attempt.success,
            'attempt_time': attempt.attempt_time.isoformat(),
            'user_agent': attempt.user_agent,
            'failure_reason': attempt.failure_reason,
            'captcha_required': attempt.captcha_required,
            'captcha_solved': attempt.captcha_solved
        } for attempt in attempts],
        'total_count': query.count()
    })

@app.route('/api/security_alerts', methods=['GET', 'POST'])
@login_required
def security_alerts():
    if not has_permission(current_user, 'system_admin'):
        return jsonify({'error': 'Access denied'}), 403

    if request.method == 'GET':
        # Return current alert settings (simplified - in production you'd store these in DB)
        return jsonify({
            'failedLoginThreshold': 5,
            'suspiciousIPThreshold': 10,
            'enableEmailAlerts': True,
            'enableRealTimeAlerts': True,
            'alertEmail': 'admin@example.com'
        })

    elif request.method == 'POST':
        # Save alert settings
        data = request.get_json()

        # In a real implementation, you'd save these to a database
        # For now, just return success
        return jsonify({
            'success': True,
            'message': 'Security alert settings updated successfully'
        })

@app.route('/api/security_threat_analysis')
@login_required
def get_security_threat_analysis():
    if not has_permission(current_user, 'system_admin'):
        return jsonify({'error': 'Access denied'}), 403

    # Analyze current threat levels
    now = datetime.now(timezone.utc)
    last_hour = now - timedelta(hours=1)
    last_24h = now - timedelta(hours=24)

    # Failed login attempts in last hour
    recent_failed = LoginAttempt.query.filter(
        LoginAttempt.success == False,
        LoginAttempt.attempt_time >= last_hour
    ).count()

    # Failed login attempts in last 24 hours
    daily_failed = LoginAttempt.query.filter(
        LoginAttempt.success == False,
        LoginAttempt.attempt_time >= last_24h
    ).count()

    # Currently blocked IPs
    blocked_count = BlockedIP.query.filter(
        BlockedIP.blocked_until > now
    ).count()

    # Calculate threat level
    threat_score = 0
    if recent_failed > 10:
        threat_score += 3
    elif recent_failed > 5:
        threat_score += 2
    elif recent_failed > 2:
        threat_score += 1

    if daily_failed > 50:
        threat_score += 3
    elif daily_failed > 25:
        threat_score += 2
    elif daily_failed > 10:
        threat_score += 1

    if blocked_count > 5:
        threat_score += 2
    elif blocked_count > 2:
        threat_score += 1

    # Determine threat level
    if threat_score >= 6:
        threat_level = 'critical'
    elif threat_score >= 4:
        threat_level = 'high'
    elif threat_score >= 2:
        threat_level = 'medium'
    else:
        threat_level = 'low'

    return jsonify({
        'threat_level': threat_level,
        'threat_score': threat_score,
        'metrics': {
            'recent_failed_attempts': recent_failed,
            'daily_failed_attempts': daily_failed,
            'blocked_ips': blocked_count
        },
        'recommendations': get_security_recommendations(threat_level)
    })

def get_security_recommendations(threat_level):
    """Get security recommendations based on threat level"""
    recommendations = {
        'low': [
            'Continue monitoring login attempts',
            'Regular security audits recommended'
        ],
        'medium': [
            'Increase monitoring frequency',
            'Review recent failed login attempts',
            'Consider enabling additional security measures'
        ],
        'high': [
            'Immediate attention required',
            'Review and potentially block suspicious IPs',
            'Enable enhanced security features',
            'Monitor user accounts for compromise'
        ],
        'critical': [
            'URGENT: Security breach possible',
            'Block all suspicious IPs immediately',
            'Enable maximum security measures',
            'Review all recent user activities',
            'Consider temporary system lockdown',
            'Contact security team immediately'
        ]
    }

    return recommendations.get(threat_level, [])

def get_security_stats(hours=24):
    """Get security statistics for the specified number of hours"""
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

    # Total login attempts
    total_attempts = LoginAttempt.query.filter(
        LoginAttempt.attempt_time >= cutoff_time
    ).count()

    # Successful logins
    successful_logins = LoginAttempt.query.filter(
        LoginAttempt.success == True,
        LoginAttempt.attempt_time >= cutoff_time
    ).count()

    # Failed login attempts
    failed_attempts = LoginAttempt.query.filter(
        LoginAttempt.success == False,
        LoginAttempt.attempt_time >= cutoff_time
    ).count()

    # CAPTCHA required attempts
    captcha_required = LoginAttempt.query.filter(
        LoginAttempt.captcha_required == True,
        LoginAttempt.attempt_time >= cutoff_time
    ).count()

    # CAPTCHA solved attempts
    captcha_solved = LoginAttempt.query.filter(
        LoginAttempt.captcha_solved == True,
        LoginAttempt.attempt_time >= cutoff_time
    ).count()

    # Unique IPs attempting login
    unique_ips = db.session.query(LoginAttempt.ip_address).filter(
        LoginAttempt.attempt_time >= cutoff_time
    ).distinct().count()

    # Currently blocked IPs
    currently_blocked = BlockedIP.query.filter(
        BlockedIP.blocked_until > datetime.now(timezone.utc)
    ).count()

    return {
        'total_attempts': total_attempts,
        'successful_logins': successful_logins,
        'failed_attempts': failed_attempts,
        'success_rate': (successful_logins / total_attempts * 100) if total_attempts > 0 else 0,
        'captcha_required': captcha_required,
        'captcha_solved': captcha_solved,
        'unique_ips': unique_ips,
        'currently_blocked': currently_blocked,
        'period_hours': hours
    }

@app.route('/reset_system', methods=['POST'])
@login_required
def reset_system():
    # Only admins can reset the system
    if not has_permission(current_user, 'system_admin'):
        return jsonify({'error': 'Access denied. Only system administrators can reset the system.'}), 403

    try:
        # Log the reset action before proceeding
        log_activity(user=current_user, action='system_reset', action_category='system',
                    resource_type='system', details='System reset initiated by administrator',
                    severity='critical', compliance_flag=True)

        # Import and run the database recreation script
        from recreate_db import create_tables as recreate_database

        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()

        # Run the create_tables function to set up default data
        recreate_database()

        # Log successful reset
        log_activity(user=None, action='system_reset', action_category='system',
                    resource_type='system', details='System reset completed successfully',
                    severity='info', compliance_flag=True)

        return jsonify({
            'success': True,
            'message': 'System reset completed successfully. All data has been cleared and default settings restored.'
        })

    except Exception as e:
        # Log the error
        log_activity(user=current_user, action='system_reset_failed', action_category='system',
                    resource_type='system', details=f'System reset failed: {str(e)}',
                    status='error', error_message=str(e), severity='critical', compliance_flag=True)

        return jsonify({
            'success': False,
            'error': f'System reset failed: {str(e)}'
        }), 500

@app.route('/activity_logs')
@login_required
def activity_logs():
    # Only admins can access activity logs
    if not has_permission(current_user, 'system_admin'):
        flash('Access denied. Only system administrators can view activity logs.', 'error')
        return redirect(url_for('dashboard'))

    # Get filter parameters
    user_filter = request.args.get('user')
    action_filter = request.args.get('action')
    resource_type_filter = request.args.get('resource_type')
    status_filter = request.args.get('status')
    category_filter = request.args.get('category')
    severity_filter = request.args.get('severity')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    page = int(request.args.get('page', 1))
    per_page = 50

    # Build query
    query = ActivityLog.query

    if user_filter:
        query = query.filter_by(username=user_filter)
    if action_filter:
        query = query.filter_by(action=action_filter)
    if resource_type_filter:
        query = query.filter_by(resource_type=resource_type_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if category_filter:
        query = query.filter_by(action_category=category_filter)
    if severity_filter:
        query = query.filter_by(severity=severity_filter)
    if from_date:
        query = query.filter(ActivityLog.created_at >= from_date)
    if to_date:
        query = query.filter(ActivityLog.created_at <= to_date + ' 23:59:59')

    # Get total count for pagination
    total_logs = query.count()
    total_pages = (total_logs + per_page - 1) // per_page

    # Get paginated results
    activity_logs = query.order_by(ActivityLog.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()

    # Get filter options
    users = db.session.query(ActivityLog.username).distinct().all()
    users = [user[0] for user in users]

    actions = db.session.query(ActivityLog.action).distinct().all()
    actions = [action[0] for action in actions]

    resource_types = db.session.query(ActivityLog.resource_type).distinct().all()
    resource_types = [rt[0] for rt in resource_types if rt[0]]

    categories = db.session.query(ActivityLog.action_category).distinct().all()
    categories = [cat[0] for cat in categories if cat[0]]

    severities = ['info', 'warning', 'error', 'critical']

    # Get statistics
    stats = get_activity_stats()

    return render_template('activity_logs.html',
                         activity_logs=activity_logs,
                         stats=stats,
                         users=users,
                         actions=actions,
                         resource_types=resource_types,
                         categories=categories,
                         severities=severities,
                         current_page=page,
                         total_pages=total_pages,
                         filters={
                             'user': user_filter,
                             'action': action_filter,
                             'resource_type': resource_type_filter,
                             'status': status_filter,
                             'category': category_filter,
                             'severity': severity_filter,
                             'from_date': from_date,
                             'to_date': to_date
                         },
                         max=max,
                         min=min)

@app.route('/export_activity_logs/<format>')
@login_required
def export_activity_logs(format):
    # Only admins can export activity logs
    if not has_permission(current_user, 'system_admin'):
        flash('Access denied. Only system administrators can export activity logs.', 'error')
        return redirect(url_for('dashboard'))

    # Get filter parameters
    user_filter = request.args.get('user')
    action_filter = request.args.get('action')
    resource_type_filter = request.args.get('resource_type')
    status_filter = request.args.get('status')
    category_filter = request.args.get('category')
    severity_filter = request.args.get('severity')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    # Build query
    query = ActivityLog.query

    if user_filter:
        query = query.filter_by(username=user_filter)
    if action_filter:
        query = query.filter_by(action=action_filter)
    if resource_type_filter:
        query = query.filter_by(resource_type=resource_type_filter)
    if status_filter:
        query = query.filter_by(status=status_filter)
    if category_filter:
        query = query.filter_by(action_category=category_filter)
    if severity_filter:
        query = query.filter_by(severity=severity_filter)
    if from_date:
        query = query.filter(ActivityLog.created_at >= from_date)
    if to_date:
        query = query.filter(ActivityLog.created_at <= to_date + ' 23:59:59')

    # Get all matching logs (limit to prevent memory issues)
    activity_logs = query.order_by(ActivityLog.created_at.desc()).limit(10000).all()

    if format == 'csv':
        return export_activity_logs_csv(activity_logs)
    elif format == 'pdf':
        return export_activity_logs_pdf(activity_logs)
    else:
        flash('Invalid export format.', 'error')
        return redirect(url_for('activity_logs'))

def export_activity_logs_csv(activity_logs):
    """Export activity logs to CSV format"""
    import csv
    import io
    from flask import Response

    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'Timestamp', 'Username', 'Action Category', 'Action', 'Resource Type',
        'Resource Name', 'Details', 'Status', 'Severity', 'IP Address',
        'Terminal ID', 'Session ID', 'Compliance Flag'
    ])

    # Write data
    for log in activity_logs:
        writer.writerow([
            log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            log.username,
            log.action_category,
            log.action,
            log.resource_type,
            log.resource_name or '',
            log.details or '',
            log.status,
            log.severity,
            log.ip_address or '',
            log.terminal_id or '',
            log.session_id or '',
            'Yes' if log.compliance_flag else 'No'
        ])

    output.seek(0)

    # Log the export
    log_activity(user=current_user, action='export_logs', action_category='system',
                resource_type='activity_log', details=f'Exported {len(activity_logs)} activity logs to CSV')

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=activity_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'}
    )

def export_activity_logs_pdf(activity_logs):
    """Export activity logs to PDF format"""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from flask import Response
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []

        styles = getSampleStyleSheet()

        # Title
        title = Paragraph("Activity Logs Report", styles['Heading1'])
        elements.append(title)
        elements.append(Spacer(1, 12))

        # Report info
        report_info = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>Total Records: {len(activity_logs)}", styles['Normal'])
        elements.append(report_info)
        elements.append(Spacer(1, 20))

        # Table data
        data = [['Timestamp', 'User', 'Action', 'Resource', 'Status', 'Severity']]

        for log in activity_logs[:1000]:  # Limit for PDF generation
            data.append([
                log.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                log.username,
                log.action,
                log.resource_type,
                log.status,
                log.severity
            ])

        # Create table
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))

        elements.append(table)

        # Build PDF
        doc.build(elements)
        buffer.seek(0)

        # Log the export
        log_activity(user=current_user, action='export_logs', action_category='system',
                    resource_type='activity_log', details=f'Exported {len(activity_logs)} activity logs to PDF')

        return Response(
            buffer.getvalue(),
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename=activity_logs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'}
        )

    except ImportError:
        flash('PDF export requires reportlab. Please install it: pip install reportlab', 'error')
        return redirect(url_for('activity_logs'))
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('activity_logs'))

@app.route('/branding', methods=['GET', 'POST'])
@login_required
def branding():
    # Only admins can access branding management
    if not has_permission(current_user, 'system_admin'):
        flash('Access denied. Only system administrators can manage branding.', 'error')
        return redirect(url_for('dashboard'))

    # Get the single branding record (singleton pattern)
    try:
        branding_settings = Branding.query.first()
        if not branding_settings:
            # Create the single branding record if it doesn't exist
            branding_settings = Branding()
            db.session.add(branding_settings)
            db.session.commit()
            print("Created single branding record")
    except Exception as e:
        print(f"Error querying branding table: {e}")
        # Create a default branding object for the template
        branding_settings = type('Branding', (), {
            'app_name': 'POS System',
            'app_subtitle': 'Professional Point of Sale',
            'business_name': '',
            'business_address': '',
            'business_phone': '',
            'business_email': '',
            'tax_id': '',
            'primary_color': '#6366f1',
            'secondary_color': '#8b5cf6',
            'accent_color': '#10b981',
            'background_color': '#ffffff',
            'text_color': '#1f2937',
            'font_family': 'Inter',
            'logo_url': '',
            'favicon_url': '',
            'footer_text': 'Thank you for your business!',
            'receipt_return_policy': 'For exchanges/returns, present this receipt within 30 days.',
            'receipt_header_title': 'RECEIPT',
            'receipt_number_label': 'Receipt #:',
            'date_label': 'Date:',
            'cashier_label': 'Cashier:',
            'payment_method_label': 'Payment Method:',
            'payment_method_value': 'Cash',
            'cash_received_label': 'Cash Received:',
            'change_label': 'Change:',
            'currency_symbol': 'AFA',
            'item_header': 'Item',
            'quantity_header': 'Qty',
            'amount_header': 'Amount',
            'subtotal_label': 'Subtotal:',
            'discount_label': 'Discount',
            'total_label': 'TOTAL:',
            'records_message': 'Please keep this receipt for your records.',
            'powered_by_label': 'Powered by',
            'version_text': 'v1.0'
        })()

    if request.method == 'POST':
        # Update the single branding record
        try:
            # Ensure we have a real SQLAlchemy object
            if not hasattr(branding_settings, 'id') or branding_settings.id is None:
                # If we have a mock object, get the real one from database
                real_branding = Branding.query.first()
                if real_branding:
                    branding_settings = real_branding
                else:
                    # Create new branding record
                    branding_settings = Branding()
                    db.session.add(branding_settings)

            # Update all branding settings - ALL FIELDS ARE OPTIONAL with sensible defaults

            # App Branding (required with defaults)
            app_name = request.form.get('app_name', '').strip()
            branding_settings.app_name = app_name if app_name else 'POS System'

            app_subtitle = request.form.get('app_subtitle', '').strip()
            branding_settings.app_subtitle = app_subtitle if app_subtitle else 'Professional Point of Sale'

            # Business Information (all optional - can be empty/null)
            branding_settings.business_name = request.form.get('business_name', '').strip() or None
            branding_settings.business_address = request.form.get('business_address', '').strip() or None
            branding_settings.business_phone = request.form.get('business_phone', '').strip() or None
            branding_settings.business_email = request.form.get('business_email', '').strip() or None
            branding_settings.tax_id = request.form.get('tax_id', '').strip() or None

            # Theme Colors (required with defaults)
            branding_settings.primary_color = request.form.get('primary_color', '').strip() or '#6366f1'
            branding_settings.secondary_color = request.form.get('secondary_color', '').strip() or '#8b5cf6'
            branding_settings.accent_color = request.form.get('accent_color', '').strip() or '#10b981'
            branding_settings.background_color = request.form.get('background_color', '').strip() or '#ffffff'
            branding_settings.text_color = request.form.get('text_color', '').strip() or '#1f2937'

            # Typography (required with default)
            branding_settings.font_family = request.form.get('font_family', '').strip() or 'Inter'

            # Assets (optional - can be empty/null)
            logo_url = request.form.get('logo_url', '').strip()
            branding_settings.logo_url = logo_url if logo_url and logo_url != 'https://example.com/logo.png' else None

            favicon_url = request.form.get('favicon_url', '').strip()
            branding_settings.favicon_url = favicon_url if favicon_url and favicon_url != 'https://example.com/favicon.ico' else None

            # Footer Text (optional with default)
            footer_text = request.form.get('footer_text', '').strip()
            branding_settings.footer_text = footer_text if footer_text else 'Thank you for your business!'

            # Receipt Settings (all optional with defaults)
            receipt_return_policy = request.form.get('receipt_return_policy', '').strip()
            branding_settings.receipt_return_policy = receipt_return_policy if receipt_return_policy else 'For exchanges/returns, present this receipt within 30 days.'

            records_message = request.form.get('records_message', '').strip()
            branding_settings.records_message = records_message if records_message else 'Please keep this receipt for your records.'

            # Receipt Labels (all optional with defaults)
            branding_settings.receipt_number_label = request.form.get('receipt_number_label', '').strip() or 'Receipt #:'
            branding_settings.date_label = request.form.get('date_label', '').strip() or 'Date:'
            branding_settings.cashier_label = request.form.get('cashier_label', '').strip() or 'Cashier:'
            branding_settings.payment_method_label = request.form.get('payment_method_label', '').strip() or 'Payment Method:'
            branding_settings.payment_method_value = request.form.get('payment_method_value', '').strip() or 'Cash'
            branding_settings.cash_received_label = request.form.get('cash_received_label', '').strip() or 'Cash Received:'
            branding_settings.change_label = request.form.get('change_label', '').strip() or 'Change:'
            branding_settings.currency_symbol = request.form.get('currency_symbol', '').strip() or 'AFA'

            # Receipt Table Headers (all optional with defaults)
            branding_settings.item_header = request.form.get('item_header', '').strip() or 'Item'
            branding_settings.quantity_header = request.form.get('quantity_header', '').strip() or 'Qty'
            branding_settings.amount_header = request.form.get('amount_header', '').strip() or 'Amount'

            # Receipt Totals (all optional with defaults)
            branding_settings.subtotal_label = request.form.get('subtotal_label', '').strip() or 'Subtotal:'
            branding_settings.discount_label = request.form.get('discount_label', '').strip() or 'Discount'
            branding_settings.total_label = request.form.get('total_label', '').strip() or 'TOTAL:'

            # Receipt Footer Branding (all optional with defaults)
            branding_settings.powered_by_label = request.form.get('powered_by_label', '').strip() or 'Powered by'
            branding_settings.version_text = request.form.get('version_text', '').strip() or 'v1.0'

            db.session.commit()

            # Log branding update
            if hasattr(branding_settings, 'id') and branding_settings.id:
                log_activity(user=current_user, action='branding_update', resource_type='branding',
                            resource_id=branding_settings.id, resource_name='Branding Settings',
                            details=f'Updated branding settings: app_name={branding_settings.app_name}')

            flash('Branding settings updated successfully!', 'success')
            return redirect(url_for('branding'))

        except Exception as e:
            print(f"Error updating branding: {e}")
            db.session.rollback()
            flash('Error updating branding settings. Please try again.', 'error')
            return redirect(url_for('branding'))

    return render_template('branding.html', branding=branding_settings)

@app.route('/api/branding')
@login_required
def get_branding():
    # Get branding settings with defaults
    branding_settings = Branding.query.first()

    if not branding_settings:
        # Return default branding
        return jsonify({
            'app_name': 'POS System',
            'app_subtitle': 'Professional Point of Sale',
            'business_name': None,
            'business_address': None,
            'business_phone': None,
            'business_email': None,
            'tax_id': None,
            'primary_color': '#6366f1',
            'secondary_color': '#8b5cf6',
            'accent_color': '#10b981',
            'background_color': '#ffffff',
            'text_color': '#1f2937',
            'font_family': 'Inter',
            'logo_url': None,
            'favicon_url': None,
            'footer_text': 'Thank you for your business!'
        })

    return jsonify({
        'app_name': branding_settings.app_name,
        'app_subtitle': branding_settings.app_subtitle,
        'business_name': branding_settings.business_name,
        'business_address': branding_settings.business_address,
        'business_phone': branding_settings.business_phone,
        'business_email': branding_settings.business_email,
        'tax_id': branding_settings.tax_id,
        'primary_color': branding_settings.primary_color,
        'secondary_color': branding_settings.secondary_color,
        'accent_color': branding_settings.accent_color,
        'background_color': branding_settings.background_color,
        'text_color': branding_settings.text_color,
        'font_family': branding_settings.font_family,
        'logo_url': branding_settings.logo_url,
        'favicon_url': branding_settings.favicon_url,
        'footer_text': branding_settings.footer_text
    })

# Activity Logging System
def log_activity(user=None, action='', action_category='system', resource_type='', resource_id=None,
                resource_name='', details='', old_value=None, new_value=None, status='success',
                error_message='', severity='info', compliance_flag=False, terminal_id=None, location=None,
                additional_data=None):
    """Log user activity and system events with comprehensive tracking and detailed context"""
    try:
        # Get client information
        ip_address = request.remote_addr if request else None
        user_agent = request.headers.get('User-Agent') if request else None
        session_id = session.get('session_id', str(uuid.uuid4())[:8]) if session else str(uuid.uuid4())[:8]

        # Handle user information
        user_id = user.id if user and hasattr(user, 'id') else None
        username = user.username if user and hasattr(user, 'username') else 'system'

        # Generate terminal ID if not provided
        if not terminal_id:
            terminal_id = session.get('terminal_id') if session else f'TERM-{uuid.uuid4().hex[:8].upper()}'

        # Set retention date based on compliance and severity
        retention_days = 365  # Default 1 year
        if compliance_flag or severity in ['error', 'critical']:
            retention_days = 2555  # 7 years for compliance/critical events
        elif severity == 'warning':
            retention_days = 1095  # 3 years for warnings

        retention_date = datetime.now(timezone.utc) + timedelta(days=retention_days)

        # Enhance details with more context based on action type
        enhanced_details = enhance_log_details(action, action_category, resource_type, details, old_value, new_value, additional_data)

        # Create activity log entry
        activity_log = ActivityLog(
            user_id=user_id,
            username=username,
            action=action,
            action_category=action_category,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            details=enhanced_details,
            old_value=old_value,
            new_value=new_value,
            ip_address=ip_address,
            user_agent=user_agent[:500] if user_agent else None,
            session_id=session_id,
            terminal_id=terminal_id,
            location=location,
            status=status,
            error_message=error_message[:500] if error_message else None,
            severity=severity,
            compliance_flag=compliance_flag,
            retention_date=retention_date
        )

        db.session.add(activity_log)
        db.session.commit()

    except Exception as e:
        # Log the error but don't fail the main operation
        print(f"Error logging activity: {str(e)}")
        # Don't commit here to avoid nested transaction issues

def enhance_log_details(action, action_category, resource_type, details, old_value, new_value, additional_data):
    """Enhance log details with more contextual information based on action type"""
    enhanced_details = details or ""

    # Add contextual information based on action and resource type
    if action_category == 'auth':
        if action == 'login':
            enhanced_details = f"User logged into the system successfully"
        elif action == 'logout':
            enhanced_details = f"User logged out of the system"
        elif action == 'login_failed':
            enhanced_details = f"Failed login attempt - invalid credentials provided"
        elif action == 'password_change':
            enhanced_details = f"User changed their password"
        elif action == 'profile_update':
            enhanced_details = f"User updated their profile information"

    elif action_category == 'inventory':
        if action == 'item_create':
            enhanced_details = f"Added new item to inventory with barcode and pricing information"
        elif action == 'item_update':
            enhanced_details = f"Modified item details (price, quantity, or other attributes)"
        elif action == 'item_delete':
            enhanced_details = f"Removed item from inventory system"
        elif action == 'category_create':
            enhanced_details = f"Created new product category for inventory organization"
        elif action == 'category_update':
            enhanced_details = f"Modified category information or settings"
        elif action == 'category_delete':
            enhanced_details = f"Removed category and potentially reassigned items"

    elif action_category == 'sales':
        if action == 'sale_create':
            enhanced_details = f"Completed customer transaction with receipt generation"
        elif action == 'sale_view':
            enhanced_details = f"Accessed sale transaction details for review"

    elif action_category == 'user_management':
        if action == 'user_create':
            enhanced_details = f"Created new user account with specified role and permissions"
        elif action == 'user_update':
            enhanced_details = f"Modified user account details or permissions"
        elif action == 'user_delete':
            enhanced_details = f"Removed user account from the system"
        elif action == 'permission_change':
            enhanced_details = f"Modified user permissions or role assignments"

    elif action_category == 'system':
        if action == 'backup_create':
            enhanced_details = f"Created system backup for data protection"
        elif action == 'backup_download':
            enhanced_details = f"Downloaded system backup file"
        elif action == 'backup_restore':
            enhanced_details = f"Restored system from backup file"
        elif action == 'branding_update':
            enhanced_details = f"Updated system branding and appearance settings"
        elif action == 'export_logs':
            enhanced_details = f"Exported activity logs for compliance or review purposes"

    # Add additional context from additional_data if provided
    if additional_data:
        if isinstance(additional_data, dict):
            context_parts = []
            for key, value in additional_data.items():
                if key == 'ip_address' and value:
                    context_parts.append(f"from IP {value}")
                elif key == 'user_agent' and value:
                    browser_info = extract_browser_info(value)
                    if browser_info:
                        context_parts.append(f"using {browser_info}")
                elif key == 'items_count' and value:
                    context_parts.append(f"affecting {value} items")
                elif key == 'total_amount' and value:
                    context_parts.append(f"total value: {value}")
                elif key == 'changes_made' and value:
                    context_parts.append(f"changes: {value}")

            if context_parts:
                enhanced_details += f" ({', '.join(context_parts)})"

    return enhanced_details

def extract_browser_info(user_agent):
    """Extract readable browser information from user agent string"""
    if not user_agent:
        return None

    user_agent = user_agent.lower()

    browsers = {
        'chrome': 'Chrome',
        'firefox': 'Firefox',
        'safari': 'Safari',
        'edge': 'Edge',
        'opera': 'Opera'
    }

    for browser_key, browser_name in browsers.items():
        if browser_key in user_agent:
            return browser_name

    return "Web Browser"

def get_activity_logs(user_id=None, action=None, resource_type=None,
                     status=None, limit=100, offset=0):
    """Retrieve activity logs with optional filtering"""
    query = ActivityLog.query

    if user_id:
        query = query.filter_by(user_id=user_id)
    if action:
        query = query.filter_by(action=action)
    if resource_type:
        query = query.filter_by(resource_type=resource_type)
    if status:
        query = query.filter_by(status=status)

    return query.order_by(ActivityLog.created_at.desc()).limit(limit).offset(offset).all()

def get_activity_stats(days=30):
    """Get activity statistics for the specified number of days"""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Total activities
    total_activities = ActivityLog.query.filter(
        ActivityLog.created_at >= cutoff_date
    ).count()

    # Activities by action
    action_stats = db.session.query(
        ActivityLog.action,
        db.func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.created_at >= cutoff_date
    ).group_by(ActivityLog.action).all()

    # Activities by user
    user_stats = db.session.query(
        ActivityLog.username,
        db.func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.created_at >= cutoff_date
    ).group_by(ActivityLog.username).all()

    # Error activities
    error_count = ActivityLog.query.filter(
        ActivityLog.created_at >= cutoff_date,
        ActivityLog.status == 'error'
    ).count()

    return {
        'total_activities': total_activities,
        'action_stats': dict(action_stats),
        'user_stats': dict(user_stats),
        'error_count': error_count,
        'period_days': days
    }

# Create database tables
def create_tables():
    with app.app_context():
        db.create_all()

        # Create default admin user if not exists
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)

        if not User.query.filter_by(username='cashier').first():
            cashier = User(username='cashier', role='cashier')
            cashier.set_password('cashier123')
            db.session.add(cashier)

        # Create default branding settings if not exists
        try:
            if not Branding.query.first():
                default_branding = Branding()
                db.session.add(default_branding)
        except Exception as e:
            # If there's an error (likely due to missing column), create branding with raw SQL
            print(f"Error querying branding table: {e}")
            print("Creating default branding settings with raw SQL...")
            db.session.execute(db.text("""
                INSERT OR IGNORE INTO branding (
                    app_name, app_subtitle, business_name, business_address,
                    business_phone, business_email, tax_id, primary_color,
                    secondary_color, accent_color, background_color, text_color,
                    logo_url, favicon_url, font_family, footer_text,
                    created_at, updated_at
                ) VALUES (
                    'POS System', 'Professional Point of Sale', NULL, NULL,
                    NULL, NULL, NULL, '#6366f1',
                    '#8b5cf6', '#10b981', '#ffffff', '#1f2937',
                    NULL, NULL, 'Inter', 'Thank you for your business!',
                    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            """))

        db.session.commit()

# Database migration function to handle schema updates
def migrate_database():
    """Migrate database schema to handle missing columns from older backups"""
    with app.app_context():
        import sqlite3
        from sqlalchemy import text

        try:
            # Connect to database directly for schema inspection
            db_path = 'instance/pos.db'
            if not os.path.exists(db_path):
                return

            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if item table has category_id column
            cursor.execute("PRAGMA table_info(item)")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]

            # Add category_id column if missing
            if 'category_id' not in column_names:
                print("Adding category_id column to item table...")
                cursor.execute("ALTER TABLE item ADD COLUMN category_id INTEGER REFERENCES category(id)")
                conn.commit()

            # Check if item table has expiry_date column
            if 'expiry_date' not in column_names:
                print("Adding expiry_date column to item table...")
                cursor.execute("ALTER TABLE item ADD COLUMN expiry_date DATE")
                conn.commit()

            # Check if user table has secret_question and secret_answer columns
            cursor.execute("PRAGMA table_info(user)")
            user_columns = cursor.fetchall()
            user_column_names = [col[1] for col in user_columns]

            if 'secret_question' not in user_column_names:
                print("Adding secret_question column to user table...")
                cursor.execute("ALTER TABLE user ADD COLUMN secret_question VARCHAR(200)")
                conn.commit()

            if 'secret_answer' not in user_column_names:
                print("Adding secret_answer column to user table...")
                cursor.execute("ALTER TABLE user ADD COLUMN secret_answer VARCHAR(200)")
                conn.commit()

            # Check if branding table exists and has all required columns
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='branding'")
            if not cursor.fetchone():
                print("Creating branding table...")
                cursor.execute("""
                    CREATE TABLE branding (
                        id INTEGER PRIMARY KEY,
                        app_name VARCHAR(100) DEFAULT 'POS System',
                        app_subtitle VARCHAR(200) DEFAULT 'Professional Point of Sale',
                        business_name VARCHAR(200),
                        business_address VARCHAR(500),
                        business_phone VARCHAR(50),
                        business_email VARCHAR(100),
                        tax_id VARCHAR(50),
                        primary_color VARCHAR(7) DEFAULT '#6366f1',
                        secondary_color VARCHAR(7) DEFAULT '#8b5cf6',
                        accent_color VARCHAR(7) DEFAULT '#10b981',
                        background_color VARCHAR(7) DEFAULT '#ffffff',
                        text_color VARCHAR(7) DEFAULT '#1f2937',
                        font_family VARCHAR(100) DEFAULT 'Inter',
                        logo_url VARCHAR(500),
                        favicon_url VARCHAR(500),
                        footer_text VARCHAR(500) DEFAULT 'Thank you for your business!',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()

            # Check if activity_log table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activity_log'")
            if not cursor.fetchone():
                print("Creating activity_log table...")
                cursor.execute("""
                    CREATE TABLE activity_log (
                        id INTEGER PRIMARY KEY,
                        user_id INTEGER REFERENCES user(id),
                        username VARCHAR(80) NOT NULL,
                        action VARCHAR(100) NOT NULL,
                        action_category VARCHAR(50) NOT NULL,
                        resource_type VARCHAR(50) NOT NULL,
                        resource_id INTEGER,
                        resource_name VARCHAR(200),
                        details TEXT,
                        old_value TEXT,
                        new_value TEXT,
                        ip_address VARCHAR(45),
                        user_agent VARCHAR(500),
                        session_id VARCHAR(100),
                        terminal_id VARCHAR(50),
                        location VARCHAR(100),
                        status VARCHAR(20) DEFAULT 'success',
                        error_message TEXT,
                        severity VARCHAR(20) DEFAULT 'info',
                        compliance_flag BOOLEAN DEFAULT 0,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        retention_date DATETIME
                    )
                """)
                conn.commit()

            # Remove backup_schedule table if it exists (cleanup from previous versions)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='backup_schedule'")
            if cursor.fetchone():
                print("Removing backup_schedule table...")
                cursor.execute("DROP TABLE backup_schedule")
                conn.commit()

            conn.close()
            print("Database migration completed successfully!")

        except Exception as e:
            print(f"Database migration failed: {str(e)}")
            # Don't fail the application if migration fails

if __name__ == '__main__':
    create_tables()
    migrate_database()  # Run database migration to handle schema updates
    app.run(debug=True, host='0.0.0.0', port=5000)
