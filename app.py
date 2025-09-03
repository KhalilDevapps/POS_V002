from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, IntegerField, FloatField
from wtforms.validators import DataRequired, Length, EqualTo, NumberRange
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, timezone
import os
from dotenv import load_dotenv

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

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    buying_price = db.Column(db.Float, nullable=False)
    selling_price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    barcode = db.Column(db.String(50), unique=True, nullable=False)
    sold_quantity = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    discount_percent = db.Column(db.Float, default=0)
    discount_amount = db.Column(db.Float, default=0)
    final_amount = db.Column(db.Float, nullable=False)
    profit = db.Column(db.Float, nullable=False)
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
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        flash('Invalid username or password', 'error')
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('logout.html')

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
            return redirect(url_for('inventory'))

    items = Item.query.all()
    return render_template('inventory.html', items=items, form=form)

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

    # Create sale record
    sale = Sale(
        user_id=current_user.id,
        total_amount=total_amount,
        discount_percent=discount_percent,
        discount_amount=discount_amount,
        final_amount=final_amount,
        profit=profit
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

    return jsonify({
        'success': True,
        'sale_id': sale.id,
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

    # Update item fields
    if 'name' in data:
        item.name = data['name']
    if 'buying_price' in data:
        item.buying_price = float(data['buying_price'])
    if 'selling_price' in data:
        item.selling_price = float(data['selling_price'])
    if 'quantity' in data:
        item.quantity = int(data['quantity'])

    db.session.commit()
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

        db.session.commit()

if __name__ == '__main__':
    create_tables()
    app.run(debug=True, host='0.0.0.0', port=5000)
