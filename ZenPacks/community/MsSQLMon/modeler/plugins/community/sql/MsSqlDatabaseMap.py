################################################################################
#
# This program is part of the MsSQLMon Zenpack for Zenoss.
# Copyright (C) 2009-2012 Egor Puzanov.
#
# This program can be used under the GNU General Public License version 2
# You can find full information here: http://www.zenoss.com/oss
#
################################################################################

__doc__="""MsSqlDatabaseMap.py

MsSqlDatabaseMap maps the MS SQL Databases table to Database objects

$Id: MsSqlDatabaseMap.py,v 1.8 2012/04/20 19:06:07 egor Exp $"""

__version__ = "$Revision: 1.8 $"[11:-2]

from Products.ZenModel.ZenPackPersistence import ZenPackPersistence
from Products.DataCollector.plugins.DataMaps import MultiArgs
from ZenPacks.community.SQLDataSource.SQLPlugin import SQLPlugin

QUERYINST = """SET NOCOUNT ON
DECLARE @InstanceName nvarchar(50)
DECLARE @value VARCHAR(100)
DECLARE @RegKey nvarchar(500)
SET @InstanceName=RTRIM(CONVERT(nVARCHAR,isnull(SERVERPROPERTY('INSTANCENAME'),'MSSQLSERVER')))
IF (SELECT Convert(varchar(1),(SERVERPROPERTY('ProductVersion'))))<>8
BEGIN
EXECUTE xp_regread
  @rootkey = 'HKEY_LOCAL_MACHINE',
  @key = 'SOFTWARE\Microsoft\Microsoft SQL Server\Instance Names\SQL',
  @value_name = @InstanceName,
  @value = @value OUTPUT
SET @RegKey='SOFTWARE\Microsoft\Microsoft SQL Server\\'+@value+'\MSSQLServer\SuperSocketNetLib\TCP\IPAll'
END
ELSE
BEGIN
IF @InstanceName='MSSQLSERVER'
BEGIN
SET @RegKey='SOFTWARE\Microsoft\'+@InstanceName+'\MSSQLServer\SuperSocketNetLib\TCP\'
END
ELSE
BEGIN
SET @RegKey='SOFTWARE\Microsoft\Microsoft SQL Server\'+@InstanceName+'\MSSQLServer\SuperSocketNetLib\TCP\'
END
END
EXECUTE xp_regread
  @rootkey = 'HKEY_LOCAL_MACHINE',
  @key = @RegKey,
  @value_name = 'TcpPort',
  @value = @value OUTPUT
IF (@value IS NULL)
BEGIN
EXECUTE xp_regread
  @rootkey = 'HKEY_LOCAL_MACHINE',
  @key = @RegKey,
  @value_name = 'TcpDynamicPorts',
  @value = @value OUTPUT
END
SELECT
@InstanceName AS InstanceName,
RTRIM(CONVERT(Char(128), SERVERPROPERTY('Edition'))) AS Edition,
RTRIM(CONVERT(Char(128), SERVERPROPERTY('LicenseType'))) AS LicenseType,
RTRIM(CONVERT(Int, SERVERPROPERTY('NumLicenses'))) AS NumLicenses,
RTRIM(CONVERT(Int, SERVERPROPERTY('ProcessID'))) AS ProcessID,
RTRIM(CONVERT(Char(128), SERVERPROPERTY('ProductVersion'))) AS ProductVersion,
RTRIM(CONVERT(Char(128), SERVERPROPERTY('ProductLevel'))) AS ProductLevel,
RTRIM((CASE WHEN SERVERPROPERTY('isClustered') = 1 THEN 'isClustered ' ELSE '' END) + (CASE WHEN SERVERPROPERTY('IsFullTextInstalled') = 1 THEN 'IsFullTextInstalled ' ELSE '' END) + (CASE WHEN SERVERPROPERTY('IsIntegratedSecurityOnly') = 1 THEN 'IsIntegratedSecurityOnly ' ELSE '' END) + (CASE WHEN SERVERPROPERTY('IsSingleUser') = 1 THEN 'IsSingleUser ' ELSE '' END)) AS dbsiproperties,
CONVERT(Int, isnull(@value, 1433)) as PortNumber,
@@version AS Version"""

class MsSqlDatabaseMap(ZenPackPersistence, SQLPlugin):

    ZENPACKID = 'ZenPacks.community.MsSQLMon'

    maptype = "DatabaseMap"
    compname = "os"
    relname = "softwaredbsrvinstances"
    modname = "ZenPacks.community.MsSQLMon.MsSqlSrvInst"
    deviceProperties = SQLPlugin.deviceProperties + ('zWinUser',
                                                    'zWinPassword',
                                                    'zMsSqlConnectionString',
                                                    'zMsSqlSrvInstances',
                                                    )


    def queries(self, device):
        tasks = {}
        connectionString = getattr(device, 'zMsSqlConnectionString',
            "'pyisqldb',DRIVER='{FreeTDS}',ansi=True,TDS_Version='8.0',SERVER='${here/manageIp}',DATABASE='master',UID='${here/zWinUser}',PWD='${here/zWinPassword}'")
        instances = getattr(device, 'zMsSqlSrvInstances', '') or ''
        if type(instances) is str:
            instances = [instances]
        for inst in instances:
            inst = inst.strip()
            if inst and not inst.isdigit():
                setattr(device, 'manageIp', '%s\%s'%(device.manageIp, inst))
                inst = '1433'
            setattr(device, 'port', inst or '1433')
            cs = self.prepareCS(device, connectionString)
            tasks['si_%s'%inst] = (
                QUERYINST,
                None,
                cs,
                {
                    'InstanceName':'dbsiname',
                    'Edition':'edition',
                    'LicenseType':'licenseType',
                    'NumLicenses':'numLicenses',
                    'ProcessID':'processID',
                    'ProductVersion':'productVersion',
                    'ProductLevel':'productLevel',
                    'Version':'setProductKey',
                    'dbsiproperties':'dbsiproperties',
                    'PortNumber':'port',
                })
            tasks['db_%s'%inst] = (
                "sp_helpdb",
                None,
                cs,
                {
                    'name':'dbname',
                    'db_size':'totalBlocks',
                    'owner':'contact',
                    'dbid':'dbid',
                    'created':'activeTime',
                    'status':'_status',
                    'compatibility_level':'type',
                })
        return tasks

    def process(self, device, results, log):
        log.info('processing %s for device %s', self.name(), device.id)
        types = {1: 'SQL Server',
                60: 'SQL Server 6.0',
                65: 'SQL Server 6.5',
                70: 'SQL Server 7.0',
                80: 'SQL Server 2000',
                90: 'SQL Server 2005',
                100: 'SQL Server 2008',
                }

        maps = [self.relMap()]
        databases = []
        instances = set([k[3:] for k in results.keys()])
        for instname in instances:
            dbs = results.get('db_%s'%instname, None)
            if not dbs: continue
            try:
                inst = results['si_%s'%instname][0]
                om = self.objectMap(inst)
            except:
                databases.extend(dbs)
                continue
            if not om.dbsiname:
                om.dbsiname = instname or 'MSSQLSERVER'
            om.dbsiname = om.dbsiname.strip()
            om.id = self.prepId(om.dbsiname)
            om.dbsiproperties = om.dbsiproperties.split()
            pn, arch = om.setProductKey.split(' - ', 1)
            arch = arch.__contains__('(X64)') and '(64-Bit) ' or ''
            pn = '%s %s(%s)' % (pn, arch, om.dbsiname)
            om.setProductKey = MultiArgs(pn, 'Microsoft')
            maps[-1].append(om)
            for db in dbs:
                db['setDBSrvInst'] = om.dbsiname
                databases.append(db)
        self.relname = "softwaredatabases"
        self.modname = "ZenPacks.community.MsSQLMon.MsSqlDatabase"
        maps.append(self.relMap())
        if not databases: return maps
        for database in databases:
            try:
                om = self.objectMap(database)
                om.dbproperties = []
                for dbprop in (database.pop('_status', '') or '').split(', '):
                    try:
                        var, val = dbprop.split('=')
                        if var == 'Status': continue
                        setattr(om, var.lower(), val)
                    except: om.dbproperties.append(dbprop)
                if not hasattr(om, 'setDBSrvInst'):
                    om.id = self.prepId(om.dbname)
                else:
                    om.id = self.prepId('%s_%s'%(om.setDBSrvInst, om.dbname))
                om.activeTime = str(om.activeTime)
                om.type = types.get(getattr(om, 'type' , 1), types[1])
                om.blockSize = 8192
                om.totalBlocks=long(round(float(om.totalBlocks.split()[0])*128))
            except AttributeError:
                continue
            maps[-1].append(om)
        return maps
