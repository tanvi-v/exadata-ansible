#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: srvctl_service

short_description: manage services

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    pdbname:
        description: list services for a pdb

    service_name:
        description: name of the service
    db_size:
        description: large or small determines where the service runs

    state:
        choices:
            - present
            - absent
            - running
            - stopped
            - standby

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#remove a service
srvctl_service:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_3
    dbname: datw1c
    pdbname: pdb1
    service_name: datw1_rw
    state: absent

'''

RETURN = r'''
nothing
'''

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_common as oc
import ansible.module_utils.oracle_srvctl_service as svc 

def run_module():
    module_args = dict(oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,pdbname=dict(type='str')
            ,service_name=dict(type='list',default=[])
            ,state=dict(type='str',required=True)
            ,db_size=dict(type='str',default='small')
            )

    module = AnsibleModule(
            argument_spec = module_args,
            supports_check_mode = True
            )

    result = dict(
            changed=False,
            status=''
            )

    oracleHome = module.params['oracle_home']
    dbname = module.params['dbname']
    pdbname = module.params['pdbname']
    serviceList = module.params['service_name']
    state = module.params['state']
    dbSize = module.params['db_size']
    
    if len(serviceList) == 0:
        changed = svc.handle_pdb_services(state
          ,module
          ,oracleHome
          ,dbname
          ,pdbname
          ,dbSize)
        result['changed'] = changed
    else:
        changed = svc.handle_service_list(state,module,oracleHome,dbname,pdbname,dbSize,serviceList)
        result['changed'] = changed

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
