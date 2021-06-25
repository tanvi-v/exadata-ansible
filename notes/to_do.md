

Code Development
- Rewrite code to work with Customer Environment
    - AWX - Khushboo
    - use Bastion Servers for DBs (necessary DB configuration - PDBs)
    - OCI Infrastructure Discovery to fill in inventory file
- ExaCC - need to speak with Albert first!
    - ExaCC provisioning: Network config (VM Cluster network difference from ExaCS? Connect to customer network?)
    - ExaCC Recovery Appliance Backup Destination
- Additional Database Set-Up 
    - PDB: additional set-up steps, make method of setting up cleaner - Tanvi
    - Database: additional set-up steps
- Playbook to call FPP - check with Santosh
- DataGuard (low priority)
    - Change Remote Peering to Discovery Method
    - ExaCC/ExaCS Dataguard
- Try to remove "Blocks" when possible

Code Organization
- Dataguard: should remote peering be with initial network setup?
- Backup: Should exacc backup destination be with initial database creation or afterwards?

Testing To Do 
- DB Backup
    - Create Backup Destination
    - Add Recovery Appliance as Backup Destination to DB
- ExaCC
    - Exadata Set-Up
    - Create VM Cluster 
    - PDB
    - Teardown
- ExaCS
    - Exadata Set-Up
    - Create VM Cluster 
    - PDB
    - Teardown

Successfully Tested 
- DB Backup
    - Add NFS or Object Storage as Backup Destinations to DB
- ExaCC
    - Create DB Home
    - Create DB 
- ExaCS
    - Network Set-Up
    - Create DB Home
    - Create DB 

Ansible Best Practices / Clean-Up
- Add More Comments
- Follow Style Guide: https://confluence.oraclecorp.com/confluence/display/CDO/Ansible+Guidelines
- Figure out best practice for setting region variable (ie for dataguard since now working with two regions in one play)
- Figure out best practice for setting inventory 
    - export ANSIBLE_INVENTORY=/Users/tvaradha/OracleContent/OracleContent/Accounts/Fiserv/fiserv_playbook/inventory
    - ansible-playbook -i inventory add_pdb.yml
- All code should be validated to actually be idempotent
- Common Variables
    - Variable overrides should be in ./inventory/group_vars/*.yml
- Do not use block!! Use include_tasks instead!!
- Single quotes on all parameters
- when - should use when: > (strip of new lines and space)
- parameters should be alphabetical
- if a variable is being used in a when statement, should be testing to exist before used (item.changed is defined and item.changed is false)

Additional Items
- Dataguard: ExaCS/ExaCC specific dataguard: Need to change parameters and spin up Exadata in standby region
- Manual Backups: "Standalone DB Backups not permitted"
- Error Handling

Error Handling
- Focus Error Checking on DB Operations, not creation since those will all run together
- Checking to see if related resources exist / are able to be updated currently 
    - Do we need to do this? Test with DB Home and Database creation
    - if in updating, can we create a while loop with a sleep to check lifecycle status and then automatically run the next operation when resolved?
- Checking to see if the resource has already been created?
