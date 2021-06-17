#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dbv_cdb

short_description: configure DBV at the CDB level

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    state:
        description: enabled
    password:
        sys password/c##dbvowner password
    log_dir:
        place to write log files

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#configure DBV in datw1c
dbv_cdb:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_3
    dbname: datw1c
    state: enabled
    password: secure_blobbb
    log_dir = /u01/app/oracle/admin/datw1c/create
'''



import cx_Oracle
import platform
import os
from ansible.module_utils.basic import AnsibleModule

def is_ols_enabled(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM DBA_OLS_STATUS where name in ('OLS_CONFIGURE_STATUS','OLS_ENABLE_STATUS') and status = 'TRUE'")
    rows = cursor.fetchall()
    cursor.close()
    enabled_count = rows[0][0]
    return enabled_count == 2

def is_dbv_enabled(conn):
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM SYS.DBA_DV_STATUS where name in ('DV_CONFIGURE_STATUS','DV_ENABLE_STATUS') and status = 'TRUE'")
    rows = cursor.fetchall()
    cursor.close()
    enabled_count = rows[0][0]
    return enabled_count == 2

def create_dbvowner(conn,password):
    cursor = conn.cursor()
    try: 
        cursor.execute(f'CREATE USER c##dbvowner IDENTIFIED BY "{password}"')
    except cx_Oracle.DatabaseError as e:
        eo, = e.args
        if eo.code == 1920:
            pass #user already exists
        else:
            raise
    finally:
        cursor.close()

def configure_dbv(conn):
    cursor = conn.cursor()
    try:
        cursor.callproc('dvsys.configure_dv',['c##dbvowner','c##dbvowner'])
    except cx_Oracle.DatabaseError as e:
        eo, = e.args
        if eo.code == 47501:
            pass #dbv already configured
        else:
            raise
    finally:
        cursor.close()

def enable_dbv(dbvConn):
    cursor = dbvConn.cursor()
    cursor.callproc('dvsys.dbms_macadm.enable_dv')
    cursor.close()

def catcon_compile(module,oracleHome,password,logDir):
    catcon = f'/bin/env PATH={oracleHome}/bin:$PATH PERL5LIB={oracleHome}/rdbms/admin {oracleHome}/perl/bin/perl {oracleHome}/rdbms/admin/catcon.pl -n 1 -l {logDir} -b utlrp -U sys/{password} {oracleHome}/rdbms/admin/utlrp.sql\n'
    args = ['/bin/bash']
    rc,sout,serr = module.run_command(args,check_rc=True,data=catcon)

def do_dv_grants(dbvConn,sysConn):
#grants to run as c##dbvowner
    dbv_grants = [
            'grant dv_patch_admin to sys container=all'
            ,'grant dv_acctmgr to sys,system container=all'
            ,'grant dv_owner to sys container=all'
            ]
#grants to run as SYS
    sys_grants = [
            'grant dv_realm_owner to sys container=all'
            ,'grant dv_realm_resource to sys container=all'
            ,'grant administer key management to sys container=all'
            ,'grant select_catalog_role to C##DBVOWNER container = all'
            ,'grant become user to sys, system container = all'
            ]
    cursor = dbvConn.cursor()
    for g in dbv_grants:
        cursor.execute(g)
    cursor.close()
    cursor = sysConn.cursor()
    for g in sys_grants:
        cursor.execute(g)
    cursor.close()

def srvctl_stop_db(module,oracleHome,dbname):
    args = [f'{oracleHome}/bin/srvctl','stop','database','-d',dbname]
    rc,sout,serr = module.run_command(args,check_rc=False,environ_update=dict(ORACLE_HOME=oracleHome))
    if rc:
        if 'already stopped' not in sout:
            module.fail_json(msg=sout)
    else:
        return True

def srvctl_start_db(module,oracleHome,dbname):
    args = [f'{oracleHome}/bin/srvctl','start','database','-d',dbname]
    rc,sout,serr = module.run_command(args,check_rc=False,environ_update=dict(ORACLE_HOME=oracleHome))
    if rc:
        if 'already running' not in sout:
            module.fail_json(msg=sout)
    else:
        return True

def connect():
    conn = cx_Oracle.Connection(mode=cx_Oracle.SYSDBA)
    return conn

def connect_dbv(password):
    conn = cx_Oracle.Connection('c##dbvowner',password)
    return conn

def set_env(oracleHome,dbname):
    os.environ['ORACLE_HOME'] = oracleHome
    hostname = platform.node().split('.')[0]
    os.environ['ORACLE_SID'] = dbname+hostname[-1]

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,state=dict(type='str',default='enabled')
            ,password=dict(type='str',required=True,no_log=True)
            ,log_dir=dict(type='str',required=True)
            )

    module = AnsibleModule(
            argument_spec = module_args,
            supports_check_mode = True
            )

    result = dict(
            changed=False
            )


    oracleHome = module.params['oracle_home']
    dbname = module.params['dbname']
    password = module.params['password']
    logDir = module.params['log_dir']

    set_env(oracleHome,dbname)

    sysConn = connect()
    ols_enabled = is_ols_enabled(sysConn)
    dbv_enabled = is_dbv_enabled(sysConn)
    if ols_enabled and dbv_enabled:
        sysConn.close()
        module.exit_json(**result)

    result['changed'] = True
    if module.check_mode:
        sysConn.close()
        module.exit_json(**result)
    create_dbvowner(sysConn,password)
    configure_dbv(sysConn)
    dbvConn = connect_dbv(password)
    enable_dbv(dbvConn)
    catcon_compile(module,oracleHome,password,logDir)
    do_dv_grants(dbvConn,sysConn)
    dbvConn.close()
    sysConn.close()
    srvctl_stop_db(module,oracleHome,dbname)
    srvctl_start_db(module,oracleHome,dbname)

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
