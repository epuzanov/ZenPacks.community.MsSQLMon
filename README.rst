================================
ZenPacks.community.MsSQLMon
================================

About
=====

This project is `Zenoss <http://www.zenoss.com/>`_ extension (ZenPack) that
makes it possible to model and monitor MS SQL databases.

Requirements
============

Zenoss
------

You must first have, or install, Zenoss 2.5.2 or later. This ZenPack was tested
against Zenoss 2.5.2, Zenoss 3.2 and Zenoss 4.2. You can download the free Core
version of Zenoss from http://community.zenoss.org/community/download

ZenPacks
--------

You must first install

- `SQLDataSource ZenPack <http://community.zenoss.org/docs/DOC-5913>`_
- `RDBMS Monitoring ZenPack <http://community.zenoss.org/docs/DOC-3447>`_

External dependencies
---------------------

You can use **pyisqldb** module provided by SQLDataSource ZenPack in combination
with `FreeTDS <http://www.freetds.org/>`_ ODBC driver, or install Python
DB-API 2.0 compatible `pymssql <http://code.google.com/p/pymssql/>`_ module.
**pymssql** can be installed with **easy_install-2.6** command as **zenoss**
user. Note that **pymssql** module used FreeTDS driver too.

- **pyisqldb** - DB-API 2.0 compatible wrapper for **isql** command from
  `unixODBC <http://www.unixodbc.org/>`_. FreeTDS ODBC driver must be
  installed and registered with name "FreeTDS".

  zMsSqlConnectionString example (with named instances):

      ::

          'pyisqldb',DRIVER='{FreeTDS}',ansi=True,TDS_Version='8.0',SERVER='${here/manageIp}\${here/dbSrvinstName}',DATABASE='master',UID='${here/zWinUser}',PWD='${here/zWinPassword}'

- `pyodbc <http://code.google.com/p/pyodbc/>`_ - DB-API 2.0 compatible interface
  to unixODBC. FreeTDS ODBC driver must be installed and registered with name
  "FreeTDS".

  zMsSqlConnectionString example (with TCP Port):

      ::

          'pyodbc',DRIVER='{FreeTDS}',ansi=True,TDS_Version='8.0',SERVER='${dev/manageIp}',PORT='1433',DATABASE='master',UID='${here/zWinUser}',PWD='${here/zWinPassword}'

- `pymssql <http://code.google.com/p/pymssql/>`_ - DB-API 2.0 compatible interface
  to unixODBC.

  zMsSqlConnectionString example:

      ::

          'pymssql',host='${dev/manageIp}:${here/port}',database='master',user='${here/zWinUser}',password='${here/zWinPassword}',timeout=10

Installation
============

If you have an old version (ZenPacks.community.MsSQLMon_ODBC) of this ZenPack
installed, please uninstall it first.

Normal Installation (packaged egg)
----------------------------------

Download the `MsSQLMon ZenPack <http://community.zenoss.org/docs/DOC-3391>`_.
Copy this file to your Zenoss server and run the following commands as the zenoss
user.

    ::

        zenpack --install ZenPacks.community.MsSQLMon-3.4.egg
        zenoss restart

Developer Installation (link mode)
----------------------------------

If you wish to further develop and possibly contribute back to the MsSQLMon
ZenPack you should clone the git `repository <https://github.com/epuzanov/ZenPacks.community.MsSQLMon>`_,
then install the ZenPack in developer mode using the following commands.

    ::

        git clone git://github.com/epuzanov/ZenPacks.community.MsSQLMon.git
        zenpack --link --install ZenPacks.community.MsSQLMon
        zenoss restart


Usage
=====

Installing the ZenPack will add the following items to your Zenoss system.

Configuration Properties
------------------------

- zMsSqlConnectionString - connection string template.
- zMsSqlSrvInstances - list of MS SQL Server instances names or TCP ports
- zWinUser - username
- zWinPassword - password

Modeler Plugins
---------------

- community.sql.MsSqlDatabaseMap

Monitoring Templates
--------------------

- MsSqlSrvInst
- MsSqlDatabase

Performance graphs
------------------

- MsSqlSrvInst

  - SQL Lock Requests
  - SQL Lock Timeouts
  - SQL Lock Wait Time
  - SQL Deadlocks
  - SQL Errors
  - SQL Connections
  - SQL Server Memory
  - SQL Cache Hit Ratio
  - SQL Memory Pages
  - SQL Page Life Expectancy
  - SQL Scans
  - SQL Statistics

- MsSqlDatabase

  - Database Files Size
  - Transactions
  - Log Flusches
  - Throughput
  - Pending Transactions
