@echo off
chcp 65001 >nul

echo 🚀 Installing Medical Vector Database Frontend...

REM Check if Node.js is installed
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed. Please install Node.js 16+ first.
    echo Visit: https://nodejs.org/
    pause
    exit /b 1
)

echo ✅ Node.js version: 
node --version

REM Install dependencies
echo 📦 Installing dependencies...
call npm install

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully!

REM Create .env file if it doesn't exist
if not exist .env (
    echo 🔧 Creating .env file...
    (
        echo VITE_API_BASE_URL=http://localhost:8000
        echo VITE_APP_TITLE=Medical Vector Database
    ) > .env
    echo ✅ Created .env file
)

echo.
echo 🎉 Installation completed successfully!
echo.
echo To start the development server:
echo   npm run dev
echo.
echo Make sure your backend API is running on http://localhost:8000
echo.
echo The dashboard will be available at: http://localhost:3000
echo.
pause 