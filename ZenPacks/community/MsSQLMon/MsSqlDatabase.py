################################################################################
#
# This program is part of the MsSQLMon Zenpack for Zenoss.
# Copyright (C) 2009-2012 Egor Puzanov.
#
# This program can be used under the GNU General Public License version 2
# You can find full information here: http://www.zenoss.com/oss
#
################################################################################

__doc__="""MsSqlDatabase

MsSqlDatabase is a MS SQL Database

$Id: MsSqlDatabase.py,v 1.3 2012/04/25 19:55:21 egor Exp $"""

__version__ = "$Revision: 1.3 $"[11:-2]

from Globals import InitializeClass

from ZenPacks.community.RDBMS.Database import Database
from Products.ZenModel.ZenossSecurity import *
from Products.ZenModel.ZenPackPersistence import ZenPackPersistence

DOT_GREEN    = 'green'
DOT_PURPLE   = 'purple'
DOT_BLUE     = 'blue'
DOT_YELLOW   = 'yellow'
DOT_ORANGE   = 'orange'
DOT_RED      = 'red'
DOT_GREY     = 'grey'

SEV_CLEAN    = 0
SEV_DEBUG    = 1
SEV_INFO     = 2
SEV_WARNING  = 3
SEV_ERROR    = 4
SEV_CRITICAL = 5


class MsSqlDatabase(Database):
    """
    Database object
    """

    ZENPACKID = 'ZenPacks.community.MsSQLMon'

    dbid = 0
    updateability = ''
    useraccess = ''
    recovery = ''
    collation = ''
    sqlsortorder = ''
    dbproperties = []
    status = 0

    statusmap ={0: (DOT_GREEN, SEV_CLEAN, 'ONLINE'),
                1: (DOT_YELLOW, SEV_WARNING, 'RESTORING'),
                2: (DOT_YELLOW, SEV_WARNING, 'RECOVERING'),
                3: (DOT_YELLOW, SEV_WARNING, 'RECOVERY PENDING'),
                4: (DOT_ORANGE, SEV_ERROR, 'SUSPECT'),
                5: (DOT_ORANGE, SEV_ERROR, 'EMERGENCY'),
                6: (DOT_RED, SEV_CRITICAL, 'OFFLINE'),
                }

    _properties = Database._properties + (
        {'id':'dbid', 'type':'int', 'mode':'w'},
        {'id':'updateability', 'type':'string', 'mode':'w'},
        {'id':'useraccess', 'type':'string', 'mode':'w'},
        {'id':'recovery', 'type':'string', 'mode':'w'},
        {'id':'collation', 'type':'string', 'mode':'w'},
        {'id':'sqlsortorder', 'type':'string', 'mode':'w'},
        {'id':'dbproperties', 'type':'lines', 'mode':'w'},
    )


    factory_type_information = (
        {
            'id'             : 'MsSqlDatabase',
            'meta_type'      : 'MsSqlDatabase',
            'description'    : """Arbitrary device grouping class""",
            'icon'           : 'FileSystem_icon.gif',
            'product'        : 'MsSQLMon',
            'factory'        : 'manage_addDatabase',
            'immediate_view' : 'viewMsSqlDatabase',
            'actions'        :
            (
                { 'id'            : 'status'
                , 'name'          : 'Status'
                , 'action'        : 'viewMsSqlDatabase'
                , 'permissions'   : (ZEN_VIEW,)
                },
                { 'id'            : 'events'
                , 'name'          : 'Events'
                , 'action'        : 'viewEvents'
                , 'permissions'   : (ZEN_VIEW, )
                },
                { 'id'            : 'perfConf'
                , 'name'          : 'Template'
                , 'action'        : 'objTemplates'
                , 'permissions'   : (ZEN_CHANGE_DEVICE, )
                },
                { 'id'            : 'viewHistory'
                , 'name'          : 'Modifications'
                , 'action'        : 'viewHistory'
                , 'permissions'   : (ZEN_VIEW_MODIFICATIONS,)
                },
            )
          },
        )

    def manageIp(self):
        """
        Return manageIp with DB Server Instance name if needed
        """
        manageIp = self.device().manageIp
        dbsi = self.dbsrvinstance()
        return dbsi and '%s\%s'%(manageIp, dbsi.dbsiname) or manageIp

    def port(self):
        """
        Return TCP port of DB Server Instance name if needed
        """
        dbsi = self.dbsrvinstance()
        return dbsi and dbsi.port or 1433

    def totalBytes(self):
        """
        Return the number of allocated bytes
        """
        datasize = self.cacheRRDValue('sysperfinfo_DataFilesSize', 0)
        logsize = self.cacheRRDValue('sysperfinfo_LogFilesSize', 0)
        return long(datasize + logsize)

    def usedBytes(self):
        """
        Return the number of used bytes
        """
        sa = self.cacheRRDValue('sysperfinfo_SpaceAvailable', 0)
        return self.totalBytes() - sa

InitializeClass(MsSqlDatabase)
