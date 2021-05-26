
Code
- DB Operations: ExaCC Backups / Backup Destinations
- Resource teardown
    - Networking Tear down (best way to pull all the components)
    - Calling the individual tasks in an intelligent way
- Variables
    - make variable values easier, check with customer naming conventions
- Add Comments
- Check consistancy: variable definition, names of tasks, error handling method / location

Code organization
- Do we want to further split up the DB role based on creation vs. operation?
- Where should error handling occur? Since task files might be run individually? or should they be in main.yml to make sure code is not repeated? --> look at flow. Will the task file (especially the create ones really ever be run individually? If not, then no need for error handling there)

Error Handling
- Focus Error Checking on DB Operations, not creation since those will all run together
- Checking to see if related resources exist / are able to be updated currently 
    - Do we need to do this? Test with DB Home and Database creation
    - if in updating, can we create a while loop with a sleep to check lifecycle status and then automatically run the next 
    operation when resolved?
- Checking to see if the resource has already been created?

Increase timeouts?

Testing
- ExaCS creation
- ExaCC creation
- ExaCC backups
- Code Organization / calling items individually 

Deployment - Ansible Operation 
- Ansible bastion
- Ansible tower based
- Ansible with CI/CD


