https://confluence.oraclecorp.com/confluence/display/CDO/Ansible+Guidelines

Inventory
- Maintain at least 2 inventory, each split to a singular purpose. e.g. Inventory 1 = OCI, Inventory 2 = Linux & Windows OS

AWX
- One thing you will need to consider: AWX requires that you use the 'OPC' user account as the service account for Ansible to make change. This means all servers must use a SINGLE SSH KEY.

Pulling Data
- When writing Ansible there are a few things you should think about that are very old styles of thinking that if applied, you will get some fun behaviors. Inventory abuse is one of them. When you name objects, consider what everyone, including OCI documentation) considers to be bad form, and put the object type in the name of the object. Then make that object name, your inventory item as well. Now with your playbook run, you can use the regex feature to match the variable inventory_hostname against your tasks. Side effect: Automatic parallelization of your workload. Data structures are simplified to be only for the single object. Now you can treat the contents of your playbook as if you are operating a state machine on that single object. Role order in your playbook becomes your dependency chain enforcement.
    - Every task bootstrap itself into discovery, determine if requirements exists, validate configuration is safe, and then and only then make the one change you need.
    - Take VCN Local Peering into account you would use the following logic:
        look for VCN A by Name, discover OCID
        look for VCN B by Name, discover OCID
        Look for VCN A LPG by Name, idempotent assert it will exists
        Likewise VCN B LPG
        Now link them.

Roles
- Every thing you want to do should be a role. Minimize the content you have in playbooks to point you just call roles.
- Think carefully about how you will support different OS Vendor/Version and Hardware (mostly because Exa can be problematic). I usually try to do OS Vendor/Version detection, then include code in a ./tasks/$vendor/$architecture/$version/main.yml sub directory of the role. Not all bits may be needed, but I did run into some issues trying to get code to work for OL6 ia32 vs OL7 x86_64 vs OL8 aarch64, and this will help you avoid pain at the expansion of some duplicate code. (e.g. OL6 is now EOL so should be less concern for most, but OL7 and OL8 are different enough you can run into some issues). We do this because many of our roles also cover both Linux & Windows.
- Current logical break up works, but don't be afraid to refactor. 
- Use role dependency to trigger requirements (also fine to use current method of include_role to use subtasks, there is a time and place for each method)
- Use handlers to your advantage, and localize them to the role. This way as you go from Role A to B to C, you can trigger fact gathering again so the next role has a current view (needed any time you do package or service status changes).
- Consider creating default template roles that are duplicated to create new processes.
- His example: When doing OS work, I usually do it based on the RPM package I'm making changes to, or the package system. e.g. I'll have a role named 'ensure_openssh' that handles any and all OpenSSH related tasks, and it is capable of doing Bastions, SFTP, and other tasks in the correct compliance scope. By putting everything for a single task into the same place, I can use the template feature to manage the configuration and avoid/ban the usage of things like lineinfile and other single object manipulation tasks. This increases the performance of the playbook runs as well as always ensuring that only authorized configurations are in place, and the total configuration was a tested configuration.

Git
- Each role and playbook should be in their own dedicated Git Repository. GitHub can work, but you will find a private GIT repo service like Gitea, Gogs, or GitLab better suited for this. e.g. put all Playbooks in the 'Team XXX Playbook' organization, and all roles are always kept common in sale 'AnsibleRoles'. Organization of this will help you later once you migrate into Ansible AWX.
- When putting your code into GIT, consider also how large complex files vs lots of smaller simple files will effect your team with multiple developers pushing changes at the same time.(ex: https://github.com/oracle-quickstart/oci-ansible-awx)