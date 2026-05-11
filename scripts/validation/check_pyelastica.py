"""
Check if PyElastica is installed and functioning.
Usage: python scripts/check_pyelastica.py
"""
import sys


def check_pyelastica():
    try:
        import elastica
        # Try to get version, handle if not present
        version = getattr(elastica, "__version__", "unknown")
        print(f"Success: PyElastica is installed (version {version}).")

        # Simple smoke test
        from elastica import CosseratRod
        print("Success: Can import CosseratRod.")

        return 0
    except ImportError:
        print("Error: PyElastica is not installed.")
        print("To install, run:")
        print("  pip install pyelastica")
        print("Or visit: https://github.com/GazzolaLab/PyElastica")
        return 1
    except Exception as e:
        print(f"Error: PyElastica is installed but failed to load: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(check_pyelastica())
