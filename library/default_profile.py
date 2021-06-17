#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: default_profile

short_description: modify default profile

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    state:
        description: changed

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#modify default profile in datw1c
default_profile:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_3
    dbname: datw1c
    state: changed
'''



import cx_Oracle
import platform
import os
from ansible.module_utils.basic import AnsibleModule

def is_profile_changed(conn):
    cursor = conn.cursor()
    cursor.execute("select resource_name,limit from dba_profiles where profile = 'DEFAULT' and resource_name in ('PASSWORD_LIFE_TIME','PASSWORD_LOCK_TIME')")
    rows = cursor.fetchall()
    cursor.close()
    pvals = dict(rows)
    pvals['PASSWORD_LOCK_TIME'] = float(pvals['PASSWORD_LOCK_TIME'])
    if pvals['PASSWORD_LIFE_TIME'] == 'UNLIMITED' and pvals['PASSWORD_LOCK_TIME'] < 1:
        return True

def change_profile(conn):
    cursor = conn.cursor()
    cursor.execute("alter profile default limit PASSWORD_LIFE_TIME unlimited")
    cursor.execute("alter profile default limit PASSWORD_LOCK_TIME 15/1440")
    cursor.close()

def connect():
    conn = cx_Oracle.Connection(mode=cx_Oracle.SYSDBA)
    return conn

def set_env(oracleHome,dbname):
    os.environ['ORACLE_HOME'] = oracleHome
    hostname = platform.node().split('.')[0]
    os.environ['ORACLE_SID'] = dbname+hostname[-1]

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,state=dict(type='str',default='changed')
            )

    module = AnsibleModule(
            argument_spec = module_args,
            supports_check_mode = False
            )

    result = dict(
            changed=False
            )


    oracleHome = module.params['oracle_home']
    dbname = module.params['dbname']

    set_env(oracleHome,dbname)

    sysConn = connect()
    profile_changed = is_profile_changed(sysConn)
    if profile_changed:
        sysConn.close()
        module.exit_json(**result)

    result['changed'] = True
    change_profile(sysConn)
    sysConn.close()

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
