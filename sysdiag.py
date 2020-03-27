#!/usr/bin/python
# simple script to provide some diagnostics on local system
# uses a .ini file for system-specific paramters
#

# imports:
import os
import subprocess
import sys
from datetime import datetime
import pprint

# -----------------------------------------------------------------------------
# class Diag
# -----------------------------------------------------------------------------
class Diag:
    """Diagnostics class
    """
    # instance variables:
    cpu_count = 0
    cpus = dict()
    datestamp = ''
    disk_list = []
    disk_count = 0
    disks = dict()
    memory = dict()
    my_path = ''
    network = dict()
    net_interface = ''
    services_list = []
    services = dict()
    swapinfo = dict()
    sysname = ''
    netping_lines = []
    uptime = ''

    # -----------------------------------------------------------------------------
    # humanize(number)
    # -----------------------------------------------------------------------------
    def humanize(self, f):
        """turn an integer into human-readable format
        """
        if f < 1024:
            return str(f) + "B"

        if f < (1024 * 1024):
            return '{:3.1f}'.format(f / 1024.0) + "K"

        if f < (1024 * 1024 * 1024):
            return '{:3.1f}'.format(f / 1024.0 / 1024) + "M"

        if f < (1024 * 1024 * 1024 * 1024):
            return '{:3.1f}'.format(f / 1024.0 / 1024 / 1024) + "G"

        return '{:3.1f}'.format(f / 1024.0 / 1024 / 1024 / 1024) + "T"

    # -----------------------------------------------------------------------------
    # disk_stat(name)
    # -----------------------------------------------------------------------------
    def disk_stat(self, name):
        """get stats on a given disk name
        """
        stat = os.statvfs(name)
        size = stat.f_frsize * stat.f_blocks
        free = stat.f_frsize * stat.f_bfree
        used = size - free
        usep = ((1.0 - (float(free) / float(size))) * 100.0) + 0.5
        return name, size, used, free, usep

    # -----------------------------------------------------------------------------
    # disks_load(disk_list)
    # -----------------------------------------------------------------------------
    def disks_load(self):
        """create dictionary for the disks in disk_list
        """
        for disk in self.disk_list:
            td = dict()
            name, size, used, free, usep = self.disk_stat(disk)
            td['name'] = name
            td['size'] = size
            td['used'] = used
            td['free'] = free
            td['usep'] = usep
            self.disks[name] = td #[size, used, free, usep]

    # -----------------------------------------------------------------------------
    # pretty-print the disk usage:
    # -----------------------------------------------------------------------------
    def disk_print(self):
        """pretty-print the disk stats
        """
        for index in self.disk_list:
            p = self.disks[index]
            x = index.ljust(16) + \
                    "size: " + self.humanize(p['size']).rjust(7)+ \
                    "  used: " + self.humanize(p['used']).rjust(7)+ \
                    "  free: " + self.humanize(p['free']).rjust(7)+ \
                    "  %used: " + '{:3.1f}'.format(p['usep']).rjust(4)
            print "    " + x

    # -----------------------------------------------------------------------------
    # swapmem_load()
    # -----------------------------------------------------------------------------
    def swapmem_load(self):
        """get memory and swap information
        """
        work = subprocess.check_output(['/usr/bin/free'], stderr=subprocess.STDOUT)
        work_strings = work.split('\n')
        headings     = work_strings[0].split()
        mem          = work_strings[1].split()
        swap         = work_strings[2].split()

        for i in range(1, len(headings) + 1):
            self.memory[headings[i - 1]] = int(mem[i])

        for i in range(1, len(swap)):
            self.swapinfo[headings[i - 1]] = int(swap[i])

    # -----------------------------------------------------------------------------
    # swapmem_print()
    # -----------------------------------------------------------------------------
    def swapmem_print(self):
        """pretty-print the memory and swap information
        """
        print "    memory:"
        p = self.memory
        print "             used:", self.humanize(p['used']).rjust(7)
        print "        available:", self.humanize(p['available']).rjust(7)
        print "             free:", self.humanize(p['free']).rjust(7)
        print "       buff/cache:", self.humanize(p['buff/cache']).rjust(7)
        print "           shared:", self.humanize(p['shared']).rjust(7)
        print "            total:", self.humanize(p['total']).rjust(7)
        print

        print "    swap:"
        p = self.swapinfo
        print "             used:", self.humanize(p['used']).rjust(7)
        print "             free:", self.humanize(p['free']).rjust(7)
        print "            total:", self.humanize(p['total']).rjust(7)
        print

    # -----------------------------------------------------------------------------
    # cpus_load()
    # -----------------------------------------------------------------------------
    def cpus_load(self):
        """get current load information for each CPU
        """
        cpu_string = subprocess.check_output(['/usr/bin/mpstat','-P','ALL'], stderr=subprocess.STDOUT)
        cpu_array = cpu_string.split('\n')

        # headings holds the keys to cpus dictionary:
        headings =  cpu_array[2].split()
        headings[0] = 'Time'
        headings[1] = 'AM/PM'

        self.cpu_count = len(cpu_array) - 5

        for line in range(4, len(cpu_array) - 1):
            cpu_parts = cpu_array[line].split()
            td = dict()

            i = 0
            for hdr in headings:
                td[hdr] = cpu_parts[i]
                i += 1

            self.cpus[cpu_parts[2]] = td

    # -----------------------------------------------------------------------------
    # cpus_print()
    # -----------------------------------------------------------------------------
    def cpus_print(self):
        """pretty-print CPU load info we've collected
        """
        for i in range(0, self.cpu_count):
            print "    CPU", str(i) + ":",
            x = self.cpus[str(i)]

            print x['%idle'] + '% idle'

    # -----------------------------------------------------------------------------
    # network_load()
    # -----------------------------------------------------------------------------
    def network_load(self):
        """get network info
        """
        net_string = subprocess.check_output(['/usr/sbin/ifconfig', self.net_interface], \
                stderr=subprocess.STDOUT)
        net_lines = net_string.split('\n')
        self.network['header'] = net_lines[0]
        self.network['address'] = net_lines[1].split()[1]

        parts = net_lines[5].split()
        self.network['rx_errors'] = { \
                'errors':   parts[2], \
                'dropped':  parts[4], \
                'overruns': parts[6], \
                'frame':    parts[8] }

        parts = net_lines[7].split()
        self.network['tx_errors'] = { \
                'errors':     parts[2], \
                'dropped':    parts[4], \
                'overruns':   parts[6], \
                'carrier':    parts[8], \
                'collisions': parts[10] }

    # -----------------------------------------------------------------------------
    # netping_load()
    # -----------------------------------------------------------------------------
    def netping_load(self):
        """do the sysping thing
        """
        names = []
        pingoutput = ""
        pingerrors = []

        hostsfile = open("/etc/hosts","r")
        hostslines = hostsfile.readlines()
        hostsfile.close()

        for line in hostslines:
            # skip blanks, comments, localhost lines:
            if len(line) == 1 or line.startswith('#') or line.startswith('127.0.0.1') or line.startswith('::1'):
                continue

            # we have what should be an IP address, output the last name:
            entrylist = line.split()
            names.append((str(entrylist[-1]), str(entrylist[0])))

        for pinghost in names:
            try:
                pingoutput = subprocess.check_output(["/usr/bin/ping",'-c','1', pinghost[0]], \
                        stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as error:
                self.netping_lines.append("can't ping " + pinghost[0] + " by name, trying ip " + pinghost[1])
                try:
                    pingoutput = subprocess.check_output(["/usr/bin/ping",'-c','1', pinghost[1]], \
                            stderr=subprocess.STDOUT)
                except subprocess.CalledProcessError as error:
                    self.netping_lines.append("can't ping " + pinghost[0] + " by ip: " + pinghost[1])

    # -----------------------------------------------------------------------------
    # service_check()
    # -----------------------------------------------------------------------------
    def service_check(self, svc):
        """check given service,
           returns tokens 2 & 3 from line 3 of systemctl status:
           'active/dead/whatever', 'running/stopped/dead/missing'
        """
        try:
            work = subprocess.check_output(['/usr/bin/systemctl','status',svc], stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as error:
            work = error.output

        # take work, split it into lines, take the 3rd line, split it into parts:
        try:
            parts = work.split('\n')[2].split()
        except IndexError as error:
            return work #.split['\n'] #[2]

        return parts[1], parts[2]

    # -----------------------------------------------------------------------------
    # services_load()
    # -----------------------------------------------------------------------------
    def services_load(self):
        """gather services info into services dictionary
        """
        for svc in self.services_list:
            self.services[svc] = self.service_check(svc)

    # -----------------------------------------------------------------------------
    # network_print()
    # -----------------------------------------------------------------------------
    def network_print(self):
        """pretty-print the network information
        """
        print "    interface:", self.network['header']
        print "      address:", self.network['address']

        print "    RX errors:",
        x = self.network['rx_errors']
        for k,v in x.items():
            print k + ":", v,
        print

        print "    TX errors:",
        x = self.network['tx_errors']
        for k,v in x.items():
            print k + ":", v,
        print

    # -----------------------------------------------------------------------------
    # __init__()
    # -----------------------------------------------------------------------------
    def __init__(self):
        """Bring in the local .ini file
           The .ini file consists of comments, blank lines, and key-value pairs.
           The following keys are recognized in the .ini file:
               system_name - the FQDN of this system
               network     - the network interface name, shown in ifconfig
               disk        - mulitple entries for disks we track
               service     - multiple entries for systemctl services
        """

        self.my_path = os.path.dirname(__file__)
        my_ini = self.my_path + "/sysdiag.ini"

        try:
            inp = open(my_ini, "r")
        except IOError as error:
            print "File", my_ini + ":", error.strerror
            sys.exit(1)

        lines = inp.readlines()
        inp.close()

        work = subprocess.check_output(['/usr/bin/w'], stderr=subprocess.STDOUT)
        self.uptime = ' '.join(work.split('\n')[0].split()[2:])

        for line in lines:
            # skip blanks, comments:
            if len(line) == 1 or line.startswith('#') or len(line.strip()) == 1:
                continue

            # we have a key:value pair (hopefully)
            entrylist = line.strip().split()

            if len(entrylist) != 2:
                print "*** malformed line: '" + line + "'"
                continue;

            if entrylist[0] == "system_name":
                self.sysname = entrylist[1]

            if entrylist[0] == "network":
                self.net_interface = entrylist[1]

            if entrylist[0] == "service":
                self.services_list.append(entrylist[1])

            if entrylist[0] == "disk":
                self.disk_count += 1
                self.disk_list.append(entrylist[1])

        self.datestamp = datetime.now().strftime("%Y%m%d %H:%M:%S")
        self.disks_load()
        self.cpus_load()
        self.swapmem_load()
        self.network_load()
        self.netping_load()
        self.services_load()

# end of Class Diag

# -----------------------------------------------------------------------------
# create the .ini file:
# -----------------------------------------------------------------------------
def create_ini():
    sysname  = subprocess.check_output(['/usr/bin/hostname'], stderr=subprocess.STDOUT)
    disks    = subprocess.check_output(['/usr/bin/df'], stderr=subprocess.STDOUT)
    network  = subprocess.check_output(['/usr/sbin/ifconfig'], stderr=subprocess.STDOUT)
    services = subprocess.check_output(['/bin/ls','/etc/init.d/'], stderr=subprocess.STDOUT)

    # ---------------------------------
    print "system_name", sysname.rstrip()
    print

    # --- disks:
    print "# disks: please edit:"
    disklines = disks.split('\n')
    for line in disklines:
        if "tmpfs" in line:
            continue;

        parts = line.split()
        if len(parts) != 6:
            continue;

        print "disk", parts[5]
    print

    # --- network interface:
    netlines = network.split('\n')
    counter = 0
    outlines = ''
    for line in netlines:
        if "RUNNING" in line:
            parts = line.split()
            if parts[0] != "lo:":
                outlines += "network " + str(parts[0][:-1]) + "\n"
                counter += 1

    if counter == 0:
        print "# !!! no running network interfaces found !!!"
        print
    elif counter > 1:
        print "# network: choose one:"
        print outlines
    else:
        print "# network:"
        print outlines

    # --- available services:
    print "# services: please edit:"
    l = services.split('\n')
    for s in l:
        if len(s) > 0:
            print "service", s
    print

    # --- the end:
    print "# EOF:"

# -----------------------------------------------------------------------------
# main part of the program:
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """If they give us a -c, create a .ini file.
       If they give us anything else, print a usage message.
       Otherwise, create a Diag instance and display what we find.
    """
    if len(sys.argv) > 1:
        if sys.argv[1] == "-c":
            create_ini()
            sys.exit(0)
        else:
            print "usage:", __file__, " [-c >new-ini-file] # creates new sysdiag.ini"
            sys.exit(1)

    broken = False
    diag = Diag()

    hostname = subprocess.check_output(['/usr/bin/hostname'], stderr=subprocess.STDOUT)
    if diag.sysname != hostname.rstrip():
        print "system_name entry '" + diag.sysname + \
                "' not the same as '" + str(hostname) + "'"
    else:
        print "system:    ", diag.sysname

    print "uptime:    ", diag.uptime
    print

    print "datestamp: ", diag.datestamp
    print "disk_count:", diag.disk_count
    print "network:   ", diag.net_interface
    print

    print "Disks:"
    diag.disk_print()
    print

    print "CPU loads:"
    diag.cpus_print()
    print

    print "Memory and Swap space:"
    diag.swapmem_print()
    print

    print "Network info:"
    diag.network_print()
    print
    print "Sysping:",
    if len(diag.netping_lines) == 0:
        print "OK"
    else:
        print
        for l in diag.netping_lines:
            print l
    print

    print "Services:"
    for svc in diag.services:
        x = diag.services[svc]
        if x[0] != 'active' or x[1] != '(running)':
            print "    " + svc + ":", diag.services[svc]
            broken = True

    if not broken:
        print "    all", str(len(diag.services)) + " services are running"

    """ use this when we want to examine the dictionaries:
    pp = pprint.PrettyPrinter(indent=4)
    print
    print "CPU dictionary:"
    pp.pprint(diag.cpus)
    print
    print "disks dictionary:"
    pp.pprint(diag.disks)
    print
    print "memory dictionary:"
    pp.pprint(diag.memory)
    print
    print "network dictionary:"
    pp.pprint(diag.network)
    print
    print "swap dictionary:"
    pp.pprint(diag.swapinfo)
#   """
    pp = pprint.PrettyPrinter(indent=4)
    print
    print "services dictionary:"
    pp.pprint(diag.services)
    print

# -----------------------------------------------------------------------------
# 
# -----------------------------------------------------------------------------

# EOF:
