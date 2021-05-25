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
  - Exa functions [CC|CS]
    - Exa Create Infrastructure
    - Exa Create VM Cluster
    - Exa Create DB Home
    - Exa Create DB
    - Exa Check LifeCycle Status
    - Exa Enable Auto Backup
    - Exa Create Backup

Role
  - Infrastructure
    - Networking
  - Exa CC Role - All ExaCC functions
    - Create Infrastructure
    - Create VM-Cluster
  - Exa CS role - All ExaCS functions
    - Create Infrastructure
    - Create VM-Cluster
  - DB role (CC | CS)
    - Create DB Home
    - Create DB
    - Enable Automatic Backup
    - Create new Backup

Role
  - Infrastructure
    - Networking
  - Exa Creation (CC | CS) - one time big tasks
    - Create Infrastructure
    - Create VM-Cluster
  - DB role (CC | CS) - common operations
    - Create DB Home
    - Create DB
    - Enable Automatic Backup
    - Create new Backup
    - Upgrade ExaInfra
    - Upgrade DB

Design Choices
- 