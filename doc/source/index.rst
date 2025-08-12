doFolder Library Documentation
=================================

.. image:: https://badge.fury.io/py/doFolder.svg
   :target: https://badge.fury.io/py/doFolder
   :alt: PyPI version

.. image:: https://img.shields.io/badge/GitHub-Repository-181717?style=flat&logo=github
   :target: https://github.com/kuankuan2007/do-folder
   :alt: GitHub Repository

.. image:: https://img.shields.io/badge/license-MulanPSL--2.0-blue.svg
   :target: ./LICENSE
   :alt: License

Overview
=============================

The ``doFolder`` library is a comprehensive Python package designed to provide an object-oriented abstraction layer for file system operations. Built upon Python's standard ``pathlib`` module, it offers a robust and platform-independent approach to file and directory management with enhanced functionality for modern Python applications.

The library addresses common limitations in traditional file system manipulation by providing a unified interface that abstracts platform-specific details while maintaining full compatibility across Windows, macOS, and Linux environments.

API Reference
=============================

.. toctree::
   :maxdepth: 2
   :caption: Core API Documentation

   apis/doFolder

Architecture and Design Principles
======================================

Core Components
-------------------------------

The ``doFolder`` library is structured around several key architectural components:

**File System Abstraction Layer**
   The library implements a high-level abstraction that encapsulates file system entities as Python objects, providing intuitive methods for manipulation and querying.

**Path Management System**
   Built on Python's ``pathlib``, the path management system ensures robust handling of file system paths across different operating systems.

**Error Handling Framework**
   A comprehensive error handling system that provides configurable behavior for common file system operation scenarios.

**Content Management Interface**
   Specialized interfaces for handling different types of file content, including binary data, text, and structured formats like JSON.

Installation and Requirements
=============================

System Requirements
-------------------------------

* Python 3.8 or higher
* Cross-platform compatibility (Windows, macOS, Linux)

Installation
-------------------------------

The library can be installed using the Python Package Index:

.. code-block:: bash

   pip install doFolder

For development installations or bleeding-edge features, the library can be installed directly from the source repository.

Fundamental Concepts
=============================

Object-Oriented File System Model
-----------------------------------

The ``doFolder`` library treats file system entities as first-class objects, each with their own properties, methods, and behaviors. This approach provides several advantages:

* **Encapsulation**: File system operations are encapsulated within appropriate object methods
* **State Management**: Objects maintain their own state and can cache frequently-accessed information
* **Type Safety**: Full type annotations ensure better IDE support and runtime error detection

Primary Classes
-------------------------------

``File`` Class
   Represents individual files in the file system. Provides methods for content manipulation, metadata access, and file-specific operations.

``Directory`` Class
   Represents directories and provides methods for directory traversal, content listing, and hierarchical operations.

``Path`` Class
   An enhanced path representation that extends Python's ``pathlib`` with additional utility methods.

Basic Usage Patterns
=============================

File Operations
-------------------------------

The ``File`` class provides a comprehensive interface for file manipulation:

.. code-block:: python

   from doFolder import File

   # Instantiate a file object
   document = File("document.txt")
   
   # Access file properties
   file_size = document.state.st_size
   modification_time = document.state.st_mtime
   
   # Content operations
   content = document.content  # Returns bytes
   document.content = b"New content"
   
   # Structured data operations
   data = {"key": "value"}
   document.saveAsJson(data)
   loaded_data = document.loadAsJson()

Directory Operations
-------------------------------

The ``Directory`` class facilitates directory-level operations:

.. code-block:: python

   from doFolder import Directory, ItemType

   # Create directory object
   workspace = Directory("./workspace")
   
   # Create nested structures
   workspace.create("src/main", ItemType.DIR)
   workspace.create("tests/unit", ItemType.DIR)
   
   # File creation within directories
   main_file = workspace.create("src/main.py", ItemType.FILE)
   
   # Directory traversal
   for item in workspace.recursiveTraversal():
       print(f"Processing: {item.path}")

Advanced Functionality
=============================

Error Handling Strategies
-------------------------------

The library implements a sophisticated error handling system through the ``UnExistsMode`` enumeration:

.. code-block:: python

   from doFolder import File, UnExistsMode

   # Configure error handling behavior
   strict_file = File("critical.txt", unExistsMode=UnExistsMode.ERROR)
   lenient_file = File("optional.txt", unExistsMode=UnExistsMode.WARN)
   silent_file = File("cache.txt", unExistsMode=UnExistsMode.IGNORE)
   auto_create = File("log.txt", unExistsMode=UnExistsMode.CREATE)

File System Comparison
-------------------------------

The library provides sophisticated comparison capabilities for both individual files and entire directory structures:

.. code-block:: python

   from doFolder import compare
   from doFolder.compare import getDifference

   # File comparison
   result = compare.compare(file1, file2)
   
   # Directory comparison with detailed difference analysis
   differences = getDifference(source_dir, target_dir)

Content Integrity Verification
-------------------------------

Built-in hashing functionality supports content integrity verification:

.. code-block:: python

   from doFolder import File

   critical_file = File("important_data.bin")
   
   # Generate hash for integrity checking
   original_hash = critical_file.hash()
   
   # After operations, verify integrity
   if critical_file.hash() == original_hash:
       print("File integrity maintained")

Migration Considerations
=============================

Version 2.x Migration
-------------------------------

The doFolder library version 2.x introduces several architectural improvements while maintaining backward compatibility. Key changes include:

**Class Renaming**
   The ``Folder`` class has been renamed to ``Directory`` for improved semantic clarity. The original ``Folder`` class remains available for backward compatibility.

**Enhanced Type System**
   Full type annotations have been added throughout the library, improving IDE support and enabling static type checking.

**Pathlib Integration**
   The underlying path handling system now utilizes Python's standard ``pathlib`` module for improved robustness and performance.

Existing code using version 1.x remains functional:

.. code-block:: python

   # Legacy code continues to work
   from doFolder import Folder
   legacy_folder = Folder("./data")
   
   # Recommended approach for new code
   from doFolder import Directory
   modern_directory = Directory("./data")

Version History
=============================

.. toctree::

   ./changelog

Development and Contribution
=============================

The doFolder project follows standard open-source development practices. Contributions are welcomed through the project's GitHub repository at https://github.com/kuankuan2007/do-folder.

Development Guidelines
-------------------------------

* All contributions must include appropriate unit tests
* Code must conform to the project's established style guidelines
* New features should include corresponding documentation updates
* Bug reports should include minimal reproduction cases

Legal Information
=============================

This software is distributed under the MulanPSL-2.0 License. The complete license text is available in the project repository and governs all use, modification, and distribution of the software.
