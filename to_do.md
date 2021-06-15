
Basic Ansible / OCI errors
- Figure out where region is currently being set automatically
- Figure out why iad services is failing in Phoenix region but not Ashburn (route table for private subnet)
- Figure out best practice for setting inventory 
    - export ANSIBLE_INVENTORY=/Users/tvaradha/OracleContent/OracleContent/Accounts/Fiserv/fiserv_playbook/inventory
- Figure out best practice for setting region in multi regional environment (ie for dataguard)
- Finalize what security list values should be!!! especially for private backup network, etc (right now just default but should probs be something else)

Code Development
- remaining Dataguard
    - need to spin up either VM Cluster or DB System in standby region
    - then enable dataguard
    - figure out how to organize code for this
- ExaCC Backups / Backup Destinations
- PDBs
- Variables
    - make variable values easier, check with customer naming conventions
    - automatically save DB OCIDs to a file like we did for networking!

Clean-Up
- Add More Comments
- Check consistancy: variable definition, names of tasks

Testing
- ExaCS creation/termination
- ExaCC creation/termination
- ExaCC backups
- Code Organization / calling items individually 



Code organization
- How should dataguard set-up work? Should Networking be included with OG networking set-up?
- Do we want to further split up the DB role based on creation vs. operation?
- Where should error handling occur? Since task files might be run individually? or should they be in main.yml to make sure code is not repeated? --> look at flow. Will the task file (especially the create ones really ever be run individually? If not, then no need for error handling there)

Error Handling
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


