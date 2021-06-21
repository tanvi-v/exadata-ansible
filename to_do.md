
Organization/Ansible Best Practices
- All code should be validated to actually be idempotent
- Use Loop instead of with_*: https://docs.ansible.com/ansible/latest/user_guide/playbooks_loops.html#migrating-from-with-x-to-loop
- Common Variables
    - Variable overrides should be in ./inventory/group_vars/*.yml
- Do not use block!! Use include_tasks instead!!
- Avoid lineinfile!! 
- Single quotes on all parameters
- when should use when: > (strip of new lines and space)
- shell should use shell: |
- parameters should be alphabetical
- if a variable is being used in a when statement, should be testing to exist before used (item.changed is defined and item.changed is false)


- Should we be doing a lot of error handling?
- Figure out best practice for setting region variable (ie for dataguard since now working with two regions in one play)
- Figure out best practice for setting inventory 
    - export ANSIBLE_INVENTORY=/Users/tvaradha/OracleContent/OracleContent/Accounts/Fiserv/fiserv_playbook/inventory
    - ansible-playbook -i inventory add_pdb.yml

Code Development
- Dataguard
    - need to spin up ExaCS/ExaCC + database in standby region
- ExaCC Backups / Backup Destinations
- PDB (Python or ansible? How to run commands as Oracle user)
- Variables
    - make variable values easier, check with customer naming conventions
    - automatically save DB OCIDs to a file like we did for networking

Clean-Up
- Add More Comments
- Follow Style Guide: https://confluence.oraclecorp.com/confluence/display/CDO/Ansible+Guidelines

Testing
- ExaCS creation/termination
- ExaCC creation/termination
- ExaCC backups
- Code Organization / calling items individually 

Code organization
- Dataguard
    - Should remote peering be included with OG networking set-up or with enabling dataguard?
    - Which steps will be required when doing Exadata instead of a VM database?
- Do we want to further split up the DB role based on creation vs. operation?
- Where should error handling occur? Since task files might be run individually? or should they be in main.yml to make sure code is not repeated? --> look at flow. Will the task file ever be run individually? If not, then no need for error handling there. 
    - But might not need any error handling if ansible tower will automatically catch errors

Error Handling
- Change any error handling from "when" to assert statements
- Focus Error Checking on DB Operations, not creation since those will all run together
- Checking to see if related resources exist / are able to be updated currently 
    - Do we need to do this? Test with DB Home and Database creation
    - if in updating, can we create a while loop with a sleep to check lifecycle status and then automatically run the next 
    operation when resolved?
- Checking to see if the resource has already been created?


Deployment - Ansible Operation 
- Ansible bastion
- Ansible tower based
- Ansible with CI/CD


