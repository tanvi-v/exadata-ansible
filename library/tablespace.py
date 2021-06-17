#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: tablespace

short_description: create a tablespace

options:
    oracle_home:
            description: ORACLE_HOME to use for this database
    dbname:
        description: DB_UNIQUE_NAME
    pdbname:
        description: name of the PDB
    tablespace_name:
        description: the tablespace name
    initial_size:
        description: initial size
        default: 1G
    next_size:
        description: autoextend increment 
        default: 1G
    max_size:
        description: max autoextend
        default: 32G
    default_tablespace:
        description: yes or no
        default: no
    encrypted:
        description: true or false
        default: false
    encryption_algorithm:
        description: AES256 for example
        default: AES256
    state:
        description: present
        default: present

author:
    - Andy Webster webster.andrew@heb.com
'''

EXAMPLES = r'''
#create an encrypted tablespace
tablespace:
    dbname: datw1c
    pdbname: pdb1
    tablespace_name: data
    initial_size: 1G
    next_size: 1G
    max_size: 32G
    default_tablespace: yes
    encrypted: true
    encryption_algorithm: AES256
'''



import cx_Oracle
import platform
import os
from ansible.module_utils.basic import AnsibleModule
import ansible.module_utils.oracle_common as oc

def tablespace_exists(conn,tsname):
    cursor = conn.cursor()
    cursor.execute('select count(*) from dba_tablespaces where tablespace_name = :tsname',[tsname.upper()])
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 1

def create_encrypted_tablespace(conn,tsname,encryptionAlgorithm,initialSize,nextSize,maxSize):
    cursor = conn.cursor()
    cursor.execute(f'''
create bigfile tablespace {tsname} datafile size {initialSize} autoextend on next {nextSize} maxsize {maxSize}
encryption using '{encryptionAlgorithm}'
default storage(encrypt)''')
    cursor.close()

def create_tablespace(conn,tsname,initialSize,nextSize,maxSize):
    cursor = conn.cursor()
    cursor.execute(f'''
create bigfile tablespace {tsname} datafile size {initialSize} autoextend on next {nextSize} maxsize {maxSize}''')
    cursor.close()

def tablespace_default(conn,tsname):
    sql = """select count(*) from database_properties where 
    property_name = 'DEFAULT_PERMANENT_TABLESPACE'
    and property_value = :tsname"""
    cursor = conn.cursor()
    cursor.execute(sql,[tsname.upper()])
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 1

def make_default(conn,tsname):
    sql = f'alter pluggable database default tablespace {tsname}'
    cursor = conn.cursor()
    cursor.execute(sql)
    cursor.close()

def is_temp(conn,tsname):
    cursor = conn.cursor()
    cursor.execute("select contents from dba_tablespaces where tablespace_name = :tsname",[tsname.upper()])
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 'TEMPORARY'

def check_size(conn,tsname,initialSize,nextSize,maxSize):
    tempSQL = """select t.bytes,t.increment_by * ts.block_size,t.maxbytes,t.autoextensible from dba_temp_files t,dba_tablespaces ts
where t.tablespace_name = ts.tablespace_name
and ts.tablespace_name = :tsname"""

    dataSQL = """select t.bytes,t.increment_by * ts.block_size,t.maxbytes,t.autoextensible from dba_data_files t,dba_tablespaces ts
where t.tablespace_name = ts.tablespace_name
and ts.tablespace_name = :tsname"""
    
    if is_temp(conn,tsname):
        sql = tempSQL
    else:
        sql = dataSQL
    
    cursor = conn.cursor()
    cursor.execute(sql,[tsname.upper()])
    size,increment,dbMaxSize,autoExtend = cursor.fetchone()
    cursor.close()
    return nextSize == increment and dbMaxSize == maxSize and autoExtend == 'YES'

#take a size like 1G and convert it to bytes
def parseSize(module,size,pdbname,tablespace):
    if not size[-1].upper() == 'G':
        module.fail_json(msg=f'tablespace size needs to include G for gigabytes pdb {pdbname} tablespace {tablespace}')
    return int(size[0:-1]) * (1024 * 1048576)

def alter_size(conn,tsname,initialSize,nextSize,maxSize):
    cursor = conn.cursor()
    cursor.execute(f"alter tablespace {tsname} autoextend on next {nextSize} maxsize {maxSize}")
    cursor.close()

def run_module():
    module_args = dict(
            oracle_home=dict(type='str',required=True)
            ,dbname=dict(type='str',required=True)
            ,pdbname=dict(type='str',required=True)
            ,tablespace_name=dict(type='str',required=True)
            ,initial_size=dict(type='str',default='1G')
            ,next_size=dict(type='str',default='1G')
            ,max_size=dict(type='str',default='1G')
            ,default_tablespace=dict(type='bool',default=False)
            ,encrypted=dict(type='bool',default=False)
            ,encryption_algorithm=dict(type='str',default='AES256')
            ,state=dict(type='str',default='present')
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
    tsname = module.params['tablespace_name']
    initialSize = module.params['initial_size']
    nextSize = module.params['next_size']
    maxSize = module.params['max_size']
    defaultTablespace = module.params['default_tablespace']
    encrypted = module.params['encrypted']
    encryptionAlgorithm = module.params['encryption_algorithm']
    state = module.params['state']

    initialSize = parseSize(module,initialSize,pdbname,tsname)
    nextSize = parseSize(module,nextSize,pdbname,tsname)
    maxSize = parseSize(module,maxSize,pdbname,tsname)

    oc.set_env(oracleHome,dbname)

    sysConn = oc.connect_sys(pdbname)

    if state == 'present':
        if not tablespace_exists(sysConn,tsname):
            result['changed'] = True
            if module.check_mode:
                module.exit_json(**result)
            if encrypted:
                create_encrypted_tablespace(sysConn,tsname,encryptionAlgorithm,initialSize,nextSize,maxSize)
            else:
                create_tablespace(sysConn,tsname,initialSize,nextSize,maxSize)

        if not tablespace_default(sysConn,tsname) and defaultTablespace:
            result['changed'] = True
            if module.check_mode:
                module.exit_json(**result)
            make_default(sysConn,tsname)
        if not check_size(sysConn,tsname,initialSize,nextSize,maxSize):
            result['changed'] = True
            if module.check_mode:
                module.exit_json(**result)
            alter_size(sysConn,tsname,initialSize,nextSize,maxSize)

    sysConn.close()

    module.exit_json(**result)


def main():
    run_module()

if __name__ == '__main__':
    main()
