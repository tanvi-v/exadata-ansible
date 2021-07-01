
Code Development
- Region??
- PDB/DB Operations
    - Use Bastion Server to access DB (for PDB)
    - Set up group_vars/host variables for PDB
    - DB Set-Up: pip3 install pexpect
- ExaCC provisioning: Network config (VM Cluster network difference from ExaCS? Connect to customer network?)
- Additional Database/PDB Set-Up 
- Playbook to call FPP
- DataGuard (low priority) - ExaCC/ExaCS Dataguard

Santosh Questions
- FPP
- Bastion Servers
- Should region be a field?

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