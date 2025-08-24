Command Line Interface
======================

The doFolder package provides a comprehensive command-line interface for file and directory management operations. The CLI supports various subcommands for different tasks like comparing directories and calculating file hashes.

Usage Modes
~~~~~~~~~~~~

The doFolder CLI provides two equivalent usage modes after installation via pip:

**Unified Interface**

.. code-block:: shell
   
   do-folder [subcommand] [options]
   python3 -m doFolder [subcommand] [options]

**Direct Commands** (shortcuts for specific subcommands)

.. code-block:: shell
   
   do-compare [options]    # Equivalent to: do-folder compare [options]
   do-hash [options]       # Equivalent to: do-folder hash [options]

Both modes provide identical functionality - the direct commands are convenient shortcuts for frequently used operations.

Global Options
~~~~~~~~~~~~~~

All commands support these global options:

.. code-block:: text

   -v, --version         Show version information
   -vv, --full-version   Show detailed version information including Python details
   -w, --console-width INT   Set console width for output formatting
   --no-color           Disable colored output
   -m, --mute-warning    Suppress warning messages
   -t, --traceback      Show full traceback on errors
   -h, --help            Show this help message and exit

Compare Command
~~~~~~~~~~~~~~~

The compare command allows you to compare two files or directories and optionally synchronize them.

Basic Usage
^^^^^^^^^^^

.. code-block:: shell
   
   # Unified interface
   do-folder compare path_A path_B [options]
   python3 -m doFolder compare path_A path_B [options]
   
   # Direct command (equivalent)
   do-compare path_A path_B [options]

Arguments
^^^^^^^^^

.. code-block:: text

   path_A               Path to the first file or directory
   path_B               Path to the second file or directory

Options
^^^^^^^

.. code-block:: text

   -C, --compare-mode {SIZE,CONTENT,TIMETAG,TIMETAG_AND_SIZE,IGNORE}
                        How to compare two files (default: TIMETAG_AND_SIZE)
                        SIZE: Compare by file size only
                        CONTENT: Compare by file content
                        TIMETAG: Compare by modification timestamp
                        TIMETAG_AND_SIZE: Compare by both timestamp and size
                        IGNORE: Ignore all differences
   
   -S, --sync           Synchronize the directories if they are different
   
   -D, --sync-direction {BOTH,A2B,B2A,ASK}
                        Direction of synchronization (default: ASK)
                        BOTH: Synchronize in both directions
                        A2B: Synchronize from A to B only
                        B2A: Synchronize from B to A only
                        ASK: Prompt user for direction
   
   -O, --overwrite [{A2B,B2A,ASK,AUTO,IGNORE}]
                        Overwrite mode (default: ASK)
                        A2B: Always overwrite B with A
                        B2A: Always overwrite A with B
                        ASK: Prompt user for each conflict
                        AUTO: Automatically decide based on modification time
                        IGNORE: Skip all overwrites
   
   --create-root        Create root directory if it does not exist
   
   -R, --relative-timestamp [{ALWAYS,NEVER,AUTO}]
                        Timestamp display format (default: AUTO)
                        ALWAYS: Always show relative timestamps
                        NEVER: Always show absolute timestamps
                        AUTO: Automatically choose based on time difference

Examples
^^^^^^^^

Compare two directories:

.. code-block:: shell
   
   # Using unified interface
   do-folder compare /path/to/dir1 /path/to/dir2
   
   # Using direct command (equivalent)
   do-compare /path/to/dir1 /path/to/dir2

Compare and synchronize directories:

.. code-block:: shell
   
   # Using unified interface
   do-folder compare /path/to/source /path/to/backup --sync --sync-direction A2B
   
   # Using direct command (equivalent)
   do-compare /path/to/source /path/to/backup --sync --sync-direction A2B

Compare files by content:

.. code-block:: shell
   
   # Using unified interface
   do-folder compare file1.txt file2.txt --compare-mode CONTENT
   
   # Using direct command (equivalent)
   do-compare file1.txt file2.txt --compare-mode CONTENT

Hash Command
~~~~~~~~~~~~

The hash command calculates and displays hash values for files using various algorithms.

Basic Usage
^^^^^^^^^^^

.. code-block:: shell
   
   # Unified interface
   do-folder hash [options] files...
   python3 -m doFolder hash [options] files...
   
   # Direct command (equivalent)
   do-hash [options] files...

Default Behavior
^^^^^^^^^^^^^^^^

When no specific algorithms are specified, the command uses the default hash algorithm:

.. code-block:: shell
   
   # Using unified interface
   do-folder hash file1.txt file2.txt
   
   # Using direct command (equivalent)
   do-hash file1.txt file2.txt

Algorithm Selection
^^^^^^^^^^^^^^^^^^^

Use the ``-a`` option to specify custom algorithms:

.. code-block:: shell
   
   # Using unified interface
   do-folder hash -a sha1,md5 file1.txt file2.txt
   do-folder hash -a sha256 file1.txt -a blake2b file2.txt
   
   # Using direct command (equivalent)
   do-hash -a sha1,md5 file1.txt file2.txt
   do-hash -a sha256 file1.txt -a blake2b file2.txt

Options
^^^^^^^

.. code-block:: text

   -a, --algorithms ALGORITHMS FILES
                        Specify algorithms (comma-separated) followed by files.
                        Can be used multiple times.
                        Example: -a sha1,md5 file1.txt file2.txt
   
   -d, --allow-directory
                        Allow hashing of directories (hashes directory structure)
   
   -r, --recursive      Recursively hash all files in subdirectories
   
   -A, --disable-aggregate-algos
                        Disable aggregate algorithms for better performance
   
   -p, --to-absolute    Display absolute paths in output
   
   -f, --full-path      Always display the full path regardless of conflicts
   
   -s, --show-all       Display all progress bars in any situation
   
   -n, --thread-num INT Number of threads for parallel processing (default: 4)

Supported Algorithms
^^^^^^^^^^^^^^^^^^^^

The hash command supports various cryptographic hash algorithms including:

- **SHA family**: sha1, sha224, sha256, sha384, sha512
- **MD5**: md5
- **BLAKE2**: blake2b, blake2s
- **SHA3**: sha3_224, sha3_256, sha3_384, sha3_512
- And other algorithms supported by Python's hashlib

Examples
^^^^^^^^

Calculate SHA256 hash for a single file:

.. code-block:: shell
   
   # Using unified interface
   do-folder hash -a sha256 document.pdf
   
   # Using direct command (equivalent)
   do-hash -a sha256 document.pdf

Calculate multiple hashes for multiple files:

.. code-block:: shell
   
   # Using unified interface
   do-folder hash -a sha1,sha256,md5 file1.txt file2.txt
   
   # Using direct command (equivalent)
   do-hash -a sha1,sha256,md5 file1.txt file2.txt

Hash all files in a directory recursively:

.. code-block:: shell
   
   # Using unified interface
   do-folder hash -r -d /path/to/directory
   
   # Using direct command (equivalent)
   do-hash -r -d /path/to/directory

Use multiple algorithm groups:

.. code-block:: shell
   
   # Using unified interface
   do-folder hash -a sha256 *.txt -a md5 *.pdf
   
   # Using direct command (equivalent)
   do-hash -a sha256 *.txt -a md5 *.pdf

Performance and Threading
^^^^^^^^^^^^^^^^^^^^^^^^^

The hash command supports parallel processing for better performance:

.. code-block:: shell
   
   # Use 8 threads for faster processing (unified interface)
   do-folder hash -n 8 -r /large/directory
   
   # Use 8 threads for faster processing (direct command)
   do-hash -n 8 -r /large/directory
   
   # Show all progress bars for detailed monitoring (unified interface)
   do-folder hash -s -r /path/with/many/files
   
   # Show all progress bars for detailed monitoring (direct command)
   do-hash -s -r /path/with/many/files

Exit Codes
~~~~~~~~~~

All commands return standard exit codes:

- **0**: Success
- **1**: General error
- **2**: Command line argument error
- **Other**: Specific error codes depending on the operation