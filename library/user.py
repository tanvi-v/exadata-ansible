#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: user

short_description: manage users

options:
  oracle_home:
    description: ORACLE_HOME to use for this database
    required: true
  dbname:
    description: DB_UNIQUE_NAME
    required: true
  pdbname:
    description: pdbname
  username:
    description: the username
    required: true
  password:
    description: the password to set for this user
  sysdba:
    description: yes or no
    default: no
  state:
    choices:
        - present
        - absent
        - reset
        - lock

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#reset dbsnmp
user:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_3
    dbname: datw1c
    username: dbsnmp
    password: secure_blobbb
    state: reset
'''



from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_common as oc

def user_exists(conn,username):
    cursor = conn.cursor()
    cursor.execute('select count(*) from dba_users where username = :username',[username.upper()])
    res = cursor.fetchone()
    cursor.close()
    return res[0] == 1

def create_user(conn,username,password):
    sql = f'create user {username} identified by "{password}"'
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()

def is_sysdba(conn,username):
    cursor = conn.cursor()
    cursor.execute('select count(*) from v$pwfile_users where username = :username',[username.upper()])
    res = cursor.fetchone()
    cursor.close()
    return res[0] == 1

def grant_sysdba(conn,username):
    cursor = conn.cursor()
    cursor.execute(f'grant sysdba to {username} container=all')
    cursor.close()

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,pdbname=dict(type='str')
            ,username=dict(type='str',required=True)
            ,password=dict(type='str',required=True,no_log=True)
            ,sysdba=dict(type='bool',default=False)
            ,state=dict(type='str',default='present')
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
    username = module.params['username']
    password = module.params['password']
    sysdba = module.params['sysdba']
    state = module.params['state']

    oc.set_env(oracleHome,dbname)

    sysConn = oc.connect_sys(pdbname)

    if state == 'present':
        if not user_exists(sysConn,username):
            create_user(sysConn,username,password)
            result['changed'] = True
        if sysdba:
            if not is_sysdba(sysConn,username):
                grant_sysdba(sysConn,username)
                result['changed'] = True

    sysConn.close()

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
