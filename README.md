# Ansible for Exadata

This ansible project allows for Exadata Cloud@Customer and Exadata Cloud Service set-up. 

## Getting Started

### AWX Set-Up

1. Provision AWX on a Compute Instance

2. Create credentials
    - Github credentials
    - OCI credentials (New Credential Type)
    - SSH Keys (Machine) 

2. Set-Up Project
    - Set-up Organization (ansible galaxy)
    - Sync Git Repo
    - Set-up basic inventory
    - Run install_python_sdk.yml playbook

3. Set-Up Inventory
    - Sync Dynamic Inventory
    - Create Groups
    - Add ssh variables
    


## Using Ansible with AWX

### Running a Playbook
 
1. Create a Job Template

2. Define Variables
    - vars_file: File name for variables to be used for that playbook. Workload specfic. Be sure to edit these files to set variables such as workload_tag (used for naming resources) and database parameters. Path to the vars_file has already been included in the code, just have to provide the actual file name (ex: sample_exacs.yml). 
    - hostgroup: Host group to run DB operations on. Currently only required for PDB operations (other playbooks are for provisioning so use localhost).
    - additional variables: These variables are only defined at runtime, not stored in a file. Check out the Playbooks below for instructions on which plays require additional variables.

### Creating a Workflow

Creating a workflow instead of running an individual job allows you to automate a longer process. For example, linking together ExaCS Set-Up + DB Home Set-Up + Database Set-Up. These playbooks are individual since as a user, you might often want to set-up just a database on an existing home, but you might want to automate the initial creation.


## Ansible Codebase

This codebase contains a set of playbooks that can be used individually or combined into a workflow for ExaCS and ExaCC Set-up. Each playbook references ansible roles (an ansible file structure used to group reusable components). Each ansible role folder contains three subdirectories - tasks, defaults, and meta. 

- Tasks: Contains a main.yml file that will be automatically called if the role is invoked. Also contains reusable standalone tasks.
- Defaults: Default variable values for the tasks in that role. These variables have the least precedence and will be overrided by any variables defined in the included variable file (vars_file) or in the ansible job template. Many of these variables are set as null as they are optional variables for the oci tasks and it is your choice whether to define them. For required variables, check the comments on the sample vars_files or the oracle.oci ansible documentation. 
- Meta: Sets collection oracle.oci


### Playbooks

**awx_test.yml**
- Tests if your ansible environment has been set-up correctly. If running from localhost, pulls Network services information to check if your OCI credentials are working and pulls compartment information to check if your variable file was defined. If running from a host, runs a simple shell command to make sure the inventory has been set-up correctly.
- Job Template Variables
    - vars_file
    - hostgroup (localhost or the name of a group from your inventory)

**networking_setup.yml**
- Creates a network for Exadata Cloud Service environment by calling the networking role. Two options for primary ExaCS subnet: a public subnet for testing instances and a private subnet for production instances, defined by the variable prohibit_public_ip_on_vnic.
- Job Template Variables
    - vars_file

**networking_teardown.yml**
- Terminates a basic ExaCS network by calling the individual task networking_teardown from the networking role. Assumes that you used the networking role to set-up the environment.
- Job Template Variables
    - vars_file

**exacs_setup.yml**
- Creates an Exadata Cloud Service environment by spinning up the ExaCS Infrastructure and ExaCS VM Cluster. 
- Job Template Variables
    - vars_file
    - ssh_public_keys (for VM Cluster creation)

**exacc_setup.yml**
- Creates an Exadata Cloud at Customer environment by calling the Exadata VM Cluster role. Assumes that the Exadata Infrastructure has already been provisioned by Oracle.
- Job Template Variables
    - vars_file

**db_create.yml**
- Creates a new database. Assumes that the database home has already been created.
- Job Template Variables
    - vars_file
    - db_admin_password

**db_home_create.yml**
- Creates a new database home. Assumes that the VM cluster has already been created.
- Job Template Variables
    - vars_file

**db_teardown.yml**
- Terminates a database and the accompanying db home.
- Job Template Variables
    - vars_file

**db_backup.yml**
- Description
- Job Template Variables
    - vars_file

**pdb_create.yml**
- Creates a new pdb. Assumes that the database has already been created.
- Job Template Variables
    - vars_file
    - hostgroup
    - pdb_password

**pdb_delete.yml**
- Deletes the pdb. Assumes that the database has already been created.
- Job Template Variables
    - vars_file
    - hostgroup