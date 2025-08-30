#!/usr/bin/env python3
"""
Test runner script for the Cyber Threat Detection System
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print("✅ SUCCESS")
        if result.stdout:
            print("STDOUT:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        print("STDERR:", e.stderr)
        if e.stdout:
            print("STDOUT:", e.stdout)
        return False

def run_unit_tests():
    """Run unit tests"""
    command = ["python", "-m", "pytest", "tests/unit/", "-v", "--tb=short"]
    return run_command(command, "Unit Tests")

def run_integration_tests():
    """Run integration tests"""
    command = ["python", "-m", "pytest", "tests/integration/", "-v", "--tb=short"]
    return run_command(command, "Integration Tests")

def run_all_tests():
    """Run all tests"""
    command = ["python", "-m", "pytest", "tests/", "-v", "--tb=short"]
    return run_command(command, "All Tests")

def run_tests_with_coverage():
    """Run tests with coverage report"""
    command = [
        "python", "-m", "pytest", "tests/", 
        "--cov=backend/app", 
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "-v"
    ]
    return run_command(command, "Tests with Coverage")

def run_code_quality_checks():
    """Run code quality checks"""
    checks_passed = 0
    total_checks = 3
    
    # Black formatter check
    if run_command(["python", "-m", "black", "--check", "backend/"], "Black Code Formatting Check"):
        checks_passed += 1
    
    # Flake8 linting
    if run_command(["python", "-m", "flake8", "backend/app/", "--max-line-length=100"], "Flake8 Linting"):
        checks_passed += 1
    
    # MyPy type checking (optional, may have many warnings initially)
    if run_command(["python", "-m", "mypy", "backend/app/", "--ignore-missing-imports"], "MyPy Type Checking"):
        checks_passed += 1
    
    print(f"\n📊 Code Quality Summary: {checks_passed}/{total_checks} checks passed")
    return checks_passed == total_checks

def install_test_dependencies():
    """Install testing dependencies"""
    command = ["python", "-m", "pip", "install", "-r", "requirements.txt"]
    return run_command(command, "Installing Test Dependencies")

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Test runner for Cyber Threat Detection System")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage")
    parser.add_argument("--quality", action="store_true", help="Run code quality checks")
    parser.add_argument("--install", action="store_true", help="Install dependencies first")
    parser.add_argument("--all", action="store_true", help="Run everything")
    
    args = parser.parse_args()
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    print("🔍 Cyber Threat Detection System - Test Runner")
    print(f"📁 Working directory: {os.getcwd()}")
    
    success = True
    
    if args.install or args.all:
        success &= install_test_dependencies()
    
    if args.unit:
        success &= run_unit_tests()
    elif args.integration:
        success &= run_integration_tests()
    elif args.coverage:
        success &= run_tests_with_coverage()
    elif args.quality:
        success &= run_code_quality_checks()
    elif args.all:
        print("\n🚀 Running complete test suite...")
        success &= run_unit_tests()
        success &= run_integration_tests()
        success &= run_tests_with_coverage()
        success &= run_code_quality_checks()
    else:
        # Default: run all tests
        success &= run_all_tests()
    
    # Final summary
    print(f"\n{'='*60}")
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ The system is ready for deployment")
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Please fix the issues before deployment")
    print(f"{'='*60}")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)