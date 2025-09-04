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

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

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

# Context processor to make branding available globally
@app.context_processor
def inject_branding():
    """Make branding settings available to all templates"""
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
                'footer_text': 'Thank you for your business!'
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
            'footer_text': branding_settings.footer_text
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

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            # Log successful login
            log_activity(user=user, action='login', action_category='auth', resource_type='user',
                        resource_id=user.id, resource_name=user.username,
                        details=f'User {user.username} logged in successfully',
                        severity='info', compliance_flag=True,
                        additional_data={
                            'ip_address': request.remote_addr,
                            'user_agent': request.headers.get('User-Agent')
                        })
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            # Log failed login attempt
            log_activity(user=None, action='login_failed', action_category='auth', resource_type='user',
                        resource_name=form.username.data,
                        details=f'Failed login attempt for username: {form.username.data}',
                        status='error', error_message='Invalid username or password',
                        severity='warning', compliance_flag=True)
            flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

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
    total_items = Item.query.count()
    out_of_stock = Item.query.filter_by(quantity=0).count()
    low_stock = Item.query.filter(Item.quantity > 0, Item.quantity <= 5).count()

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

            # Validate new password
            if len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'error')
                return redirect(url_for('profile'))

            # Check if passwords match
            if new_password != confirm_password:
                flash('New passwords do not match.', 'error')
                return redirect(url_for('profile'))

            # Update password
            current_user.set_password(new_password)
            db.session.commit()
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

    # Get branding settings
    branding_settings = Branding.query.first()
    if not branding_settings:
        branding_settings = Branding()

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

    # Get branding settings
    branding_settings = Branding.query.first()
    if not branding_settings:
        branding_settings = Branding()

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

@app.route('/backup')
@login_required
def backup():
    if not has_permission(current_user, 'system_admin'):
        flash('Access denied. Only system administrators can access backup functionality.', 'error')
        return redirect(url_for('dashboard'))

    return render_template('backup.html')

@app.route('/download_backup')
@login_required
def download_backup():
    if not has_permission(current_user, 'system_admin'):
        flash('Access denied. Only system administrators can download backups.', 'error')
        return redirect(url_for('dashboard'))

    import os
    from flask import send_file
    from datetime import datetime

    db_path = 'instance/pos.db'

    if not os.path.exists(db_path):
        flash('Database file not found.', 'error')
        return redirect(url_for('backup'))

    # Create backup filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'pos_backup_{timestamp}.db'

    try:
        return send_file(
            db_path,
            as_attachment=True,
            download_name=backup_filename,
            mimetype='application/octet-stream'
        )
    except Exception as e:
        flash(f'Error creating backup: {str(e)}', 'error')
        return redirect(url_for('backup'))

@app.route('/create_backup', methods=['POST'])
@login_required
def create_backup():
    if not has_permission(current_user, 'system_admin'):
        return jsonify({'error': 'Access denied. Only system administrators can create backups.'}), 403

    import os
    import shutil
    from datetime import datetime

    try:
        # Ensure backup directory exists
        backup_dir = 'backups'
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)

        # Create backup filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f'pos_backup_{timestamp}.db'
        backup_path = os.path.join(backup_dir, backup_filename)

        # Copy database file
        db_path = 'instance/pos.db'
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)

            # Get backup file size
            file_size = os.path.getsize(backup_path)
            file_size_mb = file_size / (1024 * 1024)

            # Create backup metadata
            metadata = {
                'filename': backup_filename,
                'created_at': datetime.now().isoformat(),
                'size_bytes': file_size,
                'size_mb': round(file_size_mb, 2),
                'created_by': current_user.username,
                'version': '1.0'
            }

            # Save metadata
            metadata_path = backup_path + '.meta'
            with open(metadata_path, 'w') as f:
                import json
                json.dump(metadata, f, indent=2)

            return jsonify({
                'success': True,
                'message': f'Backup created successfully: {backup_filename}',
                'filename': backup_filename,
                'size': f'{file_size_mb:.2f} MB',
                'path': backup_path,
                'metadata': metadata
            })
        else:
            return jsonify({'error': 'Database file not found.'}), 404

    except Exception as e:
        return jsonify({'error': f'Error creating backup: {str(e)}'}), 500

@app.route('/restore_backup', methods=['POST'])
@login_required
def restore_backup():
    if not has_permission(current_user, 'system_admin'):
        return jsonify({'error': 'Access denied. Only system administrators can restore backups.'}), 403

    import os
    import shutil
    from datetime import datetime
    from werkzeug.utils import secure_filename

    try:
        if 'backup_file' not in request.files:
            return jsonify({'error': 'No backup file provided.'}), 400

        file = request.files['backup_file']
        if file.filename == '':
            return jsonify({'error': 'No file selected.'}), 400

        # Validate file extension
        if not file.filename.endswith('.db'):
            return jsonify({'error': 'Invalid file type. Only .db files are allowed.'}), 400

        # Secure filename
        filename = secure_filename(file.filename)

        # Create temporary backup of current database
        db_path = 'instance/pos.db'
        temp_backup = f'instance/pos_temp_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'

        if os.path.exists(db_path):
            shutil.copy2(db_path, temp_backup)

        # Save uploaded file temporarily
        upload_dir = 'temp_uploads'
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir)

        temp_path = os.path.join(upload_dir, filename)
        file.save(temp_path)

        # Validate the uploaded file (basic check)
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            # Cleanup
            if os.path.exists(temp_path):
                os.remove(temp_path)
            return jsonify({'error': 'Uploaded file is empty or invalid.'}), 400

        # Replace current database
        shutil.copy2(temp_path, db_path)

        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)

        # Clear any cached data
        # Note: In a production app, you might want to restart the application
        # or clear specific caches

        return jsonify({
            'success': True,
            'message': f'Database restored successfully from {filename}',
            'temp_backup': temp_backup,
            'warning': 'Please restart the application to ensure all changes take effect.'
        })

    except Exception as e:
        return jsonify({'error': f'Error restoring backup: {str(e)}'}), 500

@app.route('/list_backups')
@login_required
def list_backups():
    if not has_permission(current_user, 'system_admin'):
        return jsonify({'error': 'Access denied. Only system administrators can list backups.'}), 403

    import os
    import json
    from datetime import datetime

    try:
        backup_dir = 'backups'
        backups = []

        if os.path.exists(backup_dir):
            for filename in os.listdir(backup_dir):
                if filename.endswith('.db'):
                    filepath = os.path.join(backup_dir, filename)
                    metadata_path = filepath + '.meta'

                    # Get file stats
                    stat = os.stat(filepath)
                    size_mb = stat.st_size / (1024 * 1024)

                    # Try to load metadata
                    metadata = {}
                    if os.path.exists(metadata_path):
                        try:
                            with open(metadata_path, 'r') as f:
                                metadata = json.load(f)
                        except:
                            pass

                    backup_info = {
                        'filename': filename,
                        'size_mb': round(size_mb, 2),
                        'created_at': metadata.get('created_at', stat.st_mtime),
                        'created_by': metadata.get('created_by', 'Unknown'),
                        'version': metadata.get('version', 'N/A')
                    }
                    backups.append(backup_info)

        # Sort by creation date (newest first)
        backups.sort(key=lambda x: x['created_at'], reverse=True)

        return jsonify({
            'success': True,
            'backups': backups
        })

    except Exception as e:
        return jsonify({'error': f'Error listing backups: {str(e)}'}), 500

@app.route('/download_specific_backup/<filename>')
@login_required
def download_specific_backup(filename):
    if not has_permission(current_user, 'system_admin'):
        flash('Access denied. Only system administrators can download backups.', 'error')
        return redirect(url_for('backup'))

    import os
    from werkzeug.utils import secure_filename

    try:
        # Security check - only allow .db files
        if not filename.endswith('.db'):
            flash('Invalid file type.', 'error')
            return redirect(url_for('backup'))

        # Secure the filename
        secure_name = secure_filename(filename)

        backup_path = os.path.join('backups', secure_name)

        if not os.path.exists(backup_path):
            flash('Backup file not found.', 'error')
            return redirect(url_for('backup'))

        return send_file(
            backup_path,
            as_attachment=True,
            download_name=secure_name,
            mimetype='application/octet-stream'
        )

    except Exception as e:
        flash(f'Error downloading backup: {str(e)}', 'error')
        return redirect(url_for('backup'))

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
                         })

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

    # Get or create branding settings
    branding_settings = Branding.query.first()
    if not branding_settings:
        branding_settings = Branding()
        db.session.add(branding_settings)
        db.session.commit()

    if request.method == 'POST':
        # Update branding settings
        branding_settings.app_name = request.form.get('app_name', branding_settings.app_name)
        branding_settings.app_subtitle = request.form.get('app_subtitle', branding_settings.app_subtitle)

        # Business information
        branding_settings.business_name = request.form.get('business_name', branding_settings.business_name)
        branding_settings.business_address = request.form.get('business_address', branding_settings.business_address)
        branding_settings.business_phone = request.form.get('business_phone', branding_settings.business_phone)
        branding_settings.business_email = request.form.get('business_email', branding_settings.business_email)
        branding_settings.tax_id = request.form.get('tax_id', branding_settings.tax_id)

        # Theme colors
        branding_settings.primary_color = request.form.get('primary_color', branding_settings.primary_color)
        branding_settings.secondary_color = request.form.get('secondary_color', branding_settings.secondary_color)
        branding_settings.accent_color = request.form.get('accent_color', branding_settings.accent_color)
        branding_settings.background_color = request.form.get('background_color', branding_settings.background_color)
        branding_settings.text_color = request.form.get('text_color', branding_settings.text_color)

        # Typography
        branding_settings.font_family = request.form.get('font_family', branding_settings.font_family)

        # Footer text
        branding_settings.footer_text = request.form.get('footer_text', branding_settings.footer_text)

        # Logo URLs (for now, just text fields)
        branding_settings.logo_url = request.form.get('logo_url', branding_settings.logo_url)
        branding_settings.favicon_url = request.form.get('favicon_url', branding_settings.favicon_url)

        db.session.commit()

        # Log branding update
        log_activity(user=current_user, action='branding_update', resource_type='branding',
                    resource_id=branding_settings.id, resource_name='Branding Settings',
                    details=f'Updated branding settings: app_name={branding_settings.app_name}, business_name={branding_settings.business_name}')

        flash('Branding settings updated successfully!', 'success')
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
        if not Branding.query.first():
            default_branding = Branding()
            db.session.add(default_branding)

        db.session.commit()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, host='0.0.0.0', port=5000)
