"""
newsApp/__init__.py

Package initialisation file for the Speedy Spectator news application.

Installs PyMySQL as a drop-in replacement for MySQLdb to allow Django
to connect to a MySQL database using the pure-Python PyMySQL driver.

This is required because mysqlclient (the C-based MySQLdb driver) can
be difficult to install on some systems, particularly macOS. PyMySQL
provides identical functionality in pure Python without requiring
any C extensions to be compiled.

This must be called before Django initialises the database connection,
which is why it is placed in __init__.py — this file is imported
automatically when the package is first loaded.
"""

import pymysql

# Install PyMySQL as a drop-in replacement for MySQLdb.
# This must be called before Django attempts to connect to the database.
# Without this, Django will raise an error if mysqlclient is not installed.
pymysql.install_as_MySQLdb()