# POS System Setup Guide

## 🚀 Quick Setup with Automated Script

The POS system now includes a fully automated setup script that handles everything for you!

### Prerequisites
- Python 3.8 or higher installed
- Internet connection for downloading dependencies
- Basic command line knowledge

### One-Command Setup

#### Windows
```bash
python setup.py
```

#### Linux/Mac
```bash
chmod +x setup.py
python setup.py
# OR
./setup.py
```

### What the Setup Script Does

The automated setup script performs these steps:

1. ✅ **Python Version Check** - Ensures Python 3.8+ is installed
2. ✅ **Virtual Environment** - Creates isolated Python environment
3. ✅ **Dependencies Installation** - Installs all required packages
4. ✅ **Environment Configuration** - Creates .env file with defaults
5. ✅ **Database Setup** - Creates instance directory and initializes database
6. ✅ **Default Users** - Creates admin and cashier accounts
7. ✅ **Startup Scripts** - Creates easy-launch scripts

### Default Login Credentials

After setup completion, you can login with:

- **Admin Account**: `admin` / `admin123`
- **Cashier Account**: `cashier` / `cashier123`

⚠️ **Important**: Change these default passwords in production!

### Starting the Application

#### Option 1: Use the generated startup script
- **Windows**: Double-click `start_pos.bat`
- **Linux/Mac**: Run `./start_pos.sh`

#### Option 2: Manual startup
```bash
# Windows
cd your-project-directory
venv\Scripts\activate.bat
python app.py

# Linux/Mac
cd your-project-directory
source venv/bin/activate
python app.py
```

### Accessing the Application

Once started, open your browser and go to:
```
http://localhost:5000
```

### Setup Script Features

- **Cross-platform**: Works on Windows, Linux, and macOS
- **Error handling**: Clear error messages and recovery suggestions
- **Interactive prompts**: Asks before overwriting existing files
- **Progress tracking**: Shows current step and completion status
- **Color-coded output**: Easy to read success/error messages
- **Automatic cleanup**: Handles temporary files and failed installations

### Troubleshooting

#### Common Issues

**"Python version too old"**
- Upgrade to Python 3.8 or higher
- Download from: https://python.org

**"Permission denied"**
- On Linux/Mac: `chmod +x setup.py`
- On Windows: Run as Administrator if needed

**"Virtual environment already exists"**
- Script will ask if you want to recreate it
- Choose 'y' to recreate, 'n' to use existing

**"Requirements installation failed"**
- Check internet connection
- Try running: `pip install -r requirements.txt` manually

### Manual Setup (Alternative)

If you prefer manual setup or the automated script fails:

```bash
# 1. Create virtual environment
python -m venv venv

# 2. Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables (optional)
# Copy .env.example to .env and edit as needed

# 5. Run the application
python app.py
```

### Project Structure After Setup

```
pos-system/
├── venv/                    # Virtual environment
├── instance/
│   └── pos.db              # SQLite database
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
├── backups/                # Database backups
├── temp_uploads/           # Temporary file uploads
├── .env                    # Environment configuration
├── setup.py               # Setup script
├── start_pos.bat/.sh      # Startup scripts
├── requirements.txt       # Python dependencies
├── app.py                 # Main application
└── README_SETUP.md        # This file
```

### Next Steps

1. **Login** with default credentials
2. **Change passwords** for security
3. **Add inventory items** to start selling
4. **Configure users** and permissions
5. **Set up backup schedule** for data safety

### Getting Help

- 📖 **User Guide**: Available in-app at `/user_guide`
- ⚙️ **Admin Guide**: Available in-app at `/admin_guide` (admin only)
- 👨‍💻 **Developer Guide**: Available in-app at `/developer_guide` (admin only)

### Support

For issues with the setup script:
1. Check the error messages carefully
2. Ensure all prerequisites are met
3. Try running individual commands manually
4. Check the developer guide for troubleshooting tips

---

🎉 **Happy selling with your new POS system!**
