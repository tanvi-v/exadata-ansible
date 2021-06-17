#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dg_tnsnames

short_description: make changes to tnsManager

options:
    oracle_home:
        description: ORACLE_HOME
    dbname:
        description: dbname
    dg_scans:
        description: list of scans

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#make changes to tnsnames.ora for tnsManager
dg_tnsnames:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_1
    dbname: paal2ca
    dg_scans: ['wpx4-scan','apx4-scan']
'''



import re
from ansible.module_utils.basic import AnsibleModule

def tns_entry_exists(oracleHome,dbname,sname):
    exa = sname[:1]
    bdbname = dbname[:-1]
    aliasName = f'{bdbname}{exa}'
    f = open(f'{oracleHome}/network/admin/tnsnames.ora','rt')
    for l in f:
        if re.match(f'{aliasName}\s*=',l):
            f.close()
            return True
    f.close()
    return False

def add_tns_entry(oracleHome,dbname,sname):
    exa = sname[:1]
    bdbname = dbname[:-1]
    aliasName = f'{bdbname}{exa}'
    entry = f"""{aliasName} =
  (DESCRIPTION=
    (ENABLE=BROKEN)
    (ADDRESS=(PROTOCOL=TCP)(HOST={sname})(PORT=1521))
    (CONNECT_DATA=
      (SERVICE_NAME={aliasName}.heb.com)
    )
  )"""
    f = open(f'{oracleHome}/network/admin/tnsnames.ora','at')
    f.write(f'{entry}\n\n')
    f.close()

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,dg_scans=dict(type='list',required=True)
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
    dgScans = module.params['dg_scans']

    for sname in dgScans:
        if not tns_entry_exists(oracleHome,dbname,sname):
            result['changed'] = True
            if module.check_mode:
                module.exit_json(**result)

            add_tns_entry(oracleHome,dbname,sname)

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
