#!/usr/bin/python
import ansible.module_utils.oracle_common as oc
import ansible.module_utils.oracle_srvctl_service as svc

def close_pdb(conn,pdbname):
    cursor = conn.cursor()
    cursor.execute(f"alter pluggable database {pdbname} close immediate instances=all")
    cursor.close()

def open_pdb(conn,pdbname):
    cursor = conn.cursor()
    cursor.execute(f"alter pluggable database {pdbname} open instances=all")
    cursor.close()

def drop_pdb(conn,pdbname):
    cursor = conn.cursor()
    cursor.execute(f"drop pluggable database {pdbname} including datafiles")
    cursor.close()

def pdb_exists(conn,pdbname):
    cursor = conn.cursor()
    cursor.execute("select count(*) from cdb_pdbs where pdb_name = :pdbname",[pdbname.upper()])
    r = cursor.fetchone()
    cursor.close()
    return r[0] == 1

def create_pdb(module,conn,pdbname,password):
    cursor = conn.cursor()
    try:
      sql = f'create pluggable database {pdbname} admin user oracle identified by "{password}"'
      cursor.execute(sql)
    except cx_Oracle.DatabaseError as e:
        eo, = e.args
        module.fail_json(msg=f"error creating pdb {pdbname} {eo.message}",sql=sql)

    cursor.execute(f'alter pluggable database {pdbname} open instances=all')
    cursor.execute(f'alter pluggable database {pdbname} save state instances=all')
    cursor.close()

def restart(module,oracleHome,dbname,pdbname):
    oc.set_env(oracleHome,dbname)
    conn = oc.connect_sys()
    svc.handle_pdb_services('stopped',module,oracleHome,dbname,pdbname)
    close_pdb(conn,pdbname)
    open_pdb(conn,pdbname)
    svc.handle_pdb_services('running',module,oracleHome,dbname,pdbname)
    conn.close()
