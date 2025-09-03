# POS System - Production Ready Flask Application

A complete Point of Sale (POS) system built with Python Flask, featuring user authentication, role-based access control, inventory management, and sales processing.

## 🚀 Features

- **User Authentication**: Secure login/logout with session management
- **Role-Based Access Control**: Admin and Cashier roles with different permissions
- **Inventory Management**: Add, edit, and track inventory items
- **Sales Processing**: Barcode scanning, cart management, and receipt generation
- **Dashboard**: Real-time metrics and analytics
- **Reports**: Sales reports with date filtering
- **User Management**: Admin can manage users (Admin only)
- **SQLite Database**: Local database for data persistence

## 🛠️ Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **Frontend**: HTML5, CSS3, JavaScript
- **Templates**: Jinja2

## 📋 Prerequisites

- Python 3.8 or higher
- Virtual environment (recommended)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Create virtual environment
python -m venv pos_env

# Activate virtual environment
pos_env\Scripts\activate  # Windows
# or
source pos_env/bin/activate  # Linux/Mac

# Install dependencies
pip install flask flask-sqlalchemy flask-login flask-wtf werkzeug bcrypt python-dotenv
```

### 2. Run the Application

```bash
python app.py
```

The application will be available at: http://127.0.0.1:5000

### 3. Default Login Credentials

- **Admin**: username: `admin`, password: `admin123`
- **Cashier**: username: `cashier`, password: `cashier123`

## 📁 Project Structure

```
pos-system/
├── app.py                 # Main Flask application
├── .env                   # Environment variables
├── README.md             # This file
├── templates/            # Jinja2 templates
│   ├── base.html
│   ├── login.html
│   ├── dashboard.html
│   ├── sales.html
│   ├── inventory.html
│   ├── reports.html
│   └── users.html
├── static/               # Static files
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── script.js
├── instance/             # Database files
│   └── pos.db
└── pos_env/              # Virtual environment
```

## 🔐 User Roles & Permissions

### Admin User
- Full access to all features
- Can manage users (add/edit/delete)
- Can access all sections: Dashboard, Sales, Inventory, Reports, Users

### Cashier User
- Limited access for daily operations
- Can access: Dashboard, Sales, Inventory, Reports
- Cannot access User Management

## 📊 Database Models

### User
- id, username, password_hash, role, created_at

### Item
- id, name, buying_price, selling_price, quantity, barcode, sold_quantity, created_at

### Sale
- id, user_id, total_amount, discount_percent, discount_amount, final_amount, profit, created_at

### SaleItem
- id, sale_id, item_id, quantity, unit_price, total_price

## 🔧 API Endpoints

- `GET /` - Dashboard (login required)
- `GET/POST /login` - User login
- `GET /logout` - User logout
- `GET /dashboard` - Dashboard with metrics
- `GET /sales` - Sales interface
- `GET /inventory` - Inventory management
- `GET /reports` - Sales reports
- `GET /users` - User management (admin only)

### API Routes
- `POST /api/add_item` - Add new inventory item
- `POST /api/add_user` - Add new user (admin only)
- `POST /api/complete_sale` - Process sale transaction
- `GET /api/items` - Get all inventory items
- `GET /api/sales` - Get sales data

## 🎯 Key Features

### Sales Processing
- Camera barcode scanning support
- Manual barcode entry
- Real-time cart management
- Discount application
- Automatic inventory updates
- Receipt generation

### Inventory Management
- Add/edit inventory items
- Automatic barcode generation
- Stock level tracking
- Search functionality
- Investment value calculation

### Dashboard Analytics
- Daily/Weekly/Monthly sales metrics
- Profit tracking
- Top-selling items
- Low stock alerts
- Transaction counts

### Security Features
- Password hashing with bcrypt
- Session-based authentication
- CSRF protection on forms
- Role-based access control

## 🔒 Security Considerations

- Change the `SECRET_KEY` in `.env` for production
- Use HTTPS in production
- Implement password complexity requirements
- Regular database backups
- Monitor user access logs

## 🚀 Production Deployment

For production deployment, consider:

1. **WSGI Server**: Use Gunicorn or uWSGI instead of Flask's development server
2. **Database**: Migrate to PostgreSQL for better performance
3. **Environment**: Set `FLASK_ENV=production`
4. **Security**: Implement HTTPS, change secret keys
5. **Monitoring**: Add logging and error tracking

## 📝 Development

### Adding New Features
1. Create new routes in `app.py`
2. Add corresponding templates in `templates/`
3. Update navigation in `base.html`
4. Add CSS styles in `static/css/style.css`

### Database Migrations
The application uses SQLAlchemy with automatic table creation. For schema changes:
1. Update the model classes in `app.py`
2. The tables will be created automatically on next run

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 📞 Support

For issues and questions, please create an issue in the repository or contact the development team.

---

**Happy Selling! 🛒💰**
