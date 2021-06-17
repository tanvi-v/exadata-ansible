#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: cdb

short_description: module for altering a cdb

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    prop:
        description: force_logging

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#drop pdb
cdb:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_1
    dbname: datw1c
    prop: force_logging
'''


from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_common as oc
import cx_Oracle

def is_force_logging(conn):
    cursor = conn.cursor()
    cursor.execute("select count(*) from v$database where force_logging = 'YES'")
    res = cursor.fetchone()
    cursor.close()
    return res[0] == 1

def set_force_logging(conn):
    cursor = conn.cursor()
    cursor.execute('alter database force logging')
    cursor.close()

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


def shutdown_immediate(module,oracleHome):
    script = f"""connect / as sysdba
shutdown immediate;
exit
"""
    args = [f'{oracleHome}/bin/sqlplus','/nolog']
    rc,sout,serr = module.run_command(args,check_rc=False,data=script)
    if rc:
        module.fail_json(msg=sout)
    if is_db_up():
        module.fail_json(msg=sout)

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,prop=dict(type='str',required=True)
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
    prop = module.params['prop']

    oc.set_env(oracleHome,dbname)

    try:
        sysConn = oc.connect_sys()
        dbup = True
    except cx_Oracle.DatabaseError as e:
        eo, = e.args
        if eo.code == 1034:
            dbup = False
        else:
            raise
 
    if prop == 'force_logging':
        if not dbup:
            module.fail_json(msg='database is not running')
        if not is_force_logging(sysConn):
            result['changed'] = True
            if module.check_mode:
                sysConn.close()
                module.exit_json(**result)
            set_force_logging(sysConn)
            sysConn.close()
    elif prop == 'shutdown':
        if dbup:
            result['changed'] = True
            if module.check_mode:
                sysConn.close()
                module.exit_json(**result)
            sysConn.close()
            shutdown_immediate(module,oracleHome)


    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
