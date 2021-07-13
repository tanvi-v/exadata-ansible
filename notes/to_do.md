
Code Development
- Add Variables to default and add a comment showing required
- Add ALL fields to oci modules!! and then just use defaults!!!!!

- Make PDB without dbaascli --> DBCA or wait until July 15th for new Service
- ExaCC provisioning: Network config (VM Cluster network different than ExaCS)
- Additional Database/PDB Set-Up
- Playbook to call FPP --> Depends on how FPP is set-up
- DataGuard (low priority) - ExaCC/ExaCS Dataguard, change from single job to workflow, broken up

Ansible Best Practices / Clean-Up
- All code should be validated to actually be idempotent
- Define names better + add names to side tasks (asserts, debugs)
- Add More Comments
- Follow Style Guide: https://confluence.oraclecorp.com/confluence/display/CDO/Ansible+Guidelines
- Remove blocks when possible
- when - should use when: > (strip of new lines and space); if a variable is being used in a when statement, should be testing to exist before used (item.changed is defined and item.changed is false)
- Single quotes on all parameters
- Parameters should be alphabetical




PDB NOTES (SANTOSH)
(always assume need to reset everything for each shell command. Always use absolute paths!)

- name: Create PDB Using DBCA Silent Mode
    shell: " dbca -silent -createPluggableDatabase -sourceDB {{db_unique_name}} -pdbName {{new_pdb_name}} -createPDBFrom {{db_pdb_prefix}} -pdbAdminUserName pdbadmin -pdbAdminPassword {{db_pdb_admin_password}} -createUserTableSpace true"
    become: yes
    become_user: oracle
    become_method: sudo
    environment:
       ORACLE_HOME: "{{ oracle_home }}"
       PATH: "{{ ansible_env.PATH }}:{{ oracle_home }}/bin"
       TZ: "america/new_york"
    register: pdb_creation_output
    failed_when: pdb_creation_output.stdout.find('100% complete') == -1

- name: Set TDE Key for PDB
    shell: |
        . /home/oracle/{{db_unique_name}}.env
        cd {{ ansible_workdir }}
        {{ oracle_home }}/bin/sqlplus -s "/ as sysdba" @SetTDEforPDB.sql
    become: yes
    become_user: oracle
    become_method: sudo

ALTER SESSION SET CONTAINER = {{new_pdb_name}};
ADMINISTER KEY MANAGEMENT SET KEY FORCE KEYSTORE IDENTIFIED BY "{{db_pdb_admin_password}}" WITH BACKUP;
QUIT;

Creating this file every time run the pdb command! Want to make sure it always has the accurate information (for example, db_pdb_admin_password). Not an expansive operation so not an issue, better to safe
- name: Create Set TDE for PDB sql
    copy:
      dest: "{{ ansible_workdir }}/SetTDEforPDB.sql"
      content: |
        ALTER SESSION SET CONTAINER = {{new_pdb_name}};
        ADMINISTER KEY MANAGEMENT SET KEY FORCE KEYSTORE IDENTIFIED BY "{{db_pdb_admin_password}}" WITH BACKUP;
        QUIT;
    become: yes
    become_user: oracle
    become_method: sudo