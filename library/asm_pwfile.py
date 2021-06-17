#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: asm_pwfile

short_description: copy the pasword file to asm

options:
    src_file:
        description: source filename to copy
    tgt_file:
        description: file to copy to

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#copy password file to ASM
asm_pwfile:
    src_file: /u02/app/oracle/product/19.0.0.0/dbhome_1/dbs/orapwpatw1ca1
    tgt_file: +DATAC1/patw1ca/orapwpatw1ca
'''

RETURN = r'''
message:
    description: returned by status and includes the output from srvctl status database
'''

import os

def file_exists(module,fname):
    args = ['asmcmd','ls',fname]
    rc,sout,serr = module.run_command(args,check_rc=False)
    if rc:
        module.fail_json(msg=sout)

def set_env():
    f = open('/etc/oratab','rt')
    for l in f:
        if l.startswith('+'):
            sid,ohome,flag = l.split(':')
            break
    else:
        f.close()
        raise Exception('could not find +ASM entry in /etc/oratab')
    f.close()
    os.environ['ORACLE_SID'] = sid
    os.environ['ORACLE_HOME'] = ohome

def asm_file_exists(module,fname):
    ohome = os.environ['ORACLE_HOME']
    args = [f'{ohome}/bin/asmcmd','ls',fname]
    rc,sout,serr = module.run_command(args,check_rc=False)
    return rc == 0

def file_exists(module,fname):
    if fname.startswith('+'):
        return asm_file_exists(module,fname)
    else:
        return os.path.exists(fname)

def copy_file(module,src,tgt):
    ohome = os.environ['ORACLE_HOME']
    args = [f'{ohome}/bin/asmcmd','cp',src,tgt]
    rc,sout,serr = module.run_command(args,check_rc=False)
    if rc:
        module.fail_json(msg=serr)

from ansible.module_utils.basic import AnsibleModule

def run_module():
    module_args = dict(
            src_file=dict(type='str',required=True)
            ,tgt_file=dict(type='str',required=True))

    module = AnsibleModule(
            argument_spec = module_args,
            supports_check_mode = False
            )

    result = dict(
            changed=False,
            message=''
            )

    srcFile = module.params['src_file']
    tgtFile = module.params['tgt_file']

    set_env()

    if not file_exists(module,tgtFile):
        if module.check_mode:
            module.exit_json(**result)
        copy_file(module,srcFile,tgtFile)
        result['changed'] = True

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
