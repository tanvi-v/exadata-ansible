#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: goldengate_user

short_description: create the goldendate user c##ggadmin

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    state:
        description: present is the default
    password:
        sys password/c##dbvowner password

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#create c##ggadmin in datw1c
goldengate_user:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_3
    dbname: datw1c
    admin_password: secure_bllll
    password: secure_blobbb
'''

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_common as oc
import cx_Oracle

def user_exists(conn,username):
    cursor = conn.cursor()
    cursor.execute('select count(*) from dba_users where username = :username',[username])
    res = cursor.fetchone()
    cursor.close()
    return res[0] == 1

def create_user(conn,username,password):
    if user_exists(conn,username):
        return False
    sql = f'create user {username} identified by {password} default tablespace sysaux'
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()
    return True

def has_goldengate_privs(conn,username):
    cursor = conn.cursor()
    cursor.execute('select count(*) from dba_goldengate_privileges where username = :username',[username.upper()])
    res = cursor.fetchone()
    cursor.close()
    return res[0] == 1

def goldengate_auth(conn,username):
    if has_goldengate_privs(conn,username):
        return False
    sql = '''begin
  dbms_goldengate_auth.grant_admin_privilege(:username,container=>'all');
end;'''
    cursor = conn.cursor()
    cursor.execute(sql,[username])
    cursor.close()
    return True

def authorize_ddl(conn):
    ret = True
    sql = """begin 
  dbms_macadm.authorize_ddl('SYS', 'SYSTEM');
end;"""
    cursor = conn.cursor()
    try:
        cursor.execute(sql)
    except cx_Oracle.DatabaseError as e:
        eo, = e.args
        if eo.code == 47973:
            ret = False
        else:
            raise
    finally:
        cursor.close()
    return ret

def add_to_realm(conn,username):
    ret = True
    sql = """BEGIN
  DVSYS.DBMS_MACADM.ADD_AUTH_TO_REALM(realm_name => 'Oracle Default Component Protection Realm',grantee => :username ,auth_options => 1);
END;"""
    cursor = conn.cursor()
    try:
        cursor.execute(sql,[username])
    except cx_Oracle.DatabaseError as e:
        eo, = e.args
        if eo.code == 47260:
            ret = False
        else:
            raise
    finally:
        cursor.close()
    return ret

def do_grants(conn,username):
    roles = ['DV_GOLDENGATE_ADMIN','DV_GOLDENGATE_REDO_ACCESS','DV_XSTREAM_ADMIN','XDBADMIN','RESOURCE','DBA']
    privs = ['CREATE SESSION','ALTER SYSTEM','ALTER USER']
    grantedRoles = oc.get_roles(conn,username)
    grantedPrivs = oc.get_privs(conn,username)
    grantsTodo = []
    for r in roles:
        if r not in grantedRoles:
            grantsTodo.append(r)
    for p in privs:
        if p not in grantedPrivs:
            grantsTodo.append(p)
    cursor = conn.cursor()
    for g in grantsTodo:
        cursor.execute(f'grant {g} to {username} container=all')
    cursor.close()
    return len(grantsTodo) > 0

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,state=dict(type='str',default='present')
            ,admin_password=dict(type='str',required=True,no_log=True)
            ,password=dict(type='str',required=True,no_log=True)
            )

    module = AnsibleModule(
            argument_spec = module_args,
            supports_check_mode = False
            )

    result = dict(
            changed=False
            )


    oracleHome = module.params['oracle_home']
    dbname = module.params['dbname']
    state = module.params['state']
    password = module.params['password']
    adminPassword = module.params['admin_password']
    username = 'C##GGADMIN'

    oc.set_env(oracleHome,dbname)

    sysConn = oc.connect_sys()
    dbvConn = oc.connect_dbv(adminPassword)

    if state == 'present':
        if create_user(sysConn,username,password):
            result['changed'] = True
        if goldengate_auth(sysConn,username):
            result['changed'] = True
        if authorize_ddl(dbvConn):
            result['changed'] = True
        if add_to_realm(dbvConn,username):
            result['changed'] = True
        if do_grants(sysConn,username):
            result['changed'] = True
        if not oc.test_account_password(username,password):
            oc.change_password(sysConn,username,password)
            result['changed'] = True

    sysConn.close()
    dbvConn.close()

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
