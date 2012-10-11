
import Globals
import os.path

skinsDir = os.path.join(os.path.dirname(__file__), 'skins')
from Products.CMFCore.DirectoryView import registerDirectory
if os.path.isdir(skinsDir):
    registerDirectory(skinsDir, globals())

from Products.ZenModel.ZenPack import ZenPackBase

class ZenPack(ZenPackBase):
    """ MsSQLMon loader
    """
    packZProperties = [
            ('zMsSqlConnectionString', "'pyisqldb',DRIVER='{FreeTDS}',ansi=True,TDS_Version='8.0',SERVER='${here/manageIp}\${here/dbSrvInstName}',PORT=${here/port},DATABASE='master',UID='${here/zWinUser}',PWD='${here/zWinPassword}'", 'string'),
            ('zMsSqlSrvInstances', [], 'lines'),
            ]
