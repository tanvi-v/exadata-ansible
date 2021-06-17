#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: rman_config

short_description:configure RMAN

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    service_name:
        description: name of the service
    db_size:
        description: large or small determines where the service runs
    env_type:
        description: DEV, CERT, or PROD
    rman_catalog:
        description: catalog service ie. pdba2_rw
    rman_password:
        description: catalog password
    password:
        description: SYS/SYSTEM/C##DBVOWNER password

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
rman_config:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_3
    dbname: datw1c
    db_size: small

'''

RETURN = r'''
nothing
'''

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_common as oc
import re

def is_primary(conn):
    cursor = conn.cursor()
    cursor.execute("select count(*) from v$database where database_role = 'PRIMARY'")
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 1

def oracle_exists(conn):
    cursor = conn.cursor()
    cursor.execute("select count(*) from dba_users where username = 'C##ORACLE'")
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 1

def create_oracle_user(module,oracleHome):
    script = """whenever sqlerror exit failure
connect / as sysdba
create user c##oracle identified externally
default tablespace sysaux
temporary tablespace temp;
grant create session to c##oracle container = all;
grant dba to c##oracle container = all;
exit
"""
    args = [f'{oracleHome}/bin/sqlplus','/nolog']
    rc,sout,serr = module.run_command(args,check_rc=False,data=script)
    if rc:
        module.fail_json(msg=sout)

def do_grants_exist(conn):
    sql = """select count(*)
from dba_role_privs
where grantee in ('SYS','SYSTEM')
and granted_role in ('DV_ACCTMGR','DV_PATCH_ADMIN')"""
    cursor = conn.cursor()
    cursor.execute(sql)
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 4

def do_grants(conn):
    cursor = conn.cursor()
    cursor.execute("grant dv_acctmgr, dv_patch_admin to sys, system container = all")
    cursor.close()

def is_bct_enabled(conn):
    cursor = conn.cursor()
    cursor.execute("select count(*) from v$block_change_tracking where status = 'ENABLED'")
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 1

def enable_bct(conn,dbname):
    cursor = conn.cursor()
    cursor.execute(f"alter database enable block change tracking using file '+recoc1/{dbname}/bct'")
    cursor.close()


def is_registered(module,oracleHome,rmanCatalog,rmanPassword):
    script = f"""connect target /
connect catalog rman/{rmanPassword}@{rmanCatalog}
show all;
exit
"""
    args = [f'{oracleHome}/bin/rman']
    rc,sout,serr = module.run_command(args,check_rc=False,data=script)
    if rc:
        if 'RMAN-20001' in sout:
            return False
        else:
          module.fail_json(msg=sout)
    return True

def register_catalog(module,oracleHome,rmanCatalog,rmanPassword):
    script = f"""connect target /
connect catalog rman/{rmanPassword}@{rmanCatalog}
register database;
exit
"""
    args = [f'{oracleHome}/bin/rman']
    rc,sout,serr = module.run_command(args,check_rc=False,data=script)
    if rc:
        module.fail_json(msg=sout)
 
def get_backup_loc(env,dbSize,dbname):
    if dbSize.upper() == 'LARGE':
        controller = 'c2'
    else:
        controller = 'c1'

    if env.upper() == 'PROD':
        BACKUP_LOC = f'/zfssa/backup-prod-{controller}/{dbname}'
    else:
        BACKUP_LOC = f'/zfssa/backup-cert-{controller}/{dbname}'
    return BACKUP_LOC


def get_desired_config(module,oracleHome,dbname,dbSize,env,backupLoc):
    if env.upper() == 'PROD':
        RETENTION_POLICY = 'RECOVERY WINDOW OF 31 DAYS'
    else:
        RETENTION_POLICY = 'RECOVERY WINDOW OF 7 DAYS'

    desiredConfig = [
f"CONFIGURE RETENTION POLICY TO {RETENTION_POLICY};"
,f"CONFIGURE BACKUP OPTIMIZATION ON;"
,f"CONFIGURE DEFAULT DEVICE TYPE TO DISK;"
,f"CONFIGURE CONTROLFILE AUTOBACKUP FORMAT FOR DEVICE TYPE DISK TO '{backupLoc}/%F';"
,f"CONFIGURE DEVICE TYPE DISK PARALLELISM 32 BACKUP TYPE TO COMPRESSED BACKUPSET;"
,f"CONFIGURE CHANNEL DEVICE TYPE DISK FORMAT '{backupLoc}/%d_%U';"
,f"CONFIGURE COMPRESSION ALGORITHM 'LOW' AS OF RELEASE 'DEFAULT' OPTIMIZE FOR LOAD TRUE;"
,f"CONFIGURE ARCHIVELOG DELETION POLICY TO BACKED UP 1 TIMES TO DISK;"
,f"CONFIGURE SNAPSHOT CONTROLFILE NAME TO '+RECOC1/{dbname}/snapcf_{dbname}.f';"
]
    return desiredConfig

def set_desired_config(module,oracleHome,config):
    script = "\n".join(config)
    script = "connect target /\n" + script + "\nexit\n"
    args = [f'{oracleHome}/bin/rman']
    rc,sout,serr = module.run_command(args,check_rc=False,data=script)
    if rc:
        module.fail_json(msg=sout)

def get_config(module,oracleHome):
    script = """connect target /
show all;
"""
    args = [f'{oracleHome}/bin/rman']
    rc,sout,serr = module.run_command(args,check_rc=False,data=script)
    lines = sout.split('\n')
    newLines = []
    for l in lines:
#zap multiple spaces
        nl = re.sub(r"\s+'"," '",l)
        newLines.append(nl)
    return newLines

def run_module():
    module_args = dict(oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,db_size=dict(type='str',default='small')
            ,env_type=dict(type='str')
            ,rman_catalog=dict(type='str')
            ,rman_password=dict(type='str',no_log=True)
            ,password=dict(type='str',no_log=True)
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
    dbSize = module.params['db_size']
    env = module.params['env_type']
    rmanPassword = module.params['rman_password']
    rmanCatalog = module.params['rman_catalog']
    password = module.params['password']

    oc.set_env(oracleHome,dbname)

    sysConn = oc.connect_sys()

    backupLoc = get_backup_loc(env,dbSize,dbname)

    config = get_config(module,oracleHome)
    desiredConfig = get_desired_config(module,oracleHome,dbname,dbSize,env,backupLoc)

    if is_primary(sysConn):

        if not is_registered(module,oracleHome,rmanCatalog,rmanPassword):
            result['changed'] = True
            if module.check_mode:
                sysConn.close()
                module.exit_json(**result)
            register_catalog(module,oracleHome,rmanCatalog,rmanPassword)

        if not is_bct_enabled(sysConn):
            result['changed'] = True
            if module.check_mode:
                sysConn.close()
                module.exit_json(**result)
            enable_bct(sysConn,dbname)

        if not do_grants_exist(sysConn):
            result['changed'] = True
            if module.check_mode:
                sysConn.close()
                module.exit_json(**result)
            dbvConn = oc.connect_dbv(password)
            do_grants(dbvConn)
            dbvConn.close()

        if not oracle_exists(sysConn):
            result['changed'] = True
            if module.check_mode:
                sysConn.close()
                module.exit_json(**result)
            create_oracle_user(module,oracleHome)

    #list for holding settings that need to change
    newSettings = []
    for l in desiredConfig:
        if l not in config:
            newSettings.append(l)
    if newSettings:
        result['changed'] = True
        if module.check_mode:
            sysConn.close()
            module.exit_json(**result)
        set_desired_config(module,oracleHome,newSettings)

    sysConn.close()
    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
