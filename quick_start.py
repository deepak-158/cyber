#!/usr/bin/env python3
"""
Quick Start Script for Cyber Threat Detection System
This script helps you get the system running quickly with all services
"""

import subprocess
import sys
import os
import time
import json
import argparse
from pathlib import Path
import threading

def run_command(command, description, capture_output=False, shell=False):
    """Run a command and return success status"""
    print(f"🔧 {description}...")
    
    try:
        if capture_output:
            result = subprocess.run(command, capture_output=True, text=True, shell=shell, check=True)
            return True, result.stdout.strip()
        else:
            subprocess.run(command, shell=shell, check=True)
            return True, None
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {description}")
        if capture_output and e.stderr:
            print(f"Error: {e.stderr}")
        return False, None

def check_docker():
    """Check if Docker is available and running"""
    success, _ = run_command(["docker", "--version"], "Checking Docker installation", capture_output=True)
    if not success:
        print("❌ Docker is not installed or not available in PATH")
        print("📥 Please install Docker Desktop from: https://www.docker.com/products/docker-desktop")
        return False
    
    success, _ = run_command(["docker", "info"], "Checking Docker daemon", capture_output=True)
    if not success:
        print("❌ Docker daemon is not running")
        print("🔄 Please start Docker Desktop")
        return False
    
    print("✅ Docker is ready")
    return True

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} is not supported")
        print("📥 Please install Python 3.8 or higher")
        return False
    
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
    return True

def setup_environment():
    """Setup environment file"""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if not env_file.exists():
        if env_example.exists():
            print("📝 Creating .env file from .env.example...")
            with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                dst.write(src.read())
            print("✅ .env file created")
            print("⚠️  Please edit .env file with your API credentials")
        else:
            print("❌ .env.example file not found")
            return False
    else:
        print("✅ .env file already exists")
    
    return True

def install_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    success, _ = run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                           "Installing requirements", capture_output=True)
    if success:
        print("✅ Dependencies installed successfully")
        return True
    else:
        print("❌ Failed to install dependencies")
        return False

def start_docker_services():
    """Start Docker services"""
    print("🐳 Starting Docker services...")
    success, _ = run_command(["docker-compose", "up", "-d"], "Starting Docker containers")
    if success:
        print("✅ Docker services started")
        return True
    else:
        print("❌ Failed to start Docker services")
        return False

def wait_for_services():
    """Wait for services to be ready"""
    print("⏳ Waiting for services to initialize...")
    time.sleep(10)  # Give services time to start
    
    # Check PostgreSQL
    check_postgres = [
        "docker", "exec", "cyber-postgres", "pg_isready", 
        "-U", "cyber_user", "-d", "cyber_threat_db"
    ]
    success, _ = run_command(check_postgres, "Checking PostgreSQL", capture_output=True)
    if success:
        print("✅ PostgreSQL is ready")
    else:
        print("⚠️  PostgreSQL may still be starting...")
    
    # Check Neo4j (simplified check)
    print("✅ Neo4j should be ready at http://localhost:7474")
    print("✅ Redis should be ready at localhost:6379")

def run_database_setup():
    """Initialize database schemas"""
    print("🗄️  Setting up database schemas...")
    
    # Run PostgreSQL initialization
    init_sql_path = "./backend/app/database/init_db.sql"
    if os.path.exists(init_sql_path):
        docker_cp_cmd = ["docker", "cp", init_sql_path, "cyber-postgres:/tmp/init_db.sql"]
        run_command(docker_cp_cmd, "Copying SQL file to container")
        
        exec_sql_cmd = [
            "docker", "exec", "cyber-postgres", "psql", 
            "-U", "cyber_user", "-d", "cyber_threat_db", "-f", "/tmp/init_db.sql"
        ]
        success, _ = run_command(exec_sql_cmd, "Executing database initialization")
        if success:
            print("✅ Database schemas created")
        else:
            print("⚠️  Database setup may have issues")
    else:
        print("⚠️  Database initialization file not found")

def start_backend_api():
    """Start the FastAPI backend"""
    print("🚀 Starting FastAPI backend...")
    
    def run_backend():
        os.chdir("backend")
        subprocess.run([
            sys.executable, "-m", "uvicorn", "app.main:app", 
            "--host", "0.0.0.0", "--port", "8000", "--reload"
        ])
    
    backend_thread = threading.Thread(target=run_backend, daemon=True)
    backend_thread.start()
    time.sleep(3)  # Give backend time to start
    print("✅ Backend API started at http://localhost:8000")
    return backend_thread

def start_dashboard():
    """Start the Streamlit dashboard"""
    print("📊 Starting Streamlit dashboard...")
    
    def run_dashboard():
        os.chdir("frontend")
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "dashboard.py", 
            "--server.port", "8501", "--server.address", "0.0.0.0"
        ])
    
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()
    time.sleep(3)  # Give dashboard time to start
    print("✅ Dashboard started at http://localhost:8501")
    return dashboard_thread

def show_system_status():
    """Show system status and URLs"""
    print("\n" + "="*60)
    print("🎉 CYBER THREAT DETECTION SYSTEM - READY!")
    print("="*60)
    print("📊 Streamlit Dashboard: http://localhost:8501")
    print("🔗 FastAPI Backend: http://localhost:8000")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🗄️  PostgreSQL: localhost:5432")
    print("🕸️  Neo4j Browser: http://localhost:7474")
    print("🔴 Redis: localhost:6379")
    print("="*60)
    print("⚠️  IMPORTANT:")
    print("   1. Edit .env file with your API credentials")
    print("   2. The system uses sample data if no API credentials provided")
    print("   3. Neo4j login: neo4j / cyber_graph_password_2024")
    print("   4. Press Ctrl+C to stop all services")
    print("="*60)

def cleanup_on_exit():
    """Cleanup Docker services on exit"""
    print("\n🛑 Shutting down services...")
    run_command(["docker-compose", "down"], "Stopping Docker services")
    print("✅ Services stopped")

def main():
    """Main quick start function"""
    parser = argparse.ArgumentParser(description="Quick start the Cyber Threat Detection System")
    parser.add_argument("--skip-deps", action="store_true", help="Skip dependency installation")
    parser.add_argument("--skip-docker", action="store_true", help="Skip Docker services")
    parser.add_argument("--backend-only", action="store_true", help="Start backend API only")
    parser.add_argument("--dashboard-only", action="store_true", help="Start dashboard only")
    
    args = parser.parse_args()
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🚀 Cyber Threat Detection System - Quick Start")
    print(f"📁 Working directory: {os.getcwd()}")
    
    try:
        # Pre-flight checks
        if not check_python_version():
            return 1
        
        if not args.skip_docker and not check_docker():
            return 1
        
        # Setup
        if not setup_environment():
            return 1
        
        if not args.skip_deps and not install_dependencies():
            return 1
        
        # Start services
        if not args.skip_docker:
            if not start_docker_services():
                return 1
            wait_for_services()
            run_database_setup()
        
        # Start application components
        threads = []
        
        if not args.dashboard_only:
            backend_thread = start_backend_api()
            threads.append(backend_thread)
        
        if not args.backend_only:
            dashboard_thread = start_dashboard()
            threads.append(dashboard_thread)
        
        # Show status
        show_system_status()
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        
    except KeyboardInterrupt:
        pass
    finally:
        if not args.skip_docker:
            cleanup_on_exit()
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)