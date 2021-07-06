
Code Development
- Bastion
    - Set up Bastion Server for ExaCC final and ExaCS testing
    - Consider using Bastion SERVICE instead?
- Set up group_vars for host based operations (such as PDB)... consider moving other variables to that location as well
- ExaCC provisioning: Network config (VM Cluster network different than ExaCS)
- Additional Database/PDB Set-Up
- Playbook to call FPP --> Depends on how FPP is set-up
- Make PDB without dbaascli --> DBCA
- DataGuard (low priority) - ExaCC/ExaCS Dataguard 
- Region??

Santosh Questions
- Using dynamic inventory: DB nodes??
- Should region be a field? Cross region operations?

Code Organization
- Dataguard: should remote peering be with initial network setup?
- Backup: Should exacc backup destination be with initial database creation or afterwards?

Ansible Best Practices / Clean-Up
- All code should be validated to actually be idempotent
- Add More Comments
- Follow Style Guide: https://confluence.oraclecorp.com/confluence/display/CDO/Ansible+Guidelines
- Should define names better + add names to assert/debug
- Remove blocks when possible
- when - should use when: > (strip of new lines and space)
- if a variable is being used in a when statement, should be testing to exist before used (item.changed is defined and item.changed is false)
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