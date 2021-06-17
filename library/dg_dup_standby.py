#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dg_dup_standby

short_description: dup primary from a backup to build the standby

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: db_name
    db_unique_name:
        description: db_unique_name
    backup_location:
        description: location of backup files
    init_location:
        description: location of init.ora

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
dg_init_params:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_1
    dbname: datw1c
'''


from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_common as oc
import cx_Oracle

def is_db_up():
    try:
        conn = oc.connect_sys()
        conn.close()
        dbup = True
    except cx_Oracle.DatabaseError as e:
        eo, = e.args
        if eo.code == 1034:
            dbup = False
        else:
            raise
    return dbup

def create_spfile(module,oracleHome,initFile):
    script = f"""whenever sqlerror exit failure
connect / as sysdba
create spfile from pfile='{initFile}';
exit
"""
    args = [f'{oracleHome}/bin/sqlplus','/nolog']
    rc,sout,serr = module.run_command(args,check_rc=False,data=script)
    if rc:
        module.fail_json(msg=sout)

def startup_nomount(module,oracleHome):
    script = f"""whenever sqlerror exit failure
connect / as sysdba
startup nomount
exit
"""
    args = [f'{oracleHome}/bin/sqlplus','/nolog']
    rc,sout,serr = module.run_command(args,check_rc=False,data=script)
    if rc:
        module.fail_json(msg=sout)

def rman_dup(module,oracleHome,dbname,backupLocation):
    script = f"""connect auxiliary /
duplicate database '{dbname}' for standby backup location '{backupLocation}' nofilenamecheck;
exit
"""
    args = [f'{oracleHome}/bin/rman']
    rc,sout,serr = module.run_command(args,check_rc=False,data=script)
    if rc:
        module.fail_json(msg=sout)
    

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,db_unique_name=dict(type='str',required=True)
            ,backup_location=dict(type='str',required=True)
            ,init_location=dict(type='str',required=True)
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
    dbUniqueName = module.params['db_unique_name']
    backupLocation = module.params['backup_location']
    initLocation = module.params['init_location']

    oc.set_env(oracleHome,dbUniqueName)

#if the database is up we want to bail so as not to overwrite it
    if is_db_up():
        module.exit_json(**result)

    sysConn = cx_Oracle.connect(mode = cx_Oracle.SYSDBA | cx_Oracle.PRELIM_AUTH)
            
    result['changed'] = True
    if module.check_mode:
        module.exit_json(**result)
    
    create_spfile(module,oracleHome,initLocation)
    startup_nomount(module,oracleHome)
    rman_dup(module,oracleHome,dbname,backupLocation)

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
