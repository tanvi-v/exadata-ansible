
Code Development
- Add ALL fields to oci modules and optional fields to Defaults
- ExaCC provisioning: Network config (VM Cluster network different than ExaCS)
- Make Networking Set-Up more dynamic
- PDB: pull oracle_sid automatically. Pick a different directory
- Playbook to call FPP - Depends on how FPP is set-up
- DataGuard (low priority) - ExaCC/ExaCS Dataguard

Ansible Best Practices / Clean-Up
- All code should be validated to actually be idempotent
- Define names better + add names to side tasks (asserts, debugs)
- Add More Comments
- Follow Style Guide: https://confluence.oraclecorp.com/confluence/display/CDO/Ansible+Guidelines
- Remove blocks when possible
- when - should use when: > (strip of new lines and space); if a variable is being used in a when statement, should be testing to exist before used (item.changed is defined and item.changed is false)
- Single quotes on all parameters
- Parameters should be alphabetical


Roles to clean (comments, names, alphabetical, single parameters)
- exacc_vm_cluster
- exacs_infra
- exacs_vm_cluster
- networking
- pdb