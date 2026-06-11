import sys
import subprocess

def run_tests():
    """Runs tests and outputs summary."""
    print("Running tests with pytest...")
    
    # Run pytest with coverage
    cmd = ["python", "-m", "pytest", "-v", "--cov=.", "tests/"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Print the output to the console
    print(result.stdout)
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
        
    # Write the output to a summary report
    with open("test_summary_report.txt", "w") as f:
        f.write("=== TEST SUMMARY REPORT ===\n\n")
        f.write(result.stdout)
        if result.stderr:
            f.write("\n=== STDERR ===\n\n")
            f.write(result.stderr)
            
    print(f"Tests finished with exit code {result.returncode}. Report saved to test_summary_report.txt.")
    
    # Return the exit code of pytest
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
