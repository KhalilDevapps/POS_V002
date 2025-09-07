# Admin Password Reset Tool

This tool allows you to reset the admin user password for the POS System from the command line, without needing to access the web interface.

## 🚀 Quick Start

### Method 1: Interactive Mode (Recommended)
```bash
python reset_admin_password.py
```
This will prompt you to enter the new password interactively.

### Method 2: Direct Password
```bash
python reset_admin_password.py mynewpassword
```
Replace `mynewpassword` with your desired password.

### Method 3: Specify Username
```bash
python reset_admin_password.py securepass123 --username admin
```
This resets the password for a specific user (default is 'admin').

## 📋 Usage Examples

```bash
# Interactive mode - will prompt for password
python reset_admin_password.py

# Set password directly
python reset_admin_password.py MySecurePass123

# Reset password for specific user
python reset_admin_password.py NewPass456 --username cashier

# Skip confirmation prompt (use with caution)
python reset_admin_password.py NewPass456 --confirm

# Show help
python reset_admin_password.py --help
```

## 🔧 Requirements

- Python 3.8 or higher
- Flask and SQLAlchemy installed
- Access to the POS system database file (`instance/pos.db`)

## ⚠️ Important Notes

### Security Considerations
- **Change the password after first login** - This is a temporary reset
- **Use strong passwords** - Minimum 6 characters required
- **Store passwords securely** - Don't share or write down passwords
- **Regular password changes** - Change passwords periodically

### Database Requirements
- The script looks for the database at `instance/pos.db`
- Make sure the POS system has been initialized at least once
- The database file must be accessible and writable

### User Requirements
- The user must already exist in the database
- Default admin user is created automatically when the system starts
- You can reset passwords for any user account

## 🔍 Troubleshooting

### "Database file not found"
- Make sure you're running the script from the POS system root directory
- Ensure the POS system has been started at least once to create the database
- Check that `instance/pos.db` exists

### "User not found"
- Verify the username is correct
- The script will show all available users if the specified user doesn't exist
- Default users: `admin` (role: admin) and `cashier` (role: cashier)

### "Missing required packages"
- Install dependencies: `pip install flask flask-sqlalchemy werkzeug`
- Make sure you're using the correct Python environment

### Permission Errors
- Ensure you have write permissions to the database file
- On Windows, make sure no other process is using the database
- On Linux/Mac, check file permissions: `chmod 664 instance/pos.db`

## 📊 What the Script Does

1. **Validates Requirements**: Checks for database file and required packages
2. **Password Validation**: Ensures password meets minimum requirements
3. **User Verification**: Confirms the user exists in the database
4. **Security Confirmation**: Asks for confirmation before making changes
5. **Password Reset**: Updates the password hash in the database
6. **Success Feedback**: Shows confirmation with security recommendations

## 🔐 Security Features

- **Password Hashing**: Uses Werkzeug's secure password hashing
- **Input Validation**: Validates password strength and user existence
- **Confirmation Prompts**: Requires explicit confirmation before changes
- **Error Handling**: Comprehensive error messages and graceful failure
- **Audit Trail**: Updates user timestamp for tracking

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Verify all requirements are met
3. Ensure you're running from the correct directory
4. Contact your system administrator

## 🚨 Emergency Use Only

This script should only be used when:
- You cannot access the web interface
- The admin account is locked out
- Password recovery through normal channels fails
- System maintenance requires password reset

**Remember**: Always change the temporary password after successful login!
