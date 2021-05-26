Main
  // Create Infrastructure
  if CS {
      Create Networking Infrastructure
      - Call Infrastructure Role
  }
  // Create Infrastructure - Async (TODO - Check)
  if CS {
  }
  else {
  }
  // Check If EXA Infrastructure was created
  while (true) {
      if (Call Role Exa Check  LifeCycle Status == PROVISIONED {
          delay {{ delay minutes }}
          break
      }
      else {
          if (count > 32) {
              error 
          }
      }
  } 



Role
  - Infrastructure
    - Networking
  - Exa Infrastructure Creation - one time big tasks
    - Create Infrastructure
  - Exa VM Cluster Creation (CC | CS) - one time big tasks
    - Create VM-Cluster
  - Create DB (CC | CS) - common operations
  - Create DB Home (CC | CS) - common operations
  - Backups (CC | CS) - common operations
  
  - DB role (CC | CS) - common operations
    - Create DB Home
    - Create DB
    - Enable Automatic Backup
    - Create new Backup
    - Upgrade ExaInfra?
    - Upgrade DB?

