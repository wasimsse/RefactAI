#!/bin/bash

# RefactAI Build Script
# This script helps build and run the RefactAI project

set -e

echo "🔧 RefactAI Build Script"
echo "========================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Java 21 is available
check_java() {
    print_status "Checking Java version..."
    if command -v java &> /dev/null; then
        # Set JAVA_HOME to use Java 23 if available
        if [ -d "/Library/Java/JavaVirtualMachines/jdk-23.jdk/Contents/Home" ]; then
            export JAVA_HOME="/Library/Java/JavaVirtualMachines/jdk-23.jdk/Contents/Home"
            export PATH="$JAVA_HOME/bin:$PATH"
        fi
        
        JAVA_VERSION=$(java -version 2>&1 | head -n 1 | cut -d'"' -f2 | cut -d'.' -f1)
        if [ "$JAVA_VERSION" -ge 21 ]; then
            print_success "Java $JAVA_VERSION found"
        else
            print_error "Java 21 or higher is required. Found Java $JAVA_VERSION"
            exit 1
        fi
    else
        print_error "Java is not installed"
        exit 1
    fi
}

# Check if Node.js is available
check_node() {
    print_status "Checking Node.js version..."
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        if [ "$NODE_VERSION" -ge 18 ]; then
            print_success "Node.js $NODE_VERSION found"
        else
            print_error "Node.js 18 or higher is required. Found Node.js $NODE_VERSION"
            exit 1
        fi
    else
        print_error "Node.js is not installed"
        exit 1
    fi
}

# Build backend
build_backend() {
    print_status "Building backend..."
    if [ -f "backend/pom.xml" ]; then
        cd backend
        mvn clean package -DskipTests
        cd ..
        print_success "Backend built successfully"
    else
        print_error "backend/pom.xml not found. Are you in the correct directory?"
        exit 1
    fi
}

# Build web app
build_web() {
    print_status "Building web app..."
    if [ -d "web/app" ]; then
        cd web/app
        npm install
        npm run build
        cd ../..
        print_success "Web app built successfully"
    else
        print_warning "Web app directory not found, skipping..."
    fi
}

# Build VS Code extension
build_vscode() {
    print_status "Building VS Code extension..."
    if [ -d "vscode/client" ]; then
        cd vscode/client
        npm install
        npm run compile
        cd ../..
        print_success "VS Code extension built successfully"
    else
        print_warning "VS Code extension directory not found, skipping..."
    fi
}

# Run backend server
run_backend() {
    print_status "Starting backend server..."
    if [ -f "backend/server/pom.xml" ]; then
        cd backend/server
        java -jar target/refactai-server-0.1.0-SNAPSHOT.jar &
        BACKEND_PID=$!
        cd ../..
        print_success "Backend server started (PID: $BACKEND_PID)"
        echo $BACKEND_PID > .backend.pid
    else
        print_error "Cannot start backend server"
        exit 1
    fi
}

# Run web app
run_web() {
    print_status "Starting web app..."
    if [ -d "web/app" ]; then
        cd web/app
        npm run dev &
        WEB_PID=$!
        cd ../..
        print_success "Web app started (PID: $WEB_PID)"
        echo $WEB_PID > .web.pid
    else
        print_warning "Web app directory not found, skipping..."
    fi
}

# Stop all services
stop_services() {
    print_status "Stopping services..."
    
    if [ -f ".backend.pid" ]; then
        BACKEND_PID=$(cat .backend.pid)
        if kill -0 $BACKEND_PID 2>/dev/null; then
            kill $BACKEND_PID
            print_success "Backend server stopped"
        fi
        rm .backend.pid
    fi
    
    if [ -f ".web.pid" ]; then
        WEB_PID=$(cat .web.pid)
        if kill -0 $WEB_PID 2>/dev/null; then
            kill $WEB_PID
            print_success "Web app stopped"
        fi
        rm .web.pid
    fi
}

# Clean build artifacts
clean() {
    print_status "Cleaning build artifacts..."
    if [ -f "backend/pom.xml" ]; then
        cd backend
        mvn clean
        cd ..
    fi
    if [ -d "web/app" ]; then
        cd web/app
        rm -rf .next node_modules
        cd ../..
    fi
    if [ -d "vscode/client" ]; then
        cd vscode/client
        rm -rf out node_modules
        cd ../..
    fi
    print_success "Clean completed"
}

# Show help
show_help() {
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build       Build all components (backend, web, vscode)"
    echo "  backend     Build and run backend server"
    echo "  web         Build and run web app"
    echo "  vscode      Build VS Code extension"
    echo "  run         Run all services (backend + web)"
    echo "  stop        Stop all running services"
    echo "  clean       Clean all build artifacts"
    echo "  check       Check system requirements"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build    # Build all components"
    echo "  $0 run      # Start backend and web services"
    echo "  $0 stop     # Stop all services"
}

# Main script logic
case "${1:-help}" in
    "build")
        check_java
        check_node
        build_backend
        build_web
        build_vscode
        print_success "All components built successfully!"
        ;;
    "backend")
        check_java
        build_backend
        run_backend
        print_success "Backend is running at http://localhost:8080"
        ;;
    "web")
        check_node
        build_web
        run_web
        print_success "Web app is running at http://localhost:3000"
        ;;
    "vscode")
        check_node
        build_vscode
        print_success "VS Code extension built successfully!"
        ;;
    "run")
        check_java
        check_node
        build_backend
        build_web
        run_backend
        sleep 5  # Wait for backend to start
        run_web
        print_success "All services are running!"
        print_success "Backend: http://localhost:8080"
        print_success "Web App: http://localhost:3000"
        ;;
    "stop")
        stop_services
        ;;
    "clean")
        clean
        ;;
    "check")
        check_java
        check_node
        print_success "All system requirements met!"
        ;;
    "help"|*)
        show_help
        ;;
esac
