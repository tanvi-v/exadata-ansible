#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dbv_heb

short_description: configure custom HEB DBV stuff at the pdb level

options:
    oracle_home:
        description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    pdbname:
        description: pdbname
    state:
        description: enabled
    password:
        description: sys password/c##dbvowner password
    working_dir:
        descriptiion: directory where we can copy files and work
    tablespace_name:
        descriptiion: tablespace for creating the objects

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#configure DBV in pdb1
dbv_heb:
    oracle_home: /u02/app/oracle/product/19.0.0.0/dbhome_3
    dbname: datw1c
    pdbname: pdb1
    state: enabled
    password: secure_blobbb
    tablespace_name: users
'''



import cx_Oracle
import platform
import os
from ansible.module_utils.basic import AnsibleModule


def local_objects_exist(conn):
    cursor = conn.cursor()
    cursor.execute("select count(*) from dba_objects where owner = 'ORACLE' and object_name = 'HEB_DBV' and object_type like 'PACK%' and status = 'VALID'")
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 2

def create_local_objects(module,oracleHome,pdbname,conn,result,tablespace):

    sqls = [f"alter user oracle quota unlimited on {tablespace}",
  f"""CREATE TABLE ORACLE.DBV_RULES 
   (	DBV_RULE_ID NUMBER,
    RULE_NAME VARCHAR2(90), 
	USERNAME VARCHAR2(30), 
	MACHINE VARCHAR2(64), 
	MODULE VARCHAR2(64) default '%',
	last_updated_ts date default sysdate,
	last_updated_by varchar2(30) default user
   ) tablespace {tablespace}""",
  f"ALTER TABLE ORACLE.DBV_RULES ADD CONSTRAINT DBV_RULES_UK1 UNIQUE (USERNAME, MACHINE, MODULE) using index tablespace {tablespace}",
  f"ALTER TABLE ORACLE.DBV_RULES ADD CONSTRAINT DBV_RULES_uk2 unique (RULE_NAME) using index tablespace {tablespace}",
  f"ALTER TABLE ORACLE.DBV_RULES ADD CONSTRAINT DBV_RULES_pk primary key (DBV_RULE_ID) using index tablespace {tablespace}",
  "GRANT UPDATE ON ORACLE.DBV_RULES TO C##DBVOWNER",
  "GRANT SELECT ON ORACLE.DBV_RULES TO C##DBVOWNER",
  "GRANT INSERT ON ORACLE.DBV_RULES TO C##DBVOWNER",
  "GRANT DELETE ON ORACLE.DBV_RULES TO C##DBVOWNER",
  f"""create table oracle.dbv_rule_log (
ts date,
error_code varchar2(10),
rule_match_count integer,
username varchar2(30),
machine varchar2(64),
module varchar2(65),
error_message varchar2(4000))
  tablespace {tablespace}
    partition by range (ts)
      interval (numtodsinterval(1,'DAY'))
        (partition p0 values less than (to_date('01-OCT-2017','DD-MON-YYYY')))""",
    "grant select on oracle.dbv_rule_log to c##dbvowner"]

    cursor = conn.cursor()
    for sql in sqls:
        try:
            cursor.execute(sql)
        except cx_Oracle.DatabaseError as e:
            eo, = e.args
            cursor.close()
            conn.close()
            module.fail_json(msg=f'failed when executing {sql} error {eo.message}')
    cursor.close()

    script = f"""
connect / as sysdba
alter session set container = {pdbname};
@heb_dbv.sql
@heb_dbv_body.sql
exit
"""
    args = [f'{oracleHome}/bin/sqlplus','/nolog']
    rc,sout,serr = module.run_command(args,check_rc=False,data=script,cwd='/heb/appl/oracle/sql')
    if not local_objects_exist(conn):
        conn.close()
        module.fail_json(msg=sout,**result)

def connect_rule(conn):
    sql = "select count(*) from DVSYS.DBA_DV_COMMAND_RULE where command = 'CONNECT' and rule_set_name = 'HEB Ruleset'"
    cursor = conn.cursor()
    cursor.execute(sql)
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 1

def configure_connect_rule(conn):
    rule = ["HEB_DBV","HEB_DBV.ISVALID('T','F')  = 'T'"]

    ruleSet = """ begin 
   DVSYS.DBMS_MACADM.CREATE_RULE_SET(rule_set_name => 'HEB Ruleset', description => 'This Ruleset uses a custom package for authorization', enabled => dbms_macutl.g_yes, eval_options => dbms_macutl.g_ruleset_eval_any, fail_message => '', fail_code => null,audit_options => dbms_macutl.g_ruleset_audit_fail, fail_options => 1,  handler_options => 0, handler => '',is_static => false); 
 END;"""

    addRule = """BEGIN
    DVSYS.DBMS_MACADM.ADD_RULE_TO_RULE_SET(rule_set_name => 'HEB Ruleset', rule_name => 'HEB_DBV', rule_order => '1', enabled => 'Y'); 
END;"""

    commandRule = """BEGIN
  DVSYS.DBMS_MACADM.CREATE_COMMAND_RULE(command => 'CONNECT',rule_set_name => 'HEB Ruleset',object_owner => '%', object_name => '%', enabled => 'Y');
END;"""
    cursor = conn.cursor()
    try:
        cursor.callproc('DVSYS.DBMS_MACADM.CREATE_RULE',rule)
    except cx_Oracle.DatabaseError as e:
        eo, = e.args
        if eo.code == 47320:
            pass #rule already exists

    try:
        cursor.execute(ruleSet)
    except cx_Oracle.DatabaseError as e2:
        eo, = e2.args
        if eo.code == 47340:
            pass #ruleset already exists

    try:
        cursor.execute(addRule)
    except cx_Oracle.DatabaseError as e3:
        eo, = e3.args
        if eo.code == 47360:
            pass #rule already added to ruleset
    cursor.execute(commandRule)
    cursor.close()

def connect():
    conn = cx_Oracle.Connection(mode=cx_Oracle.SYSDBA)
    return conn

def connect_dbv(password):
    conn = cx_Oracle.Connection('c##dbvowner',password)
    return conn

def set_env(oracleHome,dbname):
    os.environ['ORACLE_HOME'] = oracleHome
    hostname = platform.node().split('.')[0]
    os.environ['ORACLE_SID'] = dbname+hostname[-1]

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,pdbname=dict(type='str',required=True)
            ,state=dict(type='str',default='enabled')
            ,password=dict(type='str',required=True,no_log=True)
            ,tablespace_name=dict(type='str',required=True)
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
    password = module.params['password']
    tablespace = module.params['tablespace_name']

    set_env(oracleHome,dbname)

    sysConn = connect()
    cursor = sysConn.cursor()
    cursor.execute(f"alter session set container = {pdbname}")
    cursor.close()
    if not local_objects_exist(sysConn):
        result['changed'] = True
        if module.check_mode:
            sysConn.close()
            module.exit_json(**result)
        create_local_objects(module,oracleHome,pdbname,sysConn,result,tablespace)

    dbvConn = connect_dbv(password)
    cursor = dbvConn.cursor()
    cursor.execute(f"alter session set container = {pdbname}")
    cursor.close()
    if connect_rule(dbvConn):
        sysConn.close()
        dbvConn.close()
        module.exit_json(**result)

    result['changed'] = True
    if module.check_mode:
        sysConn.close()
        dbvConn.close()
        module.exit_json(**result)

    configure_connect_rule(dbvConn)

    dbvConn.close()
    sysConn.close()

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
