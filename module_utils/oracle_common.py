#!/usr/bin/python


import cx_Oracle
import platform
import os
import re

def connect_sys(pdbname=None):
    conn = cx_Oracle.Connection(mode=cx_Oracle.SYSDBA)
    if pdbname:
        cursor = conn.cursor()
        cursor.execute(f'alter session set container = {pdbname}')
        cursor.close()
    return conn

def connect_dbv(password,pdbname=None):
    conn = cx_Oracle.Connection('c##dbvowner',password)
    if pdbname:
        cursor = conn.cursor()
        cursor.execute(f'alter session set container = {pdbname}')
        cursor.close()
    return conn

def set_env(oracleHome,dbname):
    os.environ['ORACLE_HOME'] = oracleHome
    hostname = platform.node().split('.')[0]
    os.environ['ORACLE_SID'] = dbname+hostname[-1]

def sqlplus(module,oracleHome,script,workingDir):
    args = [f'{oracleHome}/bin/sqlplus','/nolog']
    rc,sout,serr = module.run_command(args,check_rc=False,data=script,cwd=workingDir)
    return sout

def get_instances(module,oracleHome,dbname):
    args = [f'{oracleHome}/bin/srvctl','status','database','-d',dbname]
    rc,sout,serr = module.run_command(args,check_rc=True,environ_update=dict(ORACLE_HOME=oracleHome))
    lines = sout.split('\n')
    instances = []
    for l in lines:
        m = re.match(r'^Instance\s([a-zA-Z0-9]+)',l)
        if m:
            iname = m.group(1)
            instances.append(iname)
    if instances:
        return instances
    else:
        module.fail_json(msg=f'srvctl status database -d {dbname} did not return instances',lines=lines)

def test_account_password(username,password):
    ret = True
    try:
        conn = cx_Oracle.Connection(username,password)
        conn.close()
    except cx_Oracle.DatabaseError as e:
        eo, = e.args
        if eo.code == 1017:
            ret = False
    return ret

def change_password(conn,username,password):
    cursor = conn.cursor()
    cursor.execute(f'alter user {username} identified by {password}')
    cursor.close()

def get_roles(conn,username):
    cursor = conn.cursor()
    cursor.execute('select granted_role from dba_role_privs where grantee = :username',[username.upper()])
    res = cursor.fetchall()
    cursor.close()
    res = [r[0] for r in res]
    return res

def get_privs(conn,username):
    cursor = conn.cursor()
    cursor.execute('select privilege from dba_sys_privs where grantee = :username',[username.upper()])
    res = cursor.fetchall()
    cursor.close()
    res = [r[0] for r in res]
    return res

def connect(username,password,serviceName):
    conn = cx_Oracle.Connection(username,password,serviceName)
    return conn

