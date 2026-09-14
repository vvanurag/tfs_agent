import importlib
import sys

print("=" * 45)
print("PYTHON ENVIRONMENT VERIFICATION")
print("=" * 45)
print(f"Executable Path : {sys.executable}")
print(f"Python Version  : {sys.version.split()[0]}")

# Check expected Conda environment
if "ai_agent" in sys.executable:
    print("Environment Status: [OK] Running inside 'ai_agent' environment")
else:
    print(
        "Environment Status: [WARNING] Not running inside 'ai_agent' environment"
    )

print("-" * 45)
print("DEPENDENCY CHECK")
print("-" * 45)

packages = ["pydantic", "tenacity", "requests", "requests_ntlm"]

for package in packages:
    try:
        mod = importlib.import_module(package)
        version = getattr(mod, "__version__", "Installed")
        print(f"  [OK]   {package:<15} -> {version}")
    except ImportError:
        print(f"  [FAIL] {package:<15} -> NOT INSTALLED")

print("=" * 45)