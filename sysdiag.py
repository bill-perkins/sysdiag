#!/usr/bin/python
#
# simple script to provide some diagnostics on local system
#

# imports:
import os
import subprocess

# global vars:

# -----------------------------------------------------------------------------
# class Diag
# -----------------------------------------------------------------------------
class Diag:
    """Diagnostics class
    """
    # instance variables:
    cpu_count = 0
    cpu_info = dict()
    cpu_load = ''
    datestamp = ''
    disklist = []
    disk_count = 0
    disk_dict = dict()
    mem_dict = dict()
    netstat = dict()
    net_interface = ''
    swap_dict = dict()
    sysname = ''

    # -----------------------------------------------------------------------------
    # humanize(float)
    # -----------------------------------------------------------------------------
    def humanize(self, f):
        if f < 1024:
            return str(f) + "B"

        if f < (1024 * 1024):
            return '{:3.1f}'.format(f / 1024.0) + "K"

        if f < (1024 * 1024 * 1024):
            return '{:3.1f}'.format(f / 1024.0 / 1024) + "M"

        return '{:3.1f}'.format(f / 1024.0 / 1024 / 1024) + "G"

    # -----------------------------------------------------------------------------
    # diskstat(name)
    # -----------------------------------------------------------------------------
    def diskstat(self, name):
        stat = os.statvfs(name)
        size = stat.f_frsize * stat.f_blocks
        free = stat.f_frsize * stat.f_bfree
        used = size - free
        usep = (1.0 - (float(free) / float(size))) * 100.0
        return name, size, used, free, usep

    # -----------------------------------------------------------------------------
    # diskdict_get(disklist)
    # -----------------------------------------------------------------------------
    def disk_get(self):
        for disk in self.disklist:
            td = dict()
            name, size, used, free, usep = self.diskstat(disk)
            td['name'] = name
            td['size'] = size
            td['used'] = used
            td['free'] = free
            td['usep'] = usep
            self.disk_dict[name] = td #[size, used, free, usep]

    # -----------------------------------------------------------------------------
    # pretty-print the disk usage:
    # -----------------------------------------------------------------------------
    def disk_print(self):
        for disk in self.disk_dict:
            p = self.disk_dict[disk]
            print "    ", disk, \
                    "size:", self.humanize(p['size']), \
                    "used:", self.humanize(p['used']), \
                    "free:", self.humanize(p['free']), \
                    "%used:", '{:3.1f}'.format(p['usep'])

    # -----------------------------------------------------------------------------
    # swapmem_get()
    # -----------------------------------------------------------------------------
    def swapmem_get(self):
        work = subprocess.check_output(['/usr/bin/free'], stderr=subprocess.STDOUT)
        work_strings = work.split('\n')
        headings     = work_strings[0].split()
        mem          = work_strings[1].split()
        swap         = work_strings[2].split()

        for i in range(1, len(headings) + 1):
            self.mem_dict[headings[i - 1]] = int(mem[i])

        for i in range(1, len(swap)):
            self.swap_dict[headings[i - 1]] = int(swap[i])

    # -----------------------------------------------------------------------------
    # swapmem_print()
    # -----------------------------------------------------------------------------
    def swapmem_print(self):
        print "    memory:"
        p = self.mem_dict
        print "        available:", self.humanize(p['available'])
        print "             used:", self.humanize(p['used'])
        print "             free:", self.humanize(p['free'])
        print "       buff/cache:", self.humanize(p['buff/cache'])
        print "           shared:", self.humanize(p['shared'])
        print "            total:", self.humanize(p['total'])
        print

        print "    swap:"
        p = self.swap_dict
        print "            total:", self.humanize(p['total'])
        print "             free:", self.humanize(p['free'])
        print "             used:", self.humanize(p['used'])
        print

    # -----------------------------------------------------------------------------
    # cpuload_get()
    # -----------------------------------------------------------------------------
    def cpuload_get(self):
        cpu_string = subprocess.check_output(['/usr/bin/mpstat','-P','ALL'], stderr=subprocess.STDOUT)
        cpu_array = cpu_string.split('\n')
        headings =  cpu_array[2].split()
        headings[0] = 'Time'
        headings[1] = 'AM/PM'

        self.cpu_count = len(cpu_array) - 5
        self.cpu_info['headings'] = headings

        for line in range(4, len(cpu_array) - 1):
            cpu_parts = cpu_array[line].split()
            td = dict()

            i = 0
            for hdr in self.cpu_info['headings']:
                td[hdr] = cpu_parts[i]
                i += 1

            self.cpu_info[cpu_parts[2]] = td

    # -----------------------------------------------------------------------------
    # cpuload_print()
    # -----------------------------------------------------------------------------
    def cpuload_print(self):
        """print CPU load info we've collected
        """
        for i in range(0, self.cpu_count):
            print "    CPU", str(i) + ":",
            x = self.cpu_info[str(i)]

            print x['%idle'] + '% idle'

    # -----------------------------------------------------------------------------
    # netstat_get()
    # -----------------------------------------------------------------------------
    def netstat_get(self):
        """init netstat info
        """
        net_string = subprocess.check_output(['/usr/sbin/ifconfig', self.net_interface], \
                stderr=subprocess.STDOUT)
        net_lines = net_string.split('\n')
        self.netstat['header'] = net_lines[0]
        self.netstat['address'] = net_lines[1].split()[1]

        parts = net_lines[5].split()
        self.netstat['rx_errors'] = { \
                'errors':   parts[2], \
                'dropped':  parts[4], \
                'overruns': parts[6], \
                'frame':    parts[8] }

        parts = net_lines[7].split()
        self.netstat['tx_errors'] = { \
                'errors':     parts[2], \
                'dropped':    parts[4], \
                'overruns':   parts[6], \
                'carrier':    parts[8], \
                'collisions': parts[10] }

    # -----------------------------------------------------------------------------
    # netstat_print()
    # -----------------------------------------------------------------------------
    def netstat_print(self):
        #print self.netstat
        print "    interface:", self.netstat['header']
        print "    address:  ", self.netstat['address']
        print "    RX errors:", self.netstat['rx_errors']
        print "    TX errors:", self.netstat['tx_errors']

    # -----------------------------------------------------------------------------
    # __init__()
    # -----------------------------------------------------------------------------
    def __init__(self):
        """Bring in the local .ini file
        """
        my_ini = __file__ + ".ini"
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
                self.datestamp = entrylist[1]

            if entrylist[0] == "system_name":
                self.sysname = entrylist[1]

            if entrylist[0] == "disk_list":
                self.disk_count = len(entrylist) - 1
                for i in range(1, self.disk_count + 1):
                    self.disklist.append(entrylist[i])

            if entrylist[0] == "network":
                self.net_interface = entrylist[1]

        self.disk_get()
        self.cpuload_get()
        self.swapmem_get()
        self.netstat_get()


# -----------------------------------------------------------------------------
# main part of the program:
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    diag = Diag()

    hostname = os.environ.get('HOSTNAME')
    if diag.sysname != hostname:
        print "system_name entry '" + diag.sysname + \
                "' not the same as $HOSTNAME '" + hostname + "'"
    else:
        print "system:    ", diag.sysname

    print

    print "datestamp: ", diag.datestamp
    print "disk_count:", diag.disk_count
    print "disk list: ", diag.disklist
    print "network:   ", diag.net_interface
    print

    print "Disks:"
    diag.disk_print()
    print

    print "CPU loads:"
    diag.cpuload_print()
    print

    print "Memory and Swap space:"
    diag.swapmem_print()
    print

    print "Network info:"
    diag.netstat_print()
    print

# -----------------------------------------------------------------------------
# 
# -----------------------------------------------------------------------------

# EOF:
