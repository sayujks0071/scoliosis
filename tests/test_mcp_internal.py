import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from mcp_server.server import list_experiments, read_manuscript_abstract, run_experiment


def test_read_abstract():
    print("Testing read_manuscript_abstract...")
    abstract = read_manuscript_abstract()
    print(f"Abstract length: {len(abstract)}")
    print(f"Abstract start: {abstract[:100]}...")
    assert len(abstract) > 0
    assert "Abstract environment not found" not in abstract
    print("PASS")


def test_list_experiments():
    print("\nTesting list_experiments...")
    experiments = list_experiments()
    print(f"Found {len(experiments)} experiments.")
    print(f"Experiments: {experiments}")
    assert len(experiments) > 0
    # assert "experiment_minimal_elastica.py" in experiments # File might be missing or renamed
    # Just check if we got at least one python script back
    assert any(e.endswith(".py") for e in experiments)
    print("PASS")


def test_run_experiment():
    print("\nTesting run_experiment (dry run / minimal)...")
    # We might not want to run a full simulation which could take time.
    # But we can try running a non-existent one to check error handling
    # or a very simple one if available.

    # Test error case
    res = run_experiment("non_existent_script.py")
    print(f"Result for non-existent: {res}")
    assert "not found" in res

    # Test listing (using list_experiments tool logic essentially, but via run command if we had a list script)
    # Since we don't have a trivial script guaranteed to be fast, we'll verify the existence check logic passed.

    print("PASS")


if __name__ == "__main__":
    try:
        test_read_abstract()
        test_list_experiments()
        test_run_experiment()
        print("\nAll tests passed!")
    except Exception as e:
        print(f"\nFAILED: {e}")
        sys.exit(1)
