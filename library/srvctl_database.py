#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: srvctl_database

short_description: module to invoke srvctl database commands

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    state:
        description: stop, start, restart, status,pwfile
    pwfile:
        description: path to pwfile
    spfile:
        description: path to spfile
    instances:
        description: number of instances
    role:
        description: role of the database, ie. physical_standby

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#start datw1c database
srvctl_database:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_3
    dbname: datw1c
    state: start
'''

RETURN = r'''
message:
    description: returned by status and includes the output from srvctl status database
'''

from ansible.module_utils.basic import AnsibleModule
import platform

def srvctl_status_db(module,oracleHome,dbname):
    args = [f'{oracleHome}/bin/srvctl','status','database','-d',dbname]
    ret = module.run_command(args,check_rc=False,environ_update=dict(ORACLE_HOME=oracleHome))
    return ret[1]

def srvctl_stop_db(module,oracleHome,dbname):
    args = [f'{oracleHome}/bin/srvctl','stop','database','-d',dbname]
    rc,sout,serr = module.run_command(args,check_rc=False,environ_update=dict(ORACLE_HOME=oracleHome))
    if rc:
        if 'already stopped' not in sout:
            module.fail_json(msg=sout)
    else:
        return True

def srvctl_start_db(module,oracleHome,dbname):
    args = [f'{oracleHome}/bin/srvctl','start','database','-d',dbname]
    rc,sout,serr = module.run_command(args,check_rc=False,environ_update=dict(ORACLE_HOME=oracleHome))
    if rc:
        if 'already running' not in sout:
            module.fail_json(msg=sout)
    else:
        return True

def is_pwfile_set(module,oracleHome,dbname,pwfile):
    args = [f'{oracleHome}/bin/srvctl','config','database','-d',dbname]
    rc,sout,serr = module.run_command(args,check_rc=False,environ_update=dict(ORACLE_HOME=oracleHome))
    lines = sout.split('\n')
    for l in lines:
        if l.startswith('Password'):
            s = l.split(':')
            if len(s) != 2:
                return False
            p = s[1]
            p = p.strip()
            return p.upper() == pwfile.upper()
    else:
        module.fail_json(msg=serr)

def srvctl_pwfile(module,oracleHome,dbname,pwfile):
    args = [f'{oracleHome}/bin/srvctl','modify','database','-d',dbname,'-pwfile',pwfile]
    rc,sout,serr = module.run_command(args,check_rc=False,environ_update=dict(ORACLE_HOME=oracleHome))
    if rc:
        module.fail_json(msg=serr)

def srvctl_create_db(module,oracleHome,pwfile,spfile,dbname,role):
    if role.upper() == 'PHYSICAL_STANDBY':
        startOption = 'mount'
    else:
        startOption = 'open'
    args = [f'{oracleHome}/bin/srvctl','add','database'
            ,'-d',dbname
            ,'-pwfile',pwfile
            ,'-oraclehome',oracleHome
            ,'-spfile',spfile
            ,'-role',role
            ,'-dbname',dbname[:-1]
            ,'-startoption',startOption
            ,'-diskgroup','DATAC1,RECOC1']
    rc,sout,serr = module.run_command(args,check_rc=False,environ_update=dict(ORACLE_HOME=oracleHome))
    if rc:
        module.fail_json(msg=serr)

def srvctl_add_instances(module,oracleHome,dbname,instances):
    args = [f'{oracleHome}/bin/srvctl','add','instance'
            ,'-d',dbname
            ,'-instance','a'
            ,'-node','a']

    hostname = platform.node().split('.')[0]
    baseHost = hostname[:-1]
            
    for i in range(1,instances + 1):
        args[6] = f'{dbname}{i}'
        args[8] = f'{baseHost}{i}'
        rc,sout,serr = module.run_command(args,check_rc=False,environ_update=dict(ORACLE_HOME=oracleHome))
        if rc:
            module.fail_json(msg=serr)

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,state=dict(type='str',default='status')
            ,pwfile=dict(type='str')
            ,spfile=dict(type='str')
            ,instances=dict(type='int')
            ,role=dict(type='str')
            )

    module = AnsibleModule(
            argument_spec = module_args,
            supports_check_mode = False
            )

    result = dict(
            changed=False,
            message=''
            )

    oracleHome = module.params['oracle_home']
    dbname = module.params['dbname']
    state = module.params['state']
    pwfile = module.params['pwfile']
    spfile = module.params['spfile']
    instances = module.params['instances']
    role = module.params['role']


    if module.params['state'] == 'status':
        res = srvctl_status_db(module,module.params['oracle_home'],module.params['dbname'])
        result['message'] = res
    elif module.params['state'] == 'stop':
        res = srvctl_stop_db(module,module.params['oracle_home'],module.params['dbname'])
        result['changed'] = res
    elif module.params['state'] == 'start':
        res = srvctl_start_db(module,module.params['oracle_home'],module.params['dbname'])
        result['changed'] = res
    elif module.params['state'] == 'restart':
        res = srvctl_stop_db(module,module.params['oracle_home'],module.params['dbname'])
        res = srvctl_start_db(module,module.params['oracle_home'],module.params['dbname'])
        result['changed'] = True
    elif module.params['state'] == 'pwfile':
        if not is_pwfile_set(module
                ,module.params['oracle_home']
                ,module.params['dbname']
                ,module.params['pwfile']):

            srvctl_pwfile(module
                ,module.params['oracle_home']
                ,module.params['dbname']
                ,module.params['pwfile'])
            result['changed'] = True
    elif module.params['state'] == 'create':
        res = srvctl_status_db(module,oracleHome,dbname)
#database already registered with CRS
        if res.startswith('PRCR-1001'):
            module.exit_json(**result)

        result['changed'] = True
        if module.check_mode:
            module.exit_json(**result)
        srvctl_create_db(module,oracleHome,pwfile,spfile,dbname,role)
        srvctl_add_instances(module,oracleHome,dbname,instances)


    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
