#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: pdb

short_description: create/remove a pdb

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    pdbname:
        description: name of the PDB
    state:
        description: present, absent, restart
    password:
        sys password/c##dbvowner password

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#drop pdb
pdb:
    dbname: datw1c
    pdbname: pdb1
    state: absent
    password: secure_blobbb
'''



from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_pdb as pdb
import ansible.module_utils.oracle_common as oc

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,pdbname=dict(type='str',required=True)
            ,state=dict(type='str',default='present')
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
        if pdb.pdb_exists(sysConn,pdbname):
            sysConn.close()
            module.exit_json(**result)
        else:
            result['changed'] = True
            if module.check_mode:
                sysConn.close()
                module.exit_json(**result)
            pdb.create_pdb(module,sysConn,pdbname,password)

    elif state == 'absent':
        if not pdb.pdb_exists(sysConn,pdbname):
            sysConn.close()
            module.exit_json(**result)
        else:
            result['changed'] = True
            if module.check_mode:
                module.exit_json(**result)
            pdb.close_pdb(sysConn,pdbname)
            pdb.drop_pdb(sysConn,pdbname)

    elif state == 'restart':
        result['changed'] = True
        if module.check_mode:
            module.exit_json(**result)
        pdb.restart(module,oracleHome,dbname,pdbname)



    sysConn.close()

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
