"""
Requirements Compiler

This script analyzes Python files in a specified directory to compile a list of required packages.
It distinguishes between built-in modules, site-packages, and custom user modules.

Usage:
    python script.py [-s] <directory>

Options:
    -s    Save the requirements to a file instead of printing to stdout
    -c    Custome

The script provides methods to find requirements (optionally including custom modules),
save the requirements to a file, and run the entire process with options to save or print the results.
"""

import ast
import sys
import importlib
import argparse
from pathlib import Path
from typing import Optional, Iterable, Dict, List
from collections.abc import Iterable as IterableType

class Requirements:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.requirements = set()
        self.custom_modules = set()
        self.python_lib_path = Path(sys.executable).parent.parent / 'lib'
        self.site_packages_path = Path(self.__get_site_packages_path())
        self.requirements_found = False
        self.examined_module = self.directory.name

    def __get_site_packages_path(self):
        import site
        return site.getsitepackages()[0]

    def add(self, x: str, custom=False):
        if x == self.examined_module:
            return
        x = x.split('.')[0].split('-')[0]  # take first before dot and handle cases like 'package-name-1.0'
        self.requirements.add(x)
        if custom:
            self.custom_modules.add(x)

    def exclude(self, file_path: Path, exclude: Optional[Iterable[str]] = None) -> bool:
        if exclude is None:
            return False

        # Convert file_path to a relative path from self.directory
        relative_path = file_path.relative_to(self.directory)

        for excluded_item in exclude:
            excluded_path = Path(excluded_item)

            # Check if the file or any of its parent directories match the excluded item
            if any(part == excluded_path.name for part in relative_path.parts):
                return True

            # Check if the excluded item is a directory and is a parent of the file
            if excluded_path.parts[-1] in relative_path.parts:
                excluded_index = relative_path.parts.index(excluded_path.parts[-1])
                if relative_path.parts[:excluded_index + 1] == excluded_path.parts:
                    return True

        return False

    def find(self, custom: bool = True, exclude: Optional[Iterable[str]] = None):
        """
            Analyze Python files in the specified directory to find import requirements.

            This method scans all Python files in the directory (and subdirectories) for import statements.
            It identifies required packages, distinguishing between built-in modules, site-packages, and custom user modules.
            The method can optionally include custom modules in the requirements and exclude specified files or directories from analysis.

            Args:
                custom (bool, optional): If True, include custom (user-defined) modules in the requirements. Defaults to True.
                exclude (Optional[Iterable[str]], optional): A str or an iterable of strings
                representing file or directory names to exclude from analysis.
                Can be relative or absolute paths. Defaults to None.

            Returns:
                self: Returns the instance of the class for method chaining.

            Side effects:
                - Clears and updates self.requirements and self.custom_modules sets.
                - Sets self.requirements_found to True.

            Raises:
                Exception: Prints error message if there's an issue parsing a Python file.

            Example:
                compiler = RequirementsCompiler('/path/to/project')
                compiler.find(custom=False, exclude=['tests', 'examples'])
            """

        self.requirements.clear()
        self.custom_modules.clear()

        # exclude type validation
        if isinstance(exclude, str):
            exclude = [exclude]
        elif isinstance(exclude, IterableType) and all(isinstance(e, str) for e in exclude):
            pass
        elif exclude is None:
            pass
        else:
            raise TypeError(f'Parameter exclude must be type str or Iterable of str. Got {exclude}')

        for file_path in self.directory.rglob('*.py'):
            if self.exclude(file_path, exclude):
                continue
            with open(file_path, 'r') as file:
                try:
                    tree = ast.parse(file.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                self._add_import(alias.name.split('.')[0], custom)
                        elif isinstance(node, ast.ImportFrom):
                            if node.level == 0:  # absolute import
                                self._add_import(node.module.split('.')[0], custom)
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")

        self.requirements_found = True
        return self

    def _add_import(self, module_name, custom):
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, '__file__') and module.__file__:
                module_path = Path(module.__file__)
                if self.site_packages_path in module_path.parents:
                    # This is a site-package
                    top_level_package = self._get_top_level_package(module_path)
                    self.add(top_level_package, custom=False)
                elif self.python_lib_path in module_path.parents:
                    # This is a built-in module
                    return
                elif custom:
                    # This is a user module
                    self.add(module_name, custom=True)
            else:
                # Module without a file is typically a built-in
                return
        except ImportError:
            # If we can't import it, assume it's a user module
            if custom:
                self.add(module_name, custom=True)

    def _get_top_level_package(self, module_path):
        parts = module_path.relative_to(self.site_packages_path).parts
        return parts[0]

    def save(self):
        if not self.requirements_found:
            raise RuntimeError("Requirements have not been found yet. Call find() method first.")

        with open(self.directory / 'requirements.txt', 'w') as file:
            for req in sorted(self.requirements):
                file.write(f"{req}\n")
        print(f"Requirements saved to {self.directory / 'requirements.txt'}")

    def run(self, save: bool = False, custom: bool = True):
        reqs = self.find(custom=custom)
        if save:
            self.save()
        else:
            print("Found requirements:")
            for req in reqs:
                print(req)

        if self.custom_modules:
            print("\nCustom modules detected:")
            for module in sorted(self.custom_modules):
                print(module)


def requirements(*package_paths: str,
                 custom: bool = True,
                 exclude: Optional[Iterable[str]] = None) -> Dict[str, List[str]]:
    """
    Analyze multiple package directories and return their requirements.

    This function takes a list of package directory paths, analyzes each using
    the RequirementsCompiler, and returns a dictionary where each key is a
    package name and the value is a list of its requirements.

    Args:
        package_paths (str): paths to package directories to analyze.
        custom (bool): if custom modules are to be included
        exclude ([Iterable[str]]): an iterable of strings or a string

    Returns:
        Dict[str, List[str]]: A dictionary where keys are package names and values
                              are lists of package requirements.

    Raises:
        ValueError: If a given path does not exist or is not a directory.

    Example:
        paths = ['/path/to/package1', '/path/to/package2']
        requirements = analyze_package_requirements(paths)
        print(requirements)
        # Output: {'package1': ['numpy', 'pandas'], 'package2': ['requests', 'beautifulsoup4']}
    """
    results = {}

    for path in package_paths:
        package_path = Path(path)

        if not package_path.exists() or not package_path.is_dir():
            raise ValueError(f"Invalid package path: {path}")

        package_name = package_path.name
        compiler = Requirements(package_path)

        # Analyze the package
        compiler.find(custom=custom, exclude=exclude)  # Exclude custom modules

        # Store the requirements
        results[package_name] = sorted(compiler.requirements)

    return results


def main():
    parser = argparse.ArgumentParser(description="Compile requirements for a Python project.")
    parser.add_argument("directory", help="The directory to analyze")
    parser.add_argument("-s", "--save", action="store_true", help="Save the requirements to a file")
    parser.add_argument("-c", "--custom", action="store_true", help="Save the requirements to a file")
    args = parser.parse_args()

    compiler = Requirements(args.directory)
    compiler.run(save=args.save, custom=args.custom)


if __name__ == "__main__":
    main()
