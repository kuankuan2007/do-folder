Command Line Interface
======================

For union command line interface, use

.. code-block:: shell
   
   do-folder [subcommand] [options]

or

.. code-block:: shell
   
   python3 -m doFolder [subcommand] [options]


Compare
~~~~~~~~~~~~~~

.. code-block:: shell
   
   do-folder compare [options] <path1> <path2>


or

.. code-block:: shell
   
   do-compare [options] <path1> <path2>

Options
''''''''''''

- ``-h``, ``--help``: show help message and exit
- ``-v``, ``--version``: show version and exit
- ``-C``, ``--compare-mode``: compare mode (SIZE, CONT, TIMETAG, TIMETAG_AND_SIZE, IGNORE)
- ``-S``, ``--sync``: sync two directories if different
- ``-D``, ``--sync-direction``: sync direction (BOTH, A2B, B2A, ASK)
- ``-O``, ``--overwrite``: overwrite mode (A2B, B2A, ASK, AUTO, IGNORE)
- ``--create-root``: create root directory if not exist
- ``-T``, ``--traceback``: show traceback information on error
- ``--no-color``: disable colored console output
- ``-R``, ``--relative-timestamp``: display relative or absolute timestamps (AUTO, ALWAYS, NEVER)