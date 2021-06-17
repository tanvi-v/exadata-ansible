#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: init_param

short_description: module for setting parameters

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    param_name:
        description: parameter name
    param_value:
        description: parameter value
    spfile:
        description: spfile only or not

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#init_param
init_param:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_1
    dbname: datw1c
    param_name: cluster_database
    param_value: true
    spfile: true
'''


from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_common as oc

def is_set(conn,paramName,paramValue):
    cursor = conn.cursor()
    cursor.execute("select count(*) from v$parameter where name = :name and value = :value",[paramName,paramValue])
    res = cursor.fetchone()
    cursor.close()
    return res[0] == 1

def set_param(conn,paramName,paramValue,spfile):
    if spfile:
        scope = 'spfile'
    else:
        scope = 'both'
    sql = f"alter system set {paramName} = {paramValue} scope={scope}"
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
    except:
        raise Exception(f'exception when executing {sql}')
    cursor.close()

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,param_name=dict(type='str',required=True)
            ,param_value=dict(type='str',required=True)
            ,spfile=dict(type='bool',default=False)
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
    paramName = module.params['param_name']
    paramValue = module.params['param_value']
    spfile = module.params['spfile']

    oc.set_env(oracleHome,dbname)

    sysConn = oc.connect_sys()

    if is_set(sysConn,paramName,paramValue):
        sysConn.close()
        module.exit_json(**result)

    result['changed'] = True
    if module.check_mode:
        sysConn.close()
        module.exit_json(**result)
    set_param(sysConn,paramName,paramValue,spfile)

    sysConn.close()

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
