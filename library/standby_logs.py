#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: standby_logs

short_description: module for altering a cdb

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    threads:
        description: number of threads needed
    groups:
        description: number of groups needed per thread
    size:
        description: size in gb

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
standby_logs:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_1
    dbname: datw1c
    threads: 8
    groups: 5
    size: 2
'''


from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_common as oc

def threads_exist(conn):
    cursor = conn.cursor()
    cursor.execute("select count(*) from v$standby_log")
    res = cursor.fetchone()
    cursor.close()
    return res[0] > 0

def create_standby_logs(conn,threads,groups,size):
    groupClause = ",".join([ f'size {size}g' for x in range(groups)])
    cursor = conn.cursor()
    for f in range(1,threads + 1):
        cursor.execute(f'alter database add standby logfile thread {f} ' + groupClause)
    cursor.close()

def datac1_logs_exist(conn):
    cursor = conn.cursor()
    cursor.execute("select count(*) from v$logfile where type = 'STANDBY' and member like '+DATAC%'")
    res = cursor.fetchone()
    cursor.close()
    return res[0] > 0


def drop_datac1_logs(conn):
    sql = """select member
    from v$logfile
    where type = 'STANDBY'
    and member like '+DATAC%'"""

    cursor = conn.cursor()
    cursor.execute(sql)
    res = cursor.fetchall()
    for l in res:
        lfile = l[0]
        cursor.execute(f"alter database drop standby logfile member '{lfile}'")
    cursor.close()

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,threads=dict(type='int',required=True)
            ,groups=dict(type='int',required=True)
            ,size=dict(type='int',required=True)
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
    threads = module.params['threads']
    groups = module.params['groups']
    size = module.params['size']

    oc.set_env(oracleHome,dbname)

    sysConn = oc.connect_sys()

    if not threads_exist(sysConn):
        result['changed'] = True
        if module.check_mode:
            sysConn.close()
            module.exit_json(**result)
        create_standby_logs(sysConn,threads,groups,size)
    if datac1_logs_exist(sysConn):
        result['changed'] = True
        if module.check_mode:
            sysConn.close()
            module.exit_json(**result)
        drop_datac1_logs(sysConn)


    sysConn.close()

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
