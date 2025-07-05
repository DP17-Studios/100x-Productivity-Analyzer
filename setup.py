#!/usr/bin/env python3
"""
Setup script for the Productivity Agent
"""

import os
import sys
import subprocess
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = ['data', 'logs', 'data/embeddings']
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Created directory: {directory}")

def fix_dependency_versions():
    """Fix pydantic and numpy version conflicts before installing other requirements"""
    try:
        import pkg_resources
        # Check if we need packaging module
        try:
            from packaging import version as pkg_version
        except ImportError:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'packaging'])
            from packaging import version as pkg_version
        
        upgrades_needed = []
        
        # Check pydantic
        try:
            pydantic_version = pkg_resources.get_distribution("pydantic").version
            if pkg_version.parse(pydantic_version) < pkg_version.parse("2.11.5"):
                upgrades_needed.append("pydantic>=2.11.5")
                print(f"Need to upgrade pydantic from {pydantic_version} to >=2.11.5")
        except pkg_resources.DistributionNotFound:
            print("Pydantic not installed yet")
        
        # Check numpy
        try:
            numpy_version = pkg_resources.get_distribution("numpy").version
            if pkg_version.parse(numpy_version) < pkg_version.parse("2.0.0"):
                upgrades_needed.append("numpy>=2.0.0")
                print(f"Need to upgrade numpy from {numpy_version} to >=2.0.0")
        except pkg_resources.DistributionNotFound:
            print("Numpy not installed yet")
        
        # Perform upgrades if needed
        if upgrades_needed:
            print(f"Upgrading: {', '.join(upgrades_needed)}")
            cmd = [sys.executable, '-m', 'pip', 'install', '--upgrade'] + upgrades_needed
            subprocess.check_call(cmd)
            print("✓ Dependencies upgraded successfully")
        else:
            print("✓ All core dependencies meet version requirements")
            
    except Exception as e:
        print(f"Could not check/upgrade dependency versions: {e}")

def install_requirements():
    """Install Python requirements"""
    # First fix dependency version conflicts
    print("Checking dependency versions...")
    fix_dependency_versions()
    
    try:
        print("Installing comprehensive requirements...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        print("✓ All requirements installed successfully")
        print("🎉 Full functionality available: GitHub, Jira, Slack, LlamaIndex, Composio")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install requirements: {e}")
        print("\nTrying to resolve common issues...")
        
        # Try fixing dependency conflicts first
        try:
            print("Attempting to fix dependency conflicts...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel'])
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '--upgrade', 'pydantic>=2.11.5', 'numpy>=2.0.0'])
            
            # Retry main installation
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
            print("✓ Requirements installed after fixing conflicts")
            print("🎉 Full functionality available")
            return True
        except subprocess.CalledProcessError as e2:
            print(f"✗ Failed after conflict resolution: {e2}")
            print("\nTrying essential packages only:")
            
            try:
                # Install core packages
                essential_packages = [
                    'python-dotenv>=1.0.0',
                    'requests>=2.31.0',
                    'rich>=13.7.0',
                    'pandas>=2.0.0',
                    'numpy>=2.0.0',
                    'pydantic>=2.11.5',
                    'PyGithub>=2.3.0',
                    'jira>=3.8.0',
                    'slack-sdk>=3.29.0'
                ]
                
                print("Installing essential packages for basic functionality...")
                for package in essential_packages:
                    try:
                        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                        print(f"  ✓ {package}")
                    except subprocess.CalledProcessError:
                        print(f"  ✗ {package} (skipped)")
                
                print("\n✓ Essential packages installed")
                print("⚠️  Advanced features (LlamaIndex, Composio) may be unavailable")
                print("\nRecommendation: Run 'python fix_pydantic.py' to resolve conflicts")
                return True
                
            except subprocess.CalledProcessError as e3:
                print(f"✗ Essential package installation failed: {e3}")
                print("\n=== Manual Installation Required ===")
                print("Please try these steps:")
                print("1. python fix_pydantic.py")
                print("2. pip install --upgrade pip")
                print("3. pip install python-dotenv requests rich PyGithub")
                print("4. python main.py")
                return False

def create_env_file():
    """Create .env file if it doesn't exist"""
    if os.path.exists('.env'):
        print("✓ .env file already exists")
        return
    
    if os.path.exists('.env.example'):
        try:
            # Copy .env.example to .env
            with open('.env.example', 'r') as example:
                content = example.read()
            
            with open('.env', 'w') as env_file:
                env_file.write(content)
            
            print("✓ Created .env file from template")
            print("⚠️  Please edit .env file and add your API keys")
        except Exception as e:
            print(f"✗ Failed to create .env file: {e}")
    else:
        print("✗ .env.example file not found")

def test_setup():
    """Test the setup by running basic tests"""
    try:
        print("\nRunning basic tests...")
        result = subprocess.run([sys.executable, 'test_agent.py'], 
                              capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✓ Basic tests passed")
            return True
        else:
            print(f"✗ Tests failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("✗ Tests timed out")
        return False
    except Exception as e:
        print(f"✗ Failed to run tests: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Productivity Agent Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("✗ Python 3.8+ required")
        sys.exit(1)
    
    print(f"✓ Python {sys.version.split()[0]} detected")
    
    # Create directories
    print("\nCreating directories...")
    create_directories()
    
    # Install requirements
    print("\nInstalling dependencies...")
    if not install_requirements():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Create .env file
    print("\nSetting up configuration...")
    create_env_file()
    
    # Test setup
    print("\nTesting setup...")
    test_passed = test_setup()
    
    # Final instructions
    print("\n" + "=" * 50)
    if test_passed:
        print("✅ Setup completed successfully!")
    else:
        print("⚠️  Setup completed with warnings")
    
    print("\nNext steps:")
    print("1. Edit .env file with your API keys")
    print("2. Test with: python test_agent.py")
    print("3. Run analysis: python main.py --run-now")
    print("4. Start automation: python main.py")
    print("\nFor help, see README.md")
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nSetup failed: {e}")
        sys.exit(1)