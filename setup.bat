@echo off
REM Gurumisha Django E-Commerce Platform Setup Script for Windows
REM This script automates the initial setup process

echo 🚀 Setting up Gurumisha Django E-Commerce Platform...
echo ==================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.10+ and try again.
    pause
    exit /b 1
)

echo ✅ Python detected

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 16+ and try again.
    pause
    exit /b 1
)

echo ✅ Node.js detected

REM Create virtual environment
echo 📦 Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install Python dependencies
echo 📚 Installing Python dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo ✅ Python dependencies installed
) else (
    echo ❌ requirements.txt not found
    pause
    exit /b 1
)

REM Install Node.js dependencies
echo 📦 Installing Node.js dependencies...
if exist "package.json" (
    npm install
    echo ✅ Node.js dependencies installed
) else (
    echo ❌ package.json not found
    pause
    exit /b 1
)

REM Navigate to Django project directory
cd gurumisha

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo 📝 Creating .env file...
    (
        echo DEBUG=True
        echo SECRET_KEY=your-secret-key-here-please-change-this
        echo DATABASE_URL=sqlite:///db.sqlite3
        echo EMAIL_HOST=smtp.gmail.com
        echo EMAIL_PORT=587
        echo EMAIL_HOST_USER=kamandembugua18@gmail.com
        echo EMAIL_HOST_PASSWORD=your-email-password-here
        echo EMAIL_USE_TLS=True
        echo ALLOWED_HOSTS=localhost,127.0.0.1
    ) > .env
    echo ✅ .env file created
    echo ⚠️  Please update SECRET_KEY and EMAIL_HOST_PASSWORD in .env file
) else (
    echo ✅ .env file already exists
)

REM Run database migrations
echo 🗄️  Setting up database...
python manage.py makemigrations
python manage.py migrate
echo ✅ Database migrations completed

REM Create superuser (optional)
echo 👤 Creating superuser account...
echo You can skip this step and create it later with: python manage.py createsuperuser
set /p create_superuser="Do you want to create a superuser now? (y/N): "

if /i "%create_superuser%"=="y" (
    python manage.py createsuperuser
    echo ✅ Superuser created
) else (
    echo ⏭️  Skipping superuser creation
)

REM Build Tailwind CSS
echo 🎨 Building Tailwind CSS...
cd ..
npm run build
echo ✅ Tailwind CSS built

REM Collect static files
echo 📁 Collecting static files...
cd gurumisha
python manage.py collectstatic --noinput
echo ✅ Static files collected

REM Final setup complete
echo.
echo 🎉 Setup completed successfully!
echo ==================================================
echo.
echo 📋 Next steps:
echo 1. Update SECRET_KEY and EMAIL_HOST_PASSWORD in gurumisha\.env file
echo 2. Start the development server:
echo    cd gurumisha
echo    venv\Scripts\activate.bat
echo    python manage.py runserver
echo.
echo 3. In another terminal, start Tailwind CSS watcher:
echo    npm run dev
echo.
echo 4. Visit http://127.0.0.1:8000 to see your application
echo 5. Admin panel: http://127.0.0.1:8000/admin/
echo.
echo 📚 For more information, see README.md
echo.
echo 🚀 Happy coding!
pause
