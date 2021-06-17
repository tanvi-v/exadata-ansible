#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: user_mgmt

short_description: to create database links in DBV database for user managment processes

options:
    service_name:
        description: service for connecting to pdb
    state:
        description: present is the default
    password:
        description: sys password/c##dbvowner password
    dbv_repo_password:
        description: password for the dbv repo
    dbv_repo:
        description: service name for dbv repo

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#create links for dmfact2_rw
user_mgmt:
    service_name: dmfact2_rw
    password: somethingsecure_password_fordmfact2_rw
    dbv_repo_password: somethingsecure_for_dbv_repo
    dbv_repo: pdbv1_rw
'''

from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_common as oc

def hebadmin_link_exists(conn,serviceName):
    link = f'HEBADMIN_{serviceName.upper()}'
    cursor = conn.cursor()
    cursor.execute("select count(*) from dba_db_links where owner = 'C##ORACLE' and db_link = :link",[link])
    res = cursor.fetchone()
    cursor.close()
    return res[0] == 1

def test_hebadmin_link(conn,serviceName):
    ret = False
    cursor = conn.cursor()
    rval = cursor.var(int)
    cursor.execute("""begin
  :ret := c##oracle.hebadmin.db_link_chk(:servicename);
end;""",[rval,serviceName])
    cursor.close()
    if rval.getvalue() == 0:
        ret = True
    return ret

def drop_hebadmin_link(conn,serviceName):
    cursor = conn.cursor()
    cursor.execute("""begin
  c##oracle.hebadmin.drop_db_link(:servicename);
end;""",[serviceName])
    cursor.close()

def create_hebadmin_link(conn,serviceName,password):
    if hebadmin_link_exists(conn,serviceName):
        if test_hebadmin_link(conn,serviceName):
            return False
        else:
            drop_hebadmin_link(conn,serviceName)
    cursor = conn.cursor()
    cursor.execute("""begin
  c##oracle.hebadmin.create_db_link(:servicename,:password);
end;""",[serviceName,password])
    cursor.close()
    return True

def dbvowner_link_exists(conn,serviceName):
    cursor = conn.cursor()
    cursor.execute("select count(*) from dba_db_links where owner = 'C##ORACLE' and db_link = :link",[serviceName.upper()])
    res = cursor.fetchone()
    cursor.close()
    return res[0] == 1

def test_dbvowner_link(conn,serviceName):
    cursor = conn.cursor()
    try:
        cursor.execute("""begin
  c##oracle.test_db_link(:servicename);
end;""",[serviceName])
        ret = True
    except:
        ret = False
    finally:
        cursor.close()
    return ret

def drop_dbvowner_link(conn,serviceName):
    cursor = conn.cursor()
    cursor.execute("""begin
  c##oracle.drop_db_link(:servicename);
end;""",[serviceName])
    cursor.close()

def create_dbvowner_link(conn,serviceName,password):
    if dbvowner_link_exists(conn,serviceName):
        if test_dbvowner_link(conn,serviceName):
            return False
        else:
            drop_dbvowner_link(conn,serviceName)
    cursor = conn.cursor()
    cursor.execute(r"""begin
  c##oracle.create_db_link(:servicename,:password);
end;""",[serviceName,password])
    cursor.close()
    return True

def run_module():
    module_args = dict(
            service_name=dict(type='str',required=True)
            ,state=dict(type='str',default='present')
            ,password=dict(type='str',required=True,no_log=True)
            ,dbv_repo_password=dict(type='str',required=True,no_log=True)
            ,dbv_repo=dict(type='str',required=True)
            )

    module = AnsibleModule(
            argument_spec = module_args,
            supports_check_mode = False
            )

    result = dict(
            changed=False
            )


    serviceName = module.params['service_name']
    state = module.params['state']
    password = module.params['password']
    repoPassword = module.params['dbv_repo_password']
    repo = module.params['dbv_repo']
    repoUser = 'SYSTEM'

    conn = oc.connect(repoUser,repoPassword,repo)

    if state == 'present':
        if create_hebadmin_link(conn,serviceName,password):
            result['changed'] = True
        if create_dbvowner_link(conn,serviceName,password):
            result['changed'] = True

    conn.close()

    module.exit_json(**result)

def main():
    run_module()

if __name__ == '__main__':
    main()
