#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: tde_cdb

short_description: enable tde for a cdb

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    state:
        description: present
    password:
        tde password

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
tde_cdb:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_3
    dbname: datw1c
    state: present
    password: secure_blobbb
'''



import cx_Oracle
import platform
import os
from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_common as oc

def tde_enabled(conn):
    sql = """select count(*) from v$encryption_wallet 
where status = 'OPEN' and con_id = 1
    """
    cursor = conn.cursor()
    cursor.execute(sql)
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 1

def enable_tde(conn,password):
    cursor = conn.cursor()
    cursor.execute("select value from v$parameter where name = 'wallet_root'")
    r = cursor.fetchone()
    walletLocation = r[0]
    cursor.execute(f'administer key management create keystore identified by "{password}"')
    cursor.execute(f"""administer key management create auto_login keystore
    from keystore '{walletLocation}/tde'
    identified by "{password}"
""")
    cursor.execute(f'administer key management set key force keystore identified by "{password}" with backup')
    cursor.close()

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,state=dict(type='str',default='present')
            ,password=dict(type='str',required=True,no_log=True)
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
    state = module.params['state']
    password = module.params['password']

    oc.set_env(oracleHome,dbname)

    sysConn = oc.connect_sys()

    if state == 'present':
        if tde_enabled(sysConn):
            sysConn.close()
            module.exit_json(**result)
        else:
            result['changed'] = True
            if module.check_mode:
                module.exit_json(**result)
            enable_tde(sysConn,password)

    sysConn.close()

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
