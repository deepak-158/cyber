#!/usr/bin/env python3
"""
Quick Start Script for Cyber Threat Detection System
This script helps users get started with the system quickly
"""

import os
import sys
import subprocess
import time
import requests
import json
from pathlib import Path

def print_banner():
    """Print welcome banner"""
    banner = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║              Cyber Threat Detection System                    ║
    ║              Quick Start Setup Script                         ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    prerequisites = [
        ('docker', 'Docker'),
        ('docker-compose', 'Docker Compose')
    ]
    
    missing = []
    for cmd, name in prerequisites:
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True)
            print(f"  ✅ {name} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"  ❌ {name} is not installed")
            missing.append(name)
    
    if missing:
        print(f"\n❌ Missing prerequisites: {', '.join(missing)}")
        print("Please install the missing tools and run this script again.")
        return False
    
    print("✅ All prerequisites are satisfied!")
    return True

def setup_environment():
    """Setup environment file"""
    print("\n🔧 Setting up environment...")
    
    env_file = Path('.env')
    env_template = Path('.env.template')
    
    if env_file.exists():
        print("  ✅ .env file already exists")
        return True
    
    if env_template.exists():
        # Copy template to .env
        import shutil
        shutil.copy(env_template, env_file)
        print("  ✅ Created .env file from template")
        print("  ⚠️  Please edit .env file to add your API credentials (optional)")
        return True
    else:
        # Create basic .env file
        env_content = """
# Basic configuration for quick start
DATABASE_URL=postgresql://cyber_user:cyber_secure_password_2024@postgres:5432/cyber_threat_db
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=cyber_graph_password_2024
REDIS_URL=redis://redis:6379
SECRET_KEY=cyber_threat_detection_secret_key_2024_secure
ENVIRONMENT=development
DEBUG=true
"""
        env_file.write_text(env_content.strip())
        print("  ✅ Created basic .env file")
        return True

def start_services():
    """Start Docker services"""
    print("\n🚀 Starting services...")
    
    try:
        # Build and start services
        print("  📦 Building containers...")
        subprocess.run(['docker-compose', 'build'], check=True)
        
        print("  🚀 Starting services...")
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        
        print("  ✅ Services started successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to start services: {e}")
        return False

def wait_for_services():
    """Wait for services to be ready"""
    print("\n⏳ Waiting for services to be ready...")
    
    services = [
        ('http://localhost:8000/health', 'Backend API'),
        ('http://localhost:8501', 'Frontend Dashboard'),
        ('http://localhost:7474', 'Neo4j Browser'),
    ]
    
    max_attempts = 30
    for url, name in services:
        print(f"  🔄 Waiting for {name}...")
        
        for attempt in range(max_attempts):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code in [200, 302]:
                    print(f"    ✅ {name} is ready")
                    break
            except requests.exceptions.RequestException:
                pass
            
            if attempt < max_attempts - 1:
                time.sleep(2)
        else:
            print(f"    ⚠️  {name} may not be ready yet (still starting up)")

def load_sample_data():
    """Load sample data for demonstration"""
    print("\n📊 Loading sample data...")
    
    try:
        # Check if backend API is available
        response = requests.get('http://localhost:8000/health', timeout=10)
        if response.status_code == 200:
            print("  ✅ Backend API is ready")
            
            # Try to load sample data
            sample_file = Path('data/samples/sample_posts.json')
            if sample_file.exists():
                print("  📥 Sample data file found")
                print("  ⚠️  Sample data loading will be implemented in the full system")
            else:
                print("  ⚠️  Sample data file not found, but system will work with API data")
        else:
            print("  ⚠️  Backend API not ready yet")
            
    except requests.exceptions.RequestException:
        print("  ⚠️  Could not connect to backend API (still starting up)")

def show_access_urls():
    """Show access URLs for different services"""
    print("\n🌐 Access URLs:")
    print("  📊 Main Dashboard:      http://localhost:8501")
    print("  🔧 API Documentation:   http://localhost:8000/docs")
    print("  📈 Neo4j Browser:       http://localhost:7474")
    print("  📝 Jupyter Lab:         http://localhost:8888")
    print("  📊 Kibana:              http://localhost:5601")
    print("\n🔑 Default Credentials:")
    print("  Neo4j:     neo4j / cyber_graph_password_2024")
    print("  Jupyter:   Token: cyber_research_token_2024")

def main():
    """Main function"""
    print_banner()
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Setup environment
    if not setup_environment():
        sys.exit(1)
    
    # Start services
    if not start_services():
        print("\n❌ Failed to start services. Check Docker logs for details:")
        print("   docker-compose logs")
        sys.exit(1)
    
    # Wait for services
    wait_for_services()
    
    # Load sample data
    load_sample_data()
    
    # Show access information
    show_access_urls()
    
    print("\n🎉 System is ready!")
    print("\n📚 Next steps:")
    print("  1. Open the dashboard: http://localhost:8501")
    print("  2. Explore the API docs: http://localhost:8000/docs")
    print("  3. Add your API credentials in .env file (optional)")
    print("  4. Check README.md for detailed documentation")
    
    print("\n🛑 To stop the system:")
    print("  docker-compose down")
    
    print("\n📊 To view logs:")
    print("  docker-compose logs -f")

if __name__ == "__main__":
    main()