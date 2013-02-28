################################################################################
#
# This program is part of the MsSQLMon Zenpack for Zenoss.
# Copyright (C) 2009-2013 Egor Puzanov.
#
# This program can be used under the GNU General Public License version 2
# You can find full information here: http://www.zenoss.com/oss
#
################################################################################

__doc__="""MsSqlDatabaseMap.py

MsSqlDatabaseMap maps the MS SQL Databases table to Database objects

$Id: MsSqlDatabaseMap.py,v 1.16 2013/02/28 21:20:26 egor Exp $"""

__version__ = "$Revision: 1.16 $"[11:-2]

from Products.ZenModel.ZenPackPersistence import ZenPackPersistence
from Products.DataCollector.plugins.DataMaps import MultiArgs
from ZenPacks.community.SQLDataSource.SQLPlugin import SQLPlugin
import re

DEFAULTCS = "'pyisqldb',DRIVER='{FreeTDS}',ansi=True,TDS_Version='8.0',SERVER='${here/manageIp}\${here/dbSrvInstName}',PORT=${here/port},DATABASE='master',UID='${here/zWinUser}',PWD='${here/zWinPassword}'"
QUERYINST = """SET NOCOUNT ON
DECLARE @InstanceName nvarchar(50)
DECLARE @value VARCHAR(100)
SET @InstanceName=RTRIM(CONVERT(nVARCHAR,isnull(SERVERPROPERTY('INSTANCENAME'),'MSSQLSERVER')))
SET @value = '%s'
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
QUERYREG = """DECLARE @RegKey nvarchar(500)
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
END"""

TYPES = {1: 'SQL Server',
        60: 'SQL Server 6.0',
        65: 'SQL Server 6.5',
        70: 'SQL Server 7.0',
        80: 'SQL Server 2000',
        90: 'SQL Server 2005',
        100: 'SQL Server 2008',
        }

STATES = {'ONLINE':0,
        'RESTORING':1,
        'RECOVERING':2,
        'RECOVERY PENDING':3,
        'SUSPECT':4,
        'EMERGENCY':5,
        'OFFLINE':6,
        }

class MsSqlDatabaseMap(ZenPackPersistence, SQLPlugin):

    ZENPACKID = 'ZenPacks.community.MsSQLMon'

    maptype = "DatabaseMap"
    compname = "os"
    relname = "softwaredatabases"
    modname = "ZenPacks.community.MsSQLMon.MsSqlDatabase"
    deviceProperties = SQLPlugin.deviceProperties + ('zWinUser',
                                                    'zWinPassword',
                                                    'zMsSqlConnectionString',
                                                    'zMsSqlSrvInstances',
                                                    )


    def queries(self, device):
        tasks = {}
        connectionString = getattr(device, 'zMsSqlConnectionString', DEFAULTCS)
        instances = getattr(device, 'zMsSqlSrvInstances', '') or ''
        if type(instances) is str:
            instances = [instances]
        for inst in instances:
            inst = str(inst).strip()
            if inst.isdigit():
                setattr(device, 'port', inst)
                setattr(device, 'dbSrvInstName', '')
            else:
                setattr(device, 'port', '1433')
                setattr(device, 'dbSrvInstName', inst)
            if not device.dbSrvInstName:
                cs = self.prepareCS(device,
                    connectionString.replace('\${here/dbSrvInstName}', ''))
                m = re.search("PORT\s?=\s?'?\"?(\d*)", cs, flags=re.I)
                if not m: m = re.search(":(\d*)", cs)
                query = QUERYINST%(m and m.group(1) or '1433')
            else:
                cs = self.prepareCS(device, connectionString)
                query = QUERYINST.replace("SET @value = '%s'", QUERYREG)
            tasks['si_%s'%inst] = (
                query,
                None,
                cs,
                {
                    'dbsiname':'InstanceName',
                    'edition':'Edition',
                    'licenseType':'LicenseType',
                    'numLicenses':'NumLicenses',
                    'processID':'ProcessID',
                    'productVersion':'ProductVersion',
                    'productLevel':'ProductLevel',
                    'setProductKey':'Version',
                    'dbsiproperties':'dbsiproperties',
                    'port':'PortNumber',
                })
            tasks['db_%s'%inst] = (
                "sp_helpdb",
                None,
                cs,
                {
                    'dbname':'name',
                    'totalBlocks':'db_size',
                    'contact':'owner',
                    'dbid':'dbid',
                    'activeTime':'created',
                    'status':'status',
                    'type':'compatibility_level',
                })
        return tasks

    def process(self, device, results, log):
        log.info('processing %s for device %s', self.name(), device.id)
        dbrm = self.relMap()
        irm = self.relMap()
        irm.relname = "softwaredbsrvinstances"
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
            om.modname = "ZenPacks.community.MsSQLMon.MsSqlSrvInst"
            if not om.dbsiname:
                om.dbsiname = instname or 'MSSQLSERVER'
            om.dbsiname = om.dbsiname.strip()
            om.id = self.prepId(om.dbsiname)
            om.processID = int(om.processID or 0)
            om.dbsiproperties = om.dbsiproperties.split()
            pn, arch = om.setProductKey.split(' - ', 1)
            arch = arch.__contains__('(X64)') and '(64-Bit) ' or ''
            pn = '%s %s(%s)' % (pn, arch, om.dbsiname)
            om.setProductKey = MultiArgs(pn, 'Microsoft')
            irm.append(om)
            for db in dbs:
                db['setDBSrvInst'] = om.dbsiname
                databases.append(db)
        for database in databases:
            try:
                om = self.objectMap(database)
                om.dbproperties = []
                for dbprop in (database.pop('status', '') or '').split(', '):
                    try:
                        var, val = dbprop.split('=')
                        setattr(om, var.lower(), val)
                    except: om.dbproperties.append(dbprop)
                om.status = STATES.get(getattr(om, 'status', ''), 6)
                if not hasattr(om, 'setDBSrvInst'):
                    om.id = self.prepId(om.dbname)
                else:
                    om.id = self.prepId('%s_%s'%(om.setDBSrvInst, om.dbname))
                om.dbid = int(om.dbid or 0)
                om.activeTime = str(om.activeTime)
            except Exception:
                continue
            om.blockSize = 8192
            try:
                om.type = TYPES.get(float(str(getattr(om,'type',1)))) or TYPES[1]
            except ValueError:
                om.type = TYPES[1]
            try:
                om.totalBlocks = long(round(float(str(getattr(om,
                                    'totalBlocks', 0) or 0).split()[0]) * 128))
            except ValueError:
                om.totalBlocks = 0
            dbrm.append(om)
        return [irm, dbrm]
