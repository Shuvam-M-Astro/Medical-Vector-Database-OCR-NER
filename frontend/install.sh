#!/bin/bash

# Medical Vector Database Frontend Installation Script

echo "🚀 Installing Medical Vector Database Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ first."
    echo "Visit: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 16 ]; then
    echo "❌ Node.js version 16+ is required. Current version: $(node -v)"
    exit 1
fi

echo "✅ Node.js version: $(node -v)"

# Install dependencies
echo "📦 Installing dependencies..."
npm install

if [ $? -eq 0 ]; then
    echo "✅ Dependencies installed successfully!"
else
    echo "❌ Failed to install dependencies"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "🔧 Creating .env file..."
    cat > .env << EOF
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_TITLE=Medical Vector Database
EOF
    echo "✅ Created .env file"
fi

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "To start the development server:"
echo "  npm run dev"
echo ""
echo "Make sure your backend API is running on http://localhost:8000"
echo ""
echo "The dashboard will be available at: http://localhost:3000" 