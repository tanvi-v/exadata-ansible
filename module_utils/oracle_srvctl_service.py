#!/usr/bin/python
import ansible.module_utils.oracle_common as oc
import re

def srvctl_status_service(module,oracleHome,dbname,pdbname):
    args = [f'{oracleHome}/bin/srvctl','status','service','-d',dbname,'-pdb',pdbname]
    rc,sout,serr = module.run_command(args,check_rc=True,environ_update=dict(ORACLE_HOME=oracleHome))
    lines = sout.split('\n')
    services = {}
    for l in lines:
        m = re.match(r'^Service\s([a-zA-Z0-9._]+)\sis\s(\w+)',l)
        if m:
            sname,status = m.groups()
            if status == 'running':
                serviceStatus = 'running'
            else:
                serviceStatus = 'stopped'

            services[sname] = serviceStatus

    return services

def srvctl_start_service(module,oracleHome,dbname,serviceName):
    args = [f'{oracleHome}/bin/srvctl','start','service','-d',dbname,'-s',serviceName]
    rc,sout,serr = module.run_command(args,check_rc=True,environ_update=dict(ORACLE_HOME=oracleHome))

def srvctl_stop_service(module,oracleHome,dbname,serviceName):
    args = [f'{oracleHome}/bin/srvctl','stop','service','-d',dbname,'-s',serviceName]
    rc,sout,serr = module.run_command(args,check_rc=True,environ_update=dict(ORACLE_HOME=oracleHome))

def srvctl_remove_service(module,oracleHome,dbname,serviceName):
    args = [f'{oracleHome}/bin/srvctl','remove','service','-d',dbname,'-s',serviceName]
    rc,sout,serr = module.run_command(args,check_rc=True,environ_update=dict(ORACLE_HOME=oracleHome))

def srvctl_create_service(module,oracleHome,dbname,pdbname,serviceName,dbSize):
    if dbSize == 'small':
        instances = [ f'{dbname}{x}' for x in range(1,5)]
    else:
        instances = [ f'{dbname}{x}' for x in range(5,9)]
    args = [f'{oracleHome}/bin/srvctl','add','service','-d',dbname,'-pdb',pdbname,'-s',serviceName
            ,'-preferred',','.join(instances)]
    rc,sout,serr = module.run_command(args,check_rc=True,environ_update=dict(ORACLE_HOME=oracleHome))

def handle_service(state,status,module,oracleHome,dbname,pdbname,serviceName,dbSize):
    changed = False
    if state == 'absent':
        if status == 'running':
            changed = True
            if module.check_mode:
                pass
            else:
                srvctl_stop_service(module,oracleHome,dbname,serviceName)
                srvctl_remove_service(module,oracleHome,dbname,serviceName)
        elif status == 'stopped':
            changed = True
            if module.check_mode:
                pass
            else:
                srvctl_remove_service(module,oracleHome,dbname,serviceName)
    elif state == 'present':
        if status == 'absent':
            changed = True
            if module.check_mode:
                pass
            else:
                srvctl_create_service(module,oracleHome,dbname,pdbname,serviceName,dbSize)
                srvctl_start_service(module,oracleHome,dbname,serviceName)
    elif state == 'standby':
        if status == 'absent':
            changed = True
            if module.check_mode:
                pass
            else:
                srvctl_create_service(module,oracleHome,dbname,pdbname,serviceName,dbSize)
    elif state == 'running':
        if status == 'absent':
            module.fail_json(msg=f'could not start service {serviceName}, it does not exist')
        elif status == 'stopped':
            changed = True
            if module.check_mode:
                pass
            else:
                srvctl_start_service(module,oracleHome,dbname,serviceName)
    elif state == 'stopped':
        if status == 'absent':
            module.fail_json(msg=f'could not stop service {serviceName}, it does not exist')
        elif status == 'running':
            changed = True
            if module.check_mode:
                pass
            else:
                srvctl_stop_service(module,oracleHome,dbname,serviceName)
    return changed

def handle_service_list(state,module,oracleHome,dbname,pdbname,dbSize,serviceList):
    services = srvctl_status_service(module,oracleHome,dbname,pdbname)
    changed = False
    for serviceName in serviceList:
        res = handle_service(state
          ,services.get(serviceName,'absent')
          ,module
          ,oracleHome
          ,dbname
          ,pdbname
          ,serviceName
          ,dbSize)
        if res:
            changed = True
    return changed


def handle_pdb_services(state
            ,module
            ,oracleHome
            ,dbname
            ,pdbname,dbSize='small'):
    changed = False
    services = srvctl_status_service(module,oracleHome,dbname,pdbname)
    for serviceName,status in services.items():
        if state == 'stopped':
            if status == 'running':
                changed = True
                if module.check_mode:
                    pass
                else:
                    srvctl_stop_service(module,oracleHome,dbname,serviceName)
        elif state == 'running':
            if status == 'stopped':
                changed = True
                if module.check_mode:
                    pass
                else:
                    srvctl_start_service(module,oracleHome,dbname,serviceName)
        elif state == 'absent':
            changed = True
            if module.check_mode:
                pass
            else:
                if status == 'running':
                    srvctl_stop_service(module,oracleHome,dbname,serviceName)
                srvctl_remove_service(module,oracleHome,dbname,serviceName)
    return changed
