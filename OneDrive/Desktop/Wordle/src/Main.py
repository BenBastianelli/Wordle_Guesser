import os
import re
import subprocess
import sys
import pkg_resources
import importlib

# List of standard library modules (these don't need to be installed)
STANDARD_LIBRARIES = {
    'os', 'sys', 'collections'
}

def list_versions(filename_prefix):
    """List all versions of the specified Python files that start with the given prefix."""
    directory = os.getcwd()  # Current directory
    return [f for f in os.listdir(directory) if f.startswith(filename_prefix) and f.endswith('.py')]

def check_and_install_dependencies(requirements):
    """Check and install missing dependencies."""
    for requirement in requirements:
        # Skip installing standard libraries
        if requirement in STANDARD_LIBRARIES:
            print(f"Skipping standard library: {requirement}")
            continue

        try:
            # Only install the package if it's a valid requirement string
            pkg_resources.require(requirement)
        except pkg_resources.DistributionNotFound:
            print(f"Installing missing dependency: {requirement}")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', requirement])

def extract_imports(filepath):
    """Extract package names from import statements."""
    packages = []
    with open(filepath, 'r', encoding='utf-8') as f:  # Specify 'utf-8' encoding
        for line in f:
            match = re.match(r'^(?:import|from)\s+([a-zA-Z0-9_]+)', line)
            if match:
                package = match.group(1)
                # Add the package to the list if it's a valid package
                if package not in packages:
                    packages.append(package)
    return packages


def main():
    filename_prefix = 'Wordle_'  # Files start with Wordle_ (e.g., Wordle_v1.py, Wordle_v2.py)

    # List available versions
    versions = list_versions(filename_prefix)
    if not versions:
        print("No versions found.")
        return

    print("Available versions:")
    for idx, version in enumerate(versions, 1):
        print(f"{idx}. {version}")

    # Let the user select a version
    choice = int(input("Select a version to execute (number): ")) - 1
    if choice < 0 or choice >= len(versions):
        print("Invalid selection.")
        return

    selected_file = versions[choice]
    print(f"Selected file: {selected_file}")

    # Get valid dependencies (package names) and install them
    dependencies = extract_imports(selected_file)
    print(f"Dependencies: {dependencies}")
    if dependencies:
        check_and_install_dependencies(dependencies)

    # Execute the selected file
    print(f"Executing {selected_file}...")
    subprocess.run([sys.executable, selected_file])

if __name__ == "__main__":
    main()
