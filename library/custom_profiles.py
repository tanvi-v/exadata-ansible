#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: custom_profiles

short_description: install HEB custom profiles

options:
  dbname:
    description: DB_UNIQUE_NAME
  pdbname:
    description: pdbname
  state:
    description: present
    default: present

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#make sure custom profiles are installed
custom_profiles:
  dbname: datw1c
  pdbname: pdb1
'''


#import our custom libraries here
import ansible.module_utils.oracle_common as oc
import os

from ansible.module_utils.basic import AnsibleModule

def verify_20c(conn):
    cursor = conn.cursor()
    cursor.execute("select count(*) from user_objects where object_name = 'VERIFY_FUNCTION_20C'")
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 1

def verify_8c(conn):
    cursor = conn.cursor()
    cursor.execute("select count(*) from user_objects where object_name = 'VERIFY_FUNCTION_8C'")
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 1

def setup_heb_profiles(conn):
    cursor = conn.cursor()
    cursor.execute("select count(distinct profile) from dba_profiles where profile in ('HEB_SEC_APP_USERS','HEB_SEC_END_USERS')")
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 2

def run_module():
    module_args = dict(oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,pdbname=dict(type='str',default=None)
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
    state = module.params['state']

    oc.set_env(oracleHome,dbname)
    oracleHome = os.environ['ORACLE_HOME']

    lines = []
    sysConn = oc.connect_sys(pdbname)

    if not verify_20c(sysConn):
        lines.append('@1_verify_20c.sql')

    if not verify_8c(sysConn):
        lines.append('@2_verify_8c.sql')

    if not setup_heb_profiles(sysConn):
        lines.append('@3_setup_heb_profiles.sql')

    if len(lines) > 0:
        script = "\n".join(lines)
        cmd = f'''connect / as sysdba
alter session set container = {pdbname};
{script}
exit
'''
        sout = oc.sqlplus(module,oracleHome,cmd,'/heb/appl/oracle/sql')
    else:
        sysConn.close()
        module.exit_json(**result)



    result['changed'] = True
    if module.check_mode:
        sysConn.close()
        module.exit_json(**result)

    sysConn.close()
    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
