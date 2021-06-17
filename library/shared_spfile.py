#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: shared_spfile

short_description: create an spfile in ASM

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    spfile:
        description: spfile name in ASM

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
shared_spfile:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_1
    dbname: datw1c
    spfile: +DATAC1/datw1c/spfiledatw1c.ora
'''


from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_common as oc
import cx_Oracle

def create_spfile(module,oracleHome,dbname,spfile):
    script = f"""connect / as sysdba
whenever sqlerror exit failure
create pfile='/tmp/init{dbname}.ora' from spfile;
create spfile='{spfile}' from pfile='/tmp/init{dbname}.ora';
exit
"""
    args = [f'{oracleHome}/bin/sqlplus','/nolog']
    rc,sout,serr = module.run_command(args,check_rc=False,data=script)
    if rc:
        module.fail_json(msg=sout)

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,spfile=dict(type='str',required=True)
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
    spfile = module.params['spfile']

    oc.set_env(oracleHome,dbname)

    create_spfile(module,oracleHome,dbname,spfile)
    result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
