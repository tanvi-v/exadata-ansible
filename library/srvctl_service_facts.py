#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: srvctl_service_facts

short_description: get info about services

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    pdbname:
        description: list services for a pdb

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#list services for datw1_rw
srvctl_service_facts:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_3
    dbname: datw1c
    pdbname: pdb1
'''

RETURN = r'''
services
'''

import re
from ansible.module_utils.basic import AnsibleModule

def srvctl_status_service(module,oracleHome,dbname,pdbname):
    args = [f'{oracleHome}/bin/srvctl','status','service','-d',dbname,'-pdb',pdbname]
    rc,sout,serr = module.run_command(args,check_rc=True,environ_update=dict(ORACLE_HOME=oracleHome))
    lines = sout.split('\n')
    services = []
    for l in lines:
        m = re.match(r'^Service\s([a-zA-Z0-9._]+)\sis\s(\w+)',l)
        if m:
            sname,status = m.groups()
            if status == 'running':
                serviceStatus = 'started'
            else:
                serviceStatus = 'stopped'

            services.append(dict(name=sname,service_status=serviceStatus))

    return services

def run_module():
    module_args = dict(oracle_home=dict(type='str',required=True),dbname=dict(type='str',required=True),pdbname=dict(type='str'))

    module = AnsibleModule(
            argument_spec = module_args,
            supports_check_mode = True
            )

    result = dict(
            changed=False,
            services=[]
            )

    oracleHome = module.params['oracle_home']
    dbname = module.params['dbname']
    pdbname = module.params['pdbname']

    services = srvctl_status_service(module,oracleHome,dbname,pdbname)
    result['services'] = services

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
