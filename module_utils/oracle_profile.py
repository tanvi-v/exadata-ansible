#!/usr/bin/python

def profile_setting_matches(conn,profile,resourceName,limit):
    cursor = conn.cursor()
    cursor.execute("select limit from dba_profiles where profile = :profilev and resource_name = :resourcev",
            [profile.upper(),resourceName.upper()])
    r = cursor.fetchone()
    cursor.close()
    return limit.upper() == r[0].upper()

def modify_profile(conn,profile,resourceName,limit):
    cursor = conn.cursor()
    cursor.execute(f'alter profile {profile} limit {resourceName} {limit}')
    cursor.close()
