"""
Check if all required packages are installed
Run this before using the database features
"""

import sys

def check_package(package_name, import_name=None):
    """Check if a package is installed"""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        print(f"✅ {package_name} is installed")
        return True
    except ImportError:
        print(f"❌ {package_name} is NOT installed")
        return False

def main():
    print("=" * 60)
    print("🔍 Checking Required Packages")
    print("=" * 60)
    
    packages = [
        ("SQLAlchemy", "sqlalchemy"),
        ("pandas", "pandas"),
        ("numpy", "numpy"),
        ("Flask", "flask"),
        ("Flask-Mail", "flask_mail"),
        ("scikit-learn", "sklearn"),
        ("scipy", "scipy"),
        ("gensim", "gensim"),
        ("implicit", "implicit"),
        ("nltk", "nltk"),
        ("requests", "requests"),
        ("pytube", "pytube"),
    ]
    
    missing = []
    installed = []
    
    for package_name, import_name in packages:
        if check_package(package_name, import_name):
            installed.append(package_name)
        else:
            missing.append(package_name)
    
    print("\n" + "=" * 60)
    print(f"📊 Summary: {len(installed)}/{len(packages)} packages installed")
    print("=" * 60)
    
    if missing:
        print(f"\n❌ Missing packages: {', '.join(missing)}")
        print("\n💡 To install missing packages, run:")
        print("   pip install -r requirements.txt")
        print("\nOr install individually:")
        for pkg in missing:
            print(f"   pip install {pkg}")
        return False
    else:
        print("\n✅ All required packages are installed!")
        print("🚀 You can now run:")
        print("   python setup_database.py")
        print("   python main.py")
        print("   python test_database.py")
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

