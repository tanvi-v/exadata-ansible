#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: tnsmanager

short_description: make changes to tnsManager

options:
    manager_path:
        description: path to tnsManager files
    alias_name:
        description: alias name for tnsnames.ora
    host_list:
        description: list of hostnames, ie. scans
    port:
        description: the port
        default: 1521
    state:
        description: present
        default: present
    service_name:
        description: service name

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#make changes to tnsnames.ora for tnsManager
tnsmanager:
    manager_path: /appl/tnsmanager/tnsManager
    alias_name: datw1_rw
    host_list: wcx4-scan
    service_name: datw1_rw
'''



import re
from ansible.module_utils.basic import AnsibleModule

def tns_entry_exists(managerPath,aliasName):
    f = open(f'{managerPath}/tnsnames.ora','rt')
    for l in f:
        if re.match(f'{aliasName}\s*=',l):
            f.close()
            return True

    f.close()
    return False

def add_tns_entry(managerPath,aliasName,hostList,port,serviceName):
    if len(hostList) == 1:
        entry = f"""{aliasName} =
  (DESCRIPTION=
    (ENABLE=BROKEN)
    (ADDRESS=(PROTOCOL=TCP)(HOST={hostList[0]})(PORT={port}))
    (CONNECT_DATA=
      (SERVICE_NAME={serviceName})
    )
  )"""
    else:
        addressList = []
        for h in hostList:
            addressList.append(' ' * 7 + f'(ADDRESS=(PROTOCOL=TCP)(HOST={h})(PORT={port}))' + '\n')
        entry = f"""{aliasName} =
  (DESCRIPTION=
    (ENABLE=BROKEN)
    (FAILOVER=ON)
    (RETRY_COUNT=3)
    (ADDRESS_LIST=
{''.join(addressList)}    )
    (CONNECT_DATA=
      (SERVICE_NAME={serviceName})
    )
  )"""
    f = open(f'{managerPath}/tnsnames.ora','at')
    f.write(f'{entry}\n\n')
    f.close()

def reload(module,managerPath):
    args = [f'./tnsManager','reload']
    rc,sout,serr = module.run_command(args,check_rc=True,cwd=managerPath)

def run_module():
    module_args = dict(
            manager_path=dict(type='str',required=True)
            ,alias_name=dict(type='str',required=True)
            ,host_list=dict(type='list',required=True)
            ,port=dict(type='int',default=1521)
            ,state=dict(type='str',default='present')
            ,service_name=dict(type='str',required=True)
            )

    module = AnsibleModule(
            argument_spec = module_args,
            supports_check_mode = True
            )

    result = dict(
            changed=False
            )


    managerPath = module.params['manager_path']
    aliasName = module.params['alias_name']
    hostList = module.params['host_list']
    state = module.params['state']
    serviceName = module.params['service_name']
    port = module.params['port']

    if tns_entry_exists(managerPath,aliasName):
        module.exit_json(**result)

    result['changed'] = True
    if module.check_mode:
        module.exit_json(**result)

    add_tns_entry(managerPath,aliasName,hostList,port,serviceName)
    reload(module,managerPath)
    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
