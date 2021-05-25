
Code
- DB Operations: ExaCC Backups / Backup Destinations
- Final Organization

Error Handling
- Checking to see if the resource has already been created
- Checking to see if related resources exist / are able to be updated currently
    - if in updating, can we create a while loop with a sleep to check lifecycle status and then automatically run the next 
    operation when resolved?
- Figure out WHERE error handling should occur - should it happen in the task files in case we run them individually 
or should they be in main.yml to make sure code is not repeated?

Testing
- ExaCS creation
- ExaCC creation
- ExaCC backups
- Code Organization / calling items individually 

Deployment - Ansible Operation 
- Ansible bastion
- Ansible tower based
- Ansible with CI/CD

