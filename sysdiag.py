#!/usr/bin/python
#
# simple script to provide some diagnostics on local system

# imports:
import os
import subprocess
import shutil

# global vars:
disklist = []
disk_count = 0
datestamp = ''
sysname = ''
disk_dict = dict()

# -----------------------------------------------------------------------------
# --- initialize():
# -----------------------------------------------------------------------------
def initialize():
    my_ini = __file__ + ".ini"
    global disklist
    global disk_count
    global datestamp
    global sysname

    inp = open(my_ini, "r")
    lines = inp.readlines()
    inp.close()

    for line in lines:
        # skip blanks, comments:
        if len(line) == 1 or line.startswith('#'):
            continue

        # we have key:value pairs
        entrylist = line.split()
        if entrylist[0] == 'datestamp':
            datestamp = entrylist[1]

        if entrylist[0] == "system_name":
            sysname = entrylist[1]

        if entrylist[0] == "disk_list":
            disk_count = len(entrylist)
            for i in range(1, disk_count):
                disklist.append(entrylist[i])

# -----------------------------------------------------------------------------
# --- humanize(float)
# -----------------------------------------------------------------------------
def humanize(f):
    if f < 1024:
        return str(f) + "B"

    if f < (1024 * 1024):
        #return str(f / 1024.0) + "K"
        return '{:3.1f}'.format(f / 1024.0) + "K"

    if f < (1024 * 1024 * 1024):
        #return str(f / 1024.0 / 1024) + "M"
        return '{:3.1f}'.format(f / 1024.0 / 1024) + "M"

    #return str(f / 1024.0 / 1024 / 1024) + "G"
    return '{:3.1f}'.format(f / 1024.0 / 1024 / 1024) + "G"


# -----------------------------------------------------------------------------
# --- diskstat(name)
# -----------------------------------------------------------------------------
def diskstat(name):
    stat = os.statvfs(name)
    size = stat.f_frsize * stat.f_blocks
    free = stat.f_frsize * stat.f_bfree
    used = size - free
    usep = (1.0 - (float(free) / float(size))) * 100.0
    return name, size, used, free, usep

# -----------------------------------------------------------------------------
# --- get_diskdict(disklist)
# -----------------------------------------------------------------------------
def get_diskdict(disklist):
    lcldict = dict()
    for disk in disklist:
        name, size, used, free, usep = diskstat(disk)
        lcldict[name] = [size, used, free, usep]

    return lcldict

# -----------------------------------------------------------------------------
# --- get_cpuload()
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# --- get_swap()
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# --- get_memory()
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# --- get_network
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# --- 
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# --- main part of the program:
# -----------------------------------------------------------------------------
initialize()

print "disk_count:", disk_count
print "disk list :", disklist
print "datestamp :", datestamp

hostname = os.environ.get('HOSTNAME')
if sysname != hostname:
    print "system_name entry '" + sysname,"' not the same as $HOSTNAME '" + hostname + "'"
else:
    print "sysname   :", sysname

# get disk dictionary:
disk_dict = get_diskdict(disklist)

## --- pretty-print the disk usage:
for disk in disk_dict:
    p = disk_dict[disk]
    print disk, \
            "size:", humanize(p[0]), \
            "used:", humanize(p[1]), \
            "free:", humanize(p[2]), \
            "%used:", '{:3.1f}'.format(p[3])

# EOF:
