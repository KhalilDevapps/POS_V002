#!/usr/bin/env python3
"""
POS System Setup Script
========================

This script automates the complete setup process for the POS system including:
- Virtual environment creation
- Dependency installation
- Environment configuration
- Database initialization
- Default user creation
- Application startup

Usage:
    python setup.py

Or make it executable and run:
    chmod +x setup.py
    ./setup.py

Author: POS System Development Team
Version: 1.0.0
"""

import os
import sys
import subprocess
import platform
import shutil
import json
from pathlib import Path
import time

class POSSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.requirements_file = self.project_root / "requirements.txt"
        self.env_file = self.project_root / ".env"
        self.instance_dir = self.project_root / "instance"
        self.db_path = self.instance_dir / "pos.db"

        # Colors for terminal output
        self.colors = {
            'GREEN': '\033[92m',
            'RED': '\033[91m',
            'YELLOW': '\033[93m',
            'BLUE': '\033[94m',
            'BOLD': '\033[1m',
            'ENDC': '\033[0m'
        }

        # Default configuration
        self.default_config = {
            'SECRET_KEY': 'dev-secret-key-change-in-production',
            'DATABASE_URL': 'sqlite:///pos.db',
            'DEBUG': 'True',
            'HOST': '0.0.0.0',
            'PORT': '5000',
            'SESSION_TIMEOUT': '3600'
        }

    def print_header(self):
        """Print setup header"""
        print(f"{self.colors['BOLD']}{self.colors['BLUE']}")
        print("=" * 60)
        print("         POS SYSTEM SETUP SCRIPT")
        print("=" * 60)
        print(f"{self.colors['ENDC']}")
        print("This script will set up your POS system automatically.")
        print("Make sure you have Python 3.8+ installed.\n")

    def print_step(self, step_num, description):
        """Print current step"""
        print(f"{self.colors['YELLOW']}[Step {step_num}]{self.colors['ENDC']} {description}")

    def print_success(self, message):
        """Print success message"""
        print(f"{self.colors['GREEN']}✓ {message}{self.colors['ENDC']}")

    def print_error(self, message):
        """Print error message"""
        print(f"{self.colors['RED']}✗ {message}{self.colors['ENDC']}")

    def print_info(self, message):
        """Print info message"""
        print(f"{self.colors['BLUE']}ℹ {message}{self.colors['ENDC']}")

    def run_command(self, command, cwd=None, shell=False):
        """Run a command and return success status"""
        try:
            if shell:
                result = subprocess.run(command, shell=True, cwd=cwd,
                                      capture_output=True, text=True, check=True)
            else:
                result = subprocess.run(command.split(), cwd=cwd,
                                      capture_output=True, text=True, check=True)
            return True, result.stdout, result.stderr
        except subprocess.CalledProcessError as e:
            return False, e.stdout, e.stderr
        except FileNotFoundError:
            return False, "", "Command not found"

    def check_python_version(self):
        """Check if Python version is compatible"""
        self.print_step(1, "Checking Python version...")

        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            self.print_error(f"Python {version.major}.{version.minor} detected. Python 3.8+ required.")
            return False

        self.print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")
        return True

    def check_existing_venv(self):
        """Check if virtual environment already exists"""
        if self.venv_path.exists():
            response = input(f"{self.colors['YELLOW']}Virtual environment already exists. Remove and recreate? (y/N): {self.colors['ENDC']}")
            if response.lower() in ['y', 'yes']:
                self.print_info("Removing existing virtual environment...")
                shutil.rmtree(self.venv_path)
                return True
            else:
                self.print_info("Using existing virtual environment")
                return True
        return True

    def create_virtual_environment(self):
        """Create Python virtual environment"""
        self.print_step(2, "Creating virtual environment...")

        if not self.check_existing_venv():
            return False

        success, stdout, stderr = self.run_command(f"python -m venv venv")
        if not success:
            self.print_error(f"Failed to create virtual environment: {stderr}")
            return False

        self.print_success("Virtual environment created successfully")
        return True

    def activate_venv(self):
        """Get the path to Python executable in virtual environment"""
        if platform.system() == "Windows":
            python_exe = self.venv_path / "Scripts" / "python.exe"
        else:
            python_exe = self.venv_path / "bin" / "python"

        return str(python_exe)

    def install_dependencies(self):
        """Install Python dependencies"""
        self.print_step(3, "Installing dependencies...")

        python_exe = self.activate_venv()

        # Check if requirements.txt exists
        if not self.requirements_file.exists():
            self.print_error("requirements.txt not found")
            return False

        # Upgrade pip first
        self.print_info("Upgrading pip...")
        success, stdout, stderr = self.run_command(f"{python_exe} -m pip install --upgrade pip")
        if not success:
            self.print_error(f"Failed to upgrade pip: {stderr}")
            return False

        # Install requirements
        self.print_info("Installing requirements...")
        success, stdout, stderr = self.run_command(f"{python_exe} -m pip install -r requirements.txt")
        if not success:
            self.print_error(f"Failed to install dependencies: {stderr}")
            return False

        self.print_success("Dependencies installed successfully")
        return True

    def create_env_file(self):
        """Create .env file with default configuration"""
        self.print_step(4, "Creating environment configuration...")

        if self.env_file.exists():
            response = input(f"{self.colors['YELLOW']}.env file already exists. Overwrite? (y/N): {self.colors['ENDC']}")
            if response.lower() not in ['y', 'yes']:
                self.print_info("Using existing .env file")
                return True

        try:
            with open(self.env_file, 'w') as f:
                f.write("# POS System Environment Configuration\n")
                f.write("# Generated automatically by setup script\n\n")
                for key, value in self.default_config.items():
                    f.write(f"{key}={value}\n")

            self.print_success(".env file created successfully")
            return True
        except Exception as e:
            self.print_error(f"Failed to create .env file: {e}")
            return False

    def create_instance_directory(self):
        """Create instance directory for database"""
        self.print_step(5, "Setting up database directory...")

        try:
            self.instance_dir.mkdir(exist_ok=True)
            self.print_success("Database directory created successfully")
            return True
        except Exception as e:
            self.print_error(f"Failed to create instance directory: {e}")
            return False

    def initialize_database(self):
        """Initialize the database and create default users"""
        self.print_step(6, "Initializing database...")

        python_exe = self.activate_venv()

        try:
            # Run the app to create tables and default users
            success, stdout, stderr = self.run_command(f"{python_exe} app.py", shell=True)
            if not success:
                self.print_error(f"Failed to initialize database: {stderr}")
                return False

            # Wait a moment for database initialization
            time.sleep(2)

            # Check if database was created
            if self.db_path.exists():
                db_size = self.db_path.stat().st_size
                self.print_success(f"Database initialized successfully ({db_size} bytes)")
                return True
            else:
                self.print_error("Database file was not created")
                return False

        except Exception as e:
            self.print_error(f"Database initialization failed: {e}")
            return False

    def create_startup_script(self):
        """Create a startup script for easy application launching"""
        self.print_step(7, "Creating startup script...")

        if platform.system() == "Windows":
            script_content = f'''@echo off
echo Starting POS System...
cd /d "{self.project_root}"
call venv\\Scripts\\activate.bat
python app.py
pause
'''
            script_name = "start_pos.bat"
        else:
            script_content = f'''#!/bin/bash
echo "Starting POS System..."
cd "{self.project_root}"
source venv/bin/activate
python app.py
'''
            script_name = "start_pos.sh"

        try:
            script_path = self.project_root / script_name
            with open(script_path, 'w') as f:
                f.write(script_content)

            if platform.system() != "Windows":
                script_path.chmod(0o755)

            self.print_success(f"Startup script created: {script_name}")
            return True
        except Exception as e:
            self.print_error(f"Failed to create startup script: {e}")
            return False

    def show_setup_summary(self):
        """Show setup completion summary"""
        print(f"\n{self.colors['BOLD']}{self.colors['GREEN']}")
        print("=" * 60)
        print("         SETUP COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"{self.colors['ENDC']}")

        print(f"{self.colors['BOLD']}Project Location:{self.colors['ENDC']} {self.project_root}")
        print(f"{self.colors['BOLD']}Virtual Environment:{self.colors['ENDC']} {self.venv_path}")
        print(f"{self.colors['BOLD']}Database:{self.colors['ENDC']} {self.db_path}")
        print(f"{self.colors['BOLD']}Configuration:{self.colors['ENDC']} {self.env_file}")

        print(f"\n{self.colors['BOLD']}To start the application:{self.colors['ENDC']}")

        if platform.system() == "Windows":
            print("  Double-click: start_pos.bat")
            print("  Or manually:")
            print(f"    cd {self.project_root}")
            print("    venv\\Scripts\\activate.bat")
            print("    python app.py")
        else:
            print("  Run: ./start_pos.sh")
            print("  Or manually:")
            print(f"    cd {self.project_root}")
            print("    source venv/bin/activate")
            print("    python app.py")

        print(f"\n{self.colors['BOLD']}Default Login Credentials:{self.colors['ENDC']}")
        print("  Admin: username='admin', password='admin123'")
        print("  Cashier: username='cashier', password='cashier123'")

        print(f"\n{self.colors['BOLD']}Access the application at:{self.colors['ENDC']} http://localhost:5000")

        print(f"\n{self.colors['YELLOW']}Note: Remember to change default passwords in production!{self.colors['ENDC']}")

    def run_setup(self):
        """Run the complete setup process"""
        self.print_header()

        steps = [
            self.check_python_version,
            self.create_virtual_environment,
            self.install_dependencies,
            self.create_env_file,
            self.create_instance_directory,
            self.initialize_database,
            self.create_startup_script
        ]

        for step in steps:
            if not step():
                self.print_error("Setup failed. Please check the errors above.")
                return False

        self.show_setup_summary()
        return True

def main():
    """Main entry point"""
    try:
        setup = POSSetup()
        success = setup.run_setup()

        if success:
            print(f"\n{setup.colors['GREEN']}🎉 POS System setup completed successfully!{setup.colors['ENDC']}")
            return 0
        else:
            print(f"\n{setup.colors['RED']}❌ POS System setup failed.{setup.colors['ENDC']}")
            return 1

    except KeyboardInterrupt:
        print(f"\n{setup.colors['YELLOW']}Setup interrupted by user.{setup.colors['ENDC']}")
        return 1
    except Exception as e:
        print(f"\n{setup.colors['RED']}Unexpected error: {e}{setup.colors['ENDC']}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
