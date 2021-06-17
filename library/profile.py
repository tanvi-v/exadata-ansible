#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: profile

short_description: modify a database profile

options:
  oracle_home:
    description: ORACLE_HOME to use for this database
  dbname:
    description: DB_UNIQUE_NAME
  pdbname:
    description: pdbname, optional, if not included we operation on the cdb
  profile:
    description: the profile name
  resource_name:
    description: the resource name we are changing
  limit:
    description: the limit we are setting
  state:
    description: present
    default: present

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#modify the profile in cdb to set PASSWORD_LIFE_TIME to unlimited
profile:
  oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_3
  dbname: datw1c
  pdbname: pdb1
  profile: default
  resource_name: PASSWORD_LIFE_TIME
  limit: unlimited
'''


#import our custom libraries here
import ansible.module_utils.oracle_common as oc
import ansible.module_utils.oracle_profile as op

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,pdbname=dict(type='str',default=None)
            ,profile=dict(type='str',required=True)
            ,state=dict(type='str',default='present')
            ,resource_name=dict(type='str',required=True)
            ,limit=dict(type='str',required=True)
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
    profile = module.params['profile']
    state = module.params['state']
    resourceName = module.params['resource_name']
    limit = module.params['limit']

    oc.set_env(oracleHome,dbname)

    sysConn = oc.connect_sys(pdbname)

    if op.profile_setting_matches(sysConn,profile,resourceName,limit):
        sysConn.close()
        module.exit_json(**result)

    result['changed'] = True
    if module.check_mode:
        sysConn.close()
        module.exit_json(**result)

    op.modify_profile(sysConn,profile,resourceName,limit)
    sysConn.close()
    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
