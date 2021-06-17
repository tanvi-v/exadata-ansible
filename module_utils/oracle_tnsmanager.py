#!/usr/bin/python


def get_tns_entry(aliasName,hostList,port,serviceName):
    if len(hostList) == 1:
        entry = f"""{aliasName.lower()} =
  (DESCRIPTION=
    (ENABLE=BROKEN)
    (ADDRESS=(PROTOCOL=TCP)(HOST={hostList[0]})(PORT={port}))
    (CONNECT_DATA=
      (SERVICE_NAME={serviceName.lower()}.heb.com)
    )
  )"""
    else:
        addressList = []
        for h in hostList:
            addressList.append(' ' * 7 + f'(ADDRESS=(PROTOCOL=TCP)(HOST={h})(PORT={port}))' + '\n')
        entry = f"""{aliasName.lower()} =
  (DESCRIPTION=
    (ENABLE=BROKEN)
    (FAILOVER=ON)
    (RETRY_COUNT=3)
    (ADDRESS_LIST=
{''.join(addressList)}    )
    (CONNECT_DATA=
      (SERVICE_NAME={serviceName.lower()}.heb.com)
    )
  )"""
    return entry

def get_jdbc_entry(aliasName,hostList,port,serviceName):
    if len(hostList) == 1:
        entry = f"""jdbc:oracle:thin:@(DESCRIPTION=(ENABLE=BROKEN)(ADDRESS=(PROTOCOL=TCP)(HOST={hostList[0]})(PORT={port}))(CONNECT_DATA=(SERVICE_NAME={serviceName.lower()}.heb.com)))"""
    else:
        addressList = []
        for h in hostList:
            addressList.append(f'(ADDRESS=(PROTOCOL=TCP)(HOST={h})(PORT={port}))')
        entry = f"""jdbc:oracle:thin:@(DESCRIPTION=(ENABLE=BROKEN)(FAILOVER=ON)(RETRY_COUNT=3)(ADDRESS_LIST={''.join(addressList)})(CONNECT_DATA=(SERVICE_NAME={serviceName.lower()}.heb.com)))"""
    return entry
