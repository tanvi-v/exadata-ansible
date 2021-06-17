#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dbv_pdb

short_description: configure DBV at the PDB level

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    pdbname:
        description: pdbname
    state:
        description: enabled or disabled
    password:
        sys password/c##dbvowner password
    log_dir:
        place to write log files

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#configure DBV in pdb1
dbv_pdb:
    dbname: datw1c
    pdbname: pdb1
    state: enabled
    password: secure_blobbb
    log_dir = /u01/app/oracle/admin/datw1c/create
'''



from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_pdb as pdb
import ansible.module_utils.oracle_common as oc
import os

def get_dbv_status(conn):
    status = {}
    sql = """SELECT name,status FROM SYS.DBA_DV_STATUS where name in ('DV_CONFIGURE_STATUS','DV_ENABLE_STATUS')
union all
SELECT name,status FROM DBA_OLS_STATUS where name in ('OLS_CONFIGURE_STATUS','OLS_ENABLE_STATUS')"""
    cursor = conn.cursor()
    cursor.execute(sql)
    r = cursor.fetchall()
    cursor.close()
    for s in r:
        if s[1] == 'FALSE':
            status[s[0]] = False
        else:
            status[s[0]] = True
    return status


def configure_dbv(module,oracleHome,password,logDir,pdbname):
    conn = oc.connect_sys(pdbname)
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
        conn.close()
    catcon_compile(module,oracleHome,password,logDir,pdbname)


def enable_dbv(password,pdbname):
    dbvConn = oc.connect_dbv(password,pdbname)
    cursor = dbvConn.cursor()
    cursor.callproc('dvsys.dbms_macadm.enable_dv')
    cursor.close()
    dbvConn.close()

def disable_dbv(password,pdbname):
    dbvConn = oc.connect_dbv(password,pdbname)
    cursor = dbvConn.cursor()
    cursor.callproc('dvsys.dbms_macadm.disable_dv')
    cursor.close()
    dbvConn.close()

def catcon_compile(module,oracleHome,password,logDir,pdbname):
    catcon = f'/bin/env PATH={oracleHome}/bin:$PATH PERL5LIB={oracleHome}/rdbms/admin {oracleHome}/perl/bin/perl {oracleHome}/rdbms/admin/catcon.pl -c {pdbname} -n 1 -l {logDir} -b utlrp -U sys/{password} {oracleHome}/rdbms/admin/utlrp.sql\n'
    args = ['/bin/bash']
    rc,sout,serr = module.run_command(args,check_rc=True,data=catcon)

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,pdbname=dict(type='str',required=True)
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
    pdbname = module.params['pdbname']
    password = module.params['password']
    logDir = module.params['log_dir']
    state = module.params['state']

    oc.set_env(oracleHome,dbname)

    sysConn = oc.connect_sys(pdbname)
    status = get_dbv_status(sysConn)
    sysConn.close()
    restartPDB = False

    if state.upper() == 'ENABLED':
        if not status['DV_CONFIGURE_STATUS']:
            result['changed'] = True
            if module.check_mode:
                module.exit_json(**result)
            configure_dbv(module,oracleHome,password,logDir,pdbname)
            restartPDB = True
        if not status['DV_ENABLE_STATUS']:
            result['changed'] = True
            if module.check_mode:
                module.exit_json(**result)
            enable_dbv(password,pdbname)
            restartPDB = True
    else: #disabled
        if not status['DV_CONFIGURE_STATUS']:
            result['changed'] = True
            if module.check_mode:
                module.exit_json(**result)
            configure_dbv(module,oracleHome,password,logDir,pdbname)
            restartPDB = True
        if status['DV_ENABLE_STATUS']:
            result['changed'] = True
            if module.check_mode:
                module.exit_json(**result)
            disable_dbv(password,pdbname)
            restartPDB = True

    if restartPDB:
        pdb.restart(module,oracleHome,dbname,pdbname)

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
