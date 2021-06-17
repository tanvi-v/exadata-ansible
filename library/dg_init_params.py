#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dg_init_params

short_description: set init params for data guard

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME

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

def is_params_set(conn):
    cursor = conn.cursor()
    cursor.execute("select count(distinct name) from v$spparameter where isspecified = 'TRUE' and name in ('db_file_name_convert','log_file_name_convert','standby_file_management','dg_broker_config_file1','dg_broker_config_file2','log_archive_min_succeed_dest','log_archive_trace')")
    res = cursor.fetchone()
    cursor.close()
    return res[0] == 7

def set_params(conn,dbname):
    tgt = dbname[-1]
    bdbname = dbname[:-1]
    if tgt == 'w':
        src = bdbname + 'a'
    elif tgt == 'a':
        src = bdbname + 'w'
    else:
        raise f'{dbname} should be in lowercase'
    cursor = conn.cursor()
    cursor.execute(f"alter system set db_file_name_convert = '/{src}/','/{dbname}/' scope=spfile")
    cursor.execute(f"alter system set log_file_name_convert = '/{src}/','/{dbname}/' scope=spfile")
    cursor.execute("alter system set standby_file_management = auto")
    cursor.execute(f"alter system set dg_broker_config_file1 = '+DATAC1/{dbname}/dr1{dbname}.dat'")
    cursor.execute(f"alter system set dg_broker_config_file2 = '+DATAC1/{dbname}/dr2{dbname}.dat'")
    cursor.execute(f"alter system set log_archive_min_succeed_dest = 1")
    cursor.execute(f"alter system set log_archive_trace = 0")
    cursor.close()

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
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

    oc.set_env(oracleHome,dbname)

    sysConn = oc.connect_sys()

    if not is_params_set(sysConn):
        result['changed'] = True
        if module.check_mode:
            sysConn.close()
            module.exit_json(**result)
        set_params(sysConn,dbname)

    sysConn.close()

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
