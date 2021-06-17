#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: tde_pdb

short_description: enable tde for a pdb

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    pdbname:
        description: name of the PDB
    state:
        description: present
    password:
        tde password

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#drop pdb
tde_pdb:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_3
    dbname: datw1c
    pdbname: pdb1
    state: present
    password: secure_blobbb
'''



import cx_Oracle
import platform
import os
from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_common as oc

def tde_enabled(conn,pdbname):
    sql = """select count(*) from v$encryption_wallet 
where  status = 'OPEN' 
  and con_id = (select con_id from v$pdbs where name = :pdbname)
    """
    cursor = conn.cursor()
    cursor.execute(sql,[pdbname.upper()])
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 1

def enable_tde(pdbname,password):
    conn = oc.connect_sys()
    cursor = conn.cursor()
    cursor.execute(f'alter session set container = {pdbname}')
    cursor.execute(f'administer key management set key force keystore identified by "{password}" with backup')
    cursor.close()
    conn.close()

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,pdbname=dict(type='str',required=True)
            ,state=dict(type='str',)
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
    pdbname = module.params['pdbname']
    state = module.params['state']
    password = module.params['password']

    oc.set_env(oracleHome,dbname)

    sysConn = oc.connect_sys()

    if state == 'present':
        if tde_enabled(sysConn,pdbname):
            sysConn.close()
            module.exit_json(**result)
        else:
            result['changed'] = True
            if module.check_mode:
                module.exit_json(**result)
            enable_tde(pdbname,password)

    sysConn.close()

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
