#!/usr/bin/env python3
"""
Improved Quick Start Script for Cyber Threat Detection System
Handles prerequisites, environment setup, service startup, and access info
"""

import os
import sys
import subprocess
import time
import requests
import shutil
from pathlib import Path

# ---------- Styling Helpers ----------
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    CYAN = "\033[96m"
    RESET = "\033[0m"
    BOLD = "\033[1m"

def log(msg, color=Colors.CYAN, symbol="ℹ️ "):
    print(f"{color}{symbol} {msg}{Colors.RESET}")

def success(msg):
    log(msg, Colors.GREEN, "✅")

def warning(msg):
    log(msg, Colors.YELLOW, "⚠️ ")

def error(msg):
    log(msg, Colors.RED, "❌")

# ---------- Banner ----------
def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}
╔═══════════════════════════════════════════════════════════════╗
║              Cyber Threat Detection System                    ║
║              Quick Start Setup Script                         ║
╚═══════════════════════════════════════════════════════════════╝
{Colors.RESET}
    """
    print(banner)

# ---------- Prerequisite Check ----------
def check_prerequisites():
    log("Checking prerequisites...")
    prerequisites = [
        ('docker', 'Docker'),
        ('docker-compose', 'Docker Compose')
    ]

    missing = []
    for cmd, name in prerequisites:
        try:
            subprocess.run([cmd, '--version'], capture_output=True, check=True)
            success(f"{name} is installed")
        except (subprocess.CalledProcessError, FileNotFoundError):
            error(f"{name} is not installed")
            missing.append(name)

    if missing:
        error(f"Missing prerequisites: {', '.join(missing)}")
        print("👉 Please install them and re-run this script.")
        return False

    success("All prerequisites satisfied!")
    return True

# ---------- Environment Setup ----------
def setup_environment():
    log("Setting up environment...")
    env_file = Path('.env')
    env_template = Path('.env.template')

    if env_file.exists():
        warning(".env file already exists")
        choice = input("Do you want to overwrite it with defaults? (y/N): ").lower()
        if choice != "y":
            success("Keeping existing .env file")
            return True

    if env_template.exists():
        shutil.copy(env_template, env_file)
        success("Created .env file from template")
    else:
        env_content = """
# Quick Start Configuration
DATABASE_URL=postgresql://cyber_user:cyber_secure_password_2024@postgres:5432/cyber_threat_db
NEO4J_URI=bolt://neo4j:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=cyber_graph_password_2024
REDIS_URL=redis://redis:6379
SECRET_KEY=cyber_threat_detection_secret_key_2024
ENVIRONMENT=development
DEBUG=true
"""
        env_file.write_text(env_content.strip())
        success("Created basic .env file")

    warning("⚠️ Please update .env with API credentials (if available)")
    return True

# ---------- Docker Services ----------
def start_services():
    log("Starting services with Docker Compose...")
    try:
        subprocess.run(['docker-compose', 'build'], check=True)
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        success("Services started successfully!")
        return True
    except subprocess.CalledProcessError as e:
        error(f"Failed to start services: {e}")
        return False

def stop_services():
    log("Stopping all services...")
    try:
        subprocess.run(['docker-compose', 'down'], check=True)
        success("All services stopped.")
    except subprocess.CalledProcessError as e:
        error(f"Failed to stop services: {e}")

# ---------- Service Readiness ----------
def wait_for_services():
    log("Waiting for services to be ready...")

    services = [
        ('http://localhost:8000/health', 'Backend API'),
        ('http://localhost:8501', 'Frontend Dashboard'),
        ('http://localhost:7474', 'Neo4j Browser'),
    ]

    for url, name in services:
        print(f"  ⏳ {name} ... ", end="")
        sys.stdout.flush()

        for attempt in range(20):
            try:
                response = requests.get(url, timeout=5)
                if response.status_code in [200, 302]:
                    print(f"{Colors.GREEN}READY{Colors.RESET}")
                    break
            except requests.exceptions.RequestException:
                pass

            time.sleep(2)
        else:
            print(f"{Colors.YELLOW}still starting...{Colors.RESET}")

# ---------- Sample Data ----------
def load_sample_data():
    log("Loading sample data...")
    sample_file = Path('data/samples/sample_posts.json')

    try:
        response = requests.get('http://localhost:8000/health', timeout=10)
        if response.status_code == 200:
            success("Backend API is live")
            if sample_file.exists():
                success("Sample data file found (loading skipped in demo)")
            else:
                warning("No sample data file found (system still usable)")
        else:
            warning("Backend API not ready yet")
    except requests.exceptions.RequestException:
        warning("Could not connect to backend API")

# ---------- Access Info ----------
def show_access_urls():
    print(f"""
{Colors.BOLD}{Colors.CYAN}🌐 Access URLs:{Colors.RESET}
  📊 Dashboard:       {Colors.GREEN}http://localhost:8501{Colors.RESET}
  🔧 API Docs:        {Colors.GREEN}http://localhost:8000/docs{Colors.RESET}
  📈 Neo4j Browser:   {Colors.GREEN}http://localhost:7474{Colors.RESET}
  📝 Jupyter Lab:     {Colors.GREEN}http://localhost:8888{Colors.RESET}
  📊 Kibana:          {Colors.GREEN}http://localhost:5601{Colors.RESET}

{Colors.BOLD}🔑 Default Credentials:{Colors.RESET}
  Neo4j:     {Colors.CYAN}neo4j / cyber_graph_password_2024{Colors.RESET}
  Jupyter:   {Colors.CYAN}Token: cyber_research_token_2024{Colors.RESET}
""")

# ---------- Main ----------
def main():
    print_banner()

    if not check_prerequisites():
        sys.exit(1)

    if not setup_environment():
        sys.exit(1)

    if not start_services():
        sys.exit(1)

    wait_for_services()
    load_sample_data()
    show_access_urls()

    print(f"""
🎉 {Colors.GREEN}System is ready!{Colors.RESET}

📚 Next steps:
  1. Open Dashboard: http://localhost:8501
  2. Explore API Docs: http://localhost:8000/docs
  3. Edit .env file to add credentials
  4. Check README.md for documentation

🛑 To stop the system:
  {Colors.CYAN}docker-compose down{Colors.RESET}

📊 To view logs:
  {Colors.CYAN}docker-compose logs -f{Colors.RESET}
""")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        warning("Interrupted by user. Stopping services...")
        stop_services()
