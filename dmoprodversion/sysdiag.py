#!/usr/bin/env python
# simple script to provide some diagnostics on local system
# uses a .ini file for system-specific paramters
#

## only need this if we are running python2:
from __future__ import print_function

import os
import subprocess
import sys
from datetime import datetime
import pprint
import glob

g_ini_file = ''

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
    network = dict()
    net_interface = ''
    netping_lines = []
    os_version = ''
    services_list = []
    services = dict()
    swapinfo = dict()
    sysname = ''
    uptime = ''

    # -----------------------------------------------------------------------------
    # humanize(number)
    # -----------------------------------------------------------------------------
    def humanize(self, f):
        """turn an integer into human-readable format
        """
#        print('humanize(): f =', f)

        try:
            if f < 1024:
                outstr = str(f) + 'B'
                return outstr

            if f < (1024 * 1024):
                val = f / 1024.0
                outstr = '{0:3.1f}'.format(val) + 'K'
                return outstr

            if f < (1024 * 1024 * 1024):
                val = f / 1024.0 / 1024.0
                outstr = '{0:3.1f}'.format(val) + 'M'
                return outstr

            if f < (1024 * 1024 * 1024 * 1024):
                val = f / 1024.0 / 1024.0 / 1024.0
                outstr = '{0:3.1f}'.format(val) + 'G'
                return outstr

            val = f / 1024.0 / 1024.0 / 1024.0 / 1024.0
            outstr = '{0:3.1f}'.format(val) + 'T'
            return outstr

        except ValueError as error:
            print('error:', val, error)
            print()
            outstr = str(error)
            return outstr

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
            td['name'], td['size'], td['used'], td['free'], td['usep'] = self.disk_stat(disk)
            self.disks[td['name']] = td #[size, used, free, usep]
#            print('td =', td)

    # -----------------------------------------------------------------------------
    # pretty-print the disk usage:
    # -----------------------------------------------------------------------------
    def disk_print(self):
        """pretty-print the disk stats
        """
        print('    filesystem:       size:   used:   free:  %use:')
        for index in self.disk_list:
            p = self.disks[index]
            usep    = p['usep']
            usepstr = '{0:3.1f}'.format(usep)
#            free    = p['free']
#            freestr = '{0:3.1f}'.format(free)

            try:
                x = index.ljust(16) + \
                        self.humanize(p['size']).rjust(7) + \
                        self.humanize(p['used']).rjust(8) + \
                        self.humanize(p['free']).rjust(8) + \
                        usepstr.rjust(7)
            except AttributeError as error:
                print('error:', error)
                print('freestr:', freestr)
            print('    ' + x)

    # -----------------------------------------------------------------------------
    # swapmem_load()
    # -----------------------------------------------------------------------------
    def swapmem_load(self):
        """get memory and swap information
        """
#        work = subprocess.check_output(['/usr/bin/free', '-b'], stderr=subprocess.STDOUT)
        cmd = subprocess.Popen(['/usr/bin/free', '-b'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result = cmd.communicate()
        work = result[0].decode('utf-8').rstrip()

        work_strings = work.splitlines()
        headings     = work_strings[0].split()
        mem          = work_strings[1].split()
        swap         = work_strings[2].split()
        if work_strings[2].startswith('-/+'):
            swap     = work_strings[3].split()

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
        print('    memory:')
        p = self.memory
        print('             used:', self.humanize(p['used']).rjust(7))
        if 'available' in p.keys():
            print('        available:', self.humanize(p['available']).rjust(7))
        else:
            avail = p['cached'] + p['free']
            print('        available:', self.humanize(avail).rjust(7))

        print('             free:', self.humanize(p['free']).rjust(7))
        if 'buff/cache' in p.keys():
            print('       buff/cache:', self.humanize(p['buff/cache']).rjust(7))
        else:
            buffcache = p['buffers'] + p['cached']
            print('       buff/cache:', self.humanize(buffcache).rjust(7))

        print('           shared:', self.humanize(p['shared']).rjust(7))
        print('            total:', self.humanize(p['total']).rjust(7))
        print()

        print('    swap:')
        p = self.swapinfo
        print('             used:', self.humanize(p['used']).rjust(7))
        print('             free:', self.humanize(p['free']).rjust(7))
        print('            total:', self.humanize(p['total']).rjust(7))
        print()

    # -----------------------------------------------------------------------------
    # cpus_load()
    # -----------------------------------------------------------------------------
    def cpus_load(self):
        """get current load information for each CPU
        """
        # no mpstat in Centos6.3:
        return None

#        work = subprocess.check_output(['/usr/bin/mpstat', '-P', 'ALL'], stderr=subprocess.STDOUT)
        cmd = subprocess.Popen(['/usr/bin/mpstat', '-P', 'ALL'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result = cmd.communicate()
        work = result[0].decode('utf-8').rstrip()

        cpu_array = str(work).splitlines()

        # headings holds the keys to cpus dictionary:
        headings =  cpu_array[2].split()
        headings[0] = 'Time'
        headings[1] = 'AM/PM'

        self.cpu_count = len(cpu_array) - 4

        for line in range(4, len(cpu_array)):
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
            print('    CPU', str(i) + ':', end=' ')
            x = self.cpus[str(i)]

            print(x['%idle'] + '% idle')

    # -----------------------------------------------------------------------------
    # network_load()
    # -----------------------------------------------------------------------------
    def network_load(self):
        """get network info
        """
        index = 5

# Python3:
#        work = subprocess.check_output(['/usr/sbin/ifconfig', self.net_interface], \
#        stderr=subprocess.STDOUT)

# Python2:
        cmd = subprocess.Popen(['/sbin/ifconfig', self.net_interface], \
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result = cmd.communicate()
        work = result[0].decode('utf-8').rstrip()

# back to normal code:
        net_lines = work.splitlines()
        self.network['header'] = net_lines.pop(0)
        self.network['address'] = net_lines.pop(0).split()[1]
        if net_lines[0].startswith('inet6'):
            net_lines.pop(0)

        while len(net_lines) > 0:
            lclstr = net_lines.pop(0).strip()
            if lclstr.startswith('RX packets'):
                if ':' in lclstr:
                    lclstr = lclstr.replace(':', ' ')

                parts = lclstr.split()
                if parts[3] == 'errors':
                    self.network['rx_errors'] = { \
                            'errors': parts[4], \
                            'dropped': parts[6], \
                            'overruns': parts[8], \
                            'carrier': parts[10] }

                continue

            if lclstr.startswith('TX packets'):
                if ':' in lclstr:
                    lclstr = lclstr.replace(':', ' ')

                parts = lclstr.split()
                if parts[3] == 'errors':
                    self.network['tx_errors'] = { \
                            'errors': parts[4], \
                            'dropped': parts[6], \
                            'overruns': parts[8], \
                            'carrier': parts[10] }
                continue

            if lclstr.startswith('RX errors'):
                parts = lclstr.split()
                self.network['rx_errors'] = { \
                        parts[1]: parts[2], \
                        parts[3]: parts[4], \
                        parts[5]: parts[6], \
                        parts[7]: parts[8] }
                continue

            if lclstr.startswith('TX errors'):
                parts = lclstr.split()
                self.network['tx_errors'] = { \
                        parts[1]: parts[2], \
                        parts[3]: parts[4], \
                        parts[5]: parts[6], \
                        parts[7]: parts[8] }
                continue

            if lclstr.startswith('collisions'):
                lclstr = lclstr.replace(':', ' ')
                parts = lclstr.split()
                p = self.network['tx_errors']
                p['collisions'] = parts[1]
                continue

    # -----------------------------------------------------------------------------
    # netping_load()
    # -----------------------------------------------------------------------------
    def netping_load(self):
        """do the sysping thing
        """
        names = []
        pingoutput = ''
        pingerrors = []

        with open('/etc/hosts', 'r') as hostsfile:
            hostslines = hostsfile.readlines()

        for line in hostslines:
            # skip blanks, comments, localhost lines:
            if len(line) == 1 \
                    or line.startswith('#') \
                    or line.startswith('127.0.0.1') \
                    or line.startswith('::1'):
                continue

            # we have what should be an IP address, output the last name:
            entrylist = line.split()
            names.append((str(entrylist[-1]), str(entrylist[0])))

        for pinghost in names:
            try:
                cmd = subprocess.Popen(['/bin/ping', '-c','1', pinghost[0]], \
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                result = cmd.communicate()
                pingoutput = result[0].decode('utf-8').rstrip() # single-line response needs rstrip()

            except subprocess.CalledProcessError as error:
                self.netping_lines.append("can't ping " + pinghost[0] + ' by name, trying ip ' + pinghost[1])
                try:
                    cmd = subprocess.Popen(['/usr/bin/ping', '-c','1', pinghost[1]], \
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                    result = cmd.communicate()
                    pingoutput = result[0].rstrip() # single-line response needs rstrip()
                except subprocess.CalledProcessError as error:
                    self.netping_lines.append("can't ping " + pinghost[0] + ' by ip: ' + pinghost[1])

    # -----------------------------------------------------------------------------
    # service_check()
    # -----------------------------------------------------------------------------
    def service_check(self, svc):
        """check given service,
           returns tokens 2 & 3 from line 3 of systemctl status:
           'active/dead/whatever', 'running/exited/stopped/dead/missing'
        """
        try:
# cmd = subprocess.Popen(['/usr/bin/systemctl', 'status', svc], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            cmd = subprocess.Popen(['/sbin/service', svc, 'status'], \
                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            result = cmd.communicate()
            work = result[0].decode('utf-8').rstrip()
        except subprocess.CalledProcessError as error:
            work = error.output

        svclines = work.splitlines()
        if len(work) != 0:
            return work
#            if 'Usage: ' in work:
#                return 'usage message'
#
#            if 'is running' in work:
#                return work
#
#            if 'is stopped' in work:
#                return work
#
#            print()
#            print('work:', work)
#            print('svclines:', svclines)
#
#        # take work, split it into lines, take the 3rd line, split it into parts:
#        try:
#            parts = svclines[2].split()
#        except IndexError as error:
#            return 'missing', 'gone'
#
#            #print('service_check(): len(svclines) =', len(svclines), 'Returning:')
#            #print(work)
#            #print()
#            #return work
#
#        # return active/inactive, (running/stopped/exited):
##        return parts[1], parts[2]
        return work

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
        print('    interface:', self.network['header'])
        print('      address:', self.network['address'])

        print('    RX errors:', end=' ')
        x = self.network['rx_errors']
        for k,v in list(x.items()):
            print(k + ':', v, end=' ')
        print()

        print('    TX errors:', end=' ')
        x = self.network['tx_errors']
        for k,v in list(x.items()):
            print(k + ':', v, end=' ')
        print()

    # -----------------------------------------------------------------------------
    # __init__()
    # -----------------------------------------------------------------------------
    def __init__(self):
        """ Bring in the local .ini file
            The .ini file consists of comments, blank lines, and key-value pairs.
            The following keys are recognized in the .ini file:
                system_name - the FQDN of this system
                network     - the network interface name, shown in ifconfig
                disk        - mulitple entries for disks we track
                service     - multiple entries for systemctl services
        """

        my_path = os.path.dirname(__file__) # find out just where we are
        if my_path == '':
            my_path = '.'

        my_ini = my_path + '/sysdiag.ini'   # assume ini file is where we are

        if g_ini_file != '':                # if they specified a .ini file,
            my_ini = g_ini_file             # use it instead.

        with open(my_ini, 'r') as inp:
            lines = inp.readlines()

        # process the ini lines:
        for line in lines:
            # skip blanks, comments:
            if len(line) == 1 or line.startswith('#') or len(line.strip()) == 1:
                continue

            # we have a key:value pair (hopefully)
            entrylist = line.strip().split()

            if len(entrylist) != 2:
                print('*** malformed line: ' + line)
                continue;

            if entrylist[0] == 'system_name':
                self.sysname = entrylist[1]

            if entrylist[0] == 'network':
                self.net_interface = entrylist[1]

            if entrylist[0] == 'service':
                self.services_list.append(entrylist[1])

            if entrylist[0] == 'disk':
                self.disk_count += 1
                self.disk_list.append(entrylist[1])

        # snag the uptime:
#        work = subprocess.check_output(['/usr/bin/w'], stderr=subprocess.STDOUT)
        cmd = subprocess.Popen(['/usr/bin/w'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result = cmd.communicate()
        work = result[0].decode('utf-8').rstrip()
        # I got fancy here:
        str_work = str(work)
        self.uptime = ' '.join(str(str_work.split('\n')[0]).split()[2:])

        # current date and time:
        self.datestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        # get the os_version:
        flist = ['/etc/system-release', '/etc/redhat-release', '/etc/os-release']
        os_version_failure = 0
        for lclfile in flist:
            try:
                with open(lclfile, 'r') as osfile:
                    self.os_version = osfile.readline().rstrip()
                    break;
            except IOError as error:
                os_version_failure += 1

        if os_version_failure == len(flist):
            print("Non-fatal error getting version info: can't find:", flist)
            print()

        # load up the dictionaries:
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
    """create the lines for a sysdiag.ini file.
       Output sent to stdout, capture it as you will.
       Be sure to edit the resulting output.
    """

    # --- system name:
#    sysname = subprocess.check_output(['/usr/bin/hostname'], stderr=subprocess.STDOUT)
    cmd = subprocess.Popen(['/bin/hostname'], stdout=subprocess.PIPE)
    result = cmd.communicate()
    sysname = result[0].decode('utf-8').rstrip()

    print('# sysdiag.ini:')
    print()
    print('system_name:', sysname)
    print()

    # --- disks:
    print('# disks: please edit:')
#    disklines = subprocess.check_output(['/usr/bin/df'], stderr=subprocess.STDOUT)
    cmd    = subprocess.Popen(['/bin/df'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = cmd.communicate()
    disklines = result[0].decode('utf-8').rstrip()

    disklinesarray = disklines.splitlines()
    disklines = []
    for line in disklinesarray:
        disklines.append(line)

    for line in disklines:
        if 'tmpfs' in line:
            continue;

        parts = line.split()
        if len(parts) != 6:
            continue;

        print('disk', parts[5])
    print()

    # --- network interface:
#    netlines = subprocess.check_output(['/usr/sbin/ifconfig'], stderr=subprocess.STDOUT)
    cmd = subprocess.Popen(['/sbin/ifconfig'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = cmd.communicate()
    netlines = result[0].decode('utf-8').rstrip()
    netlinesarray = str(netlines).splitlines()
    netlines = []
    for line in netlinesarray:
        netlines.append(line)

    counter = 0
    outlines = ''
    for line in netlines:
        if 'RUNNING' in line:
            parts = line.split()
            if parts[0] != 'lo:':
                outlines += 'network ' + str(parts[0][:-1]) + '\n'
                counter += 1

    if counter == 0:
        print('# !!! no running network interfaces found !!!')
        print()
    elif counter > 1:
        print('# network: choose one:')
        print(outlines)
    else:
        print('# network:')
        print(outlines)

    # --- available services:
    print('# services: please edit:')
    print('#')
    print('# from /etc/init.d:')

    svclines = glob.glob('/etc/init.d/*')
    for svc in svclines:
        if len(svc) > 0:
            print('service', os.path.basename(svc))

    svclines = glob.glob('/etc/systemd/system/*.service')
    print('#')
    print('# from /etc/systemd/system:')
    for svc in svclines:
        if len(svc) > 0:
            print('service', os.path.basename(svc))

    print()

    # --- the end:
    print('# EOF:')

# -----------------------------------------------------------------------------
# main part of the program:
# -----------------------------------------------------------------------------
if __name__ == '__main__':
    """If they give us a -c or --create, create a .ini file.
       If they give us anything else, print a usage message.
       Otherwise, create a Diag instance and display what we find.
    """
    fl_cpu = True
    fl_dsk = True
    fl_mem = True
    fl_net = True
    fl_png = True
    fl_svc = True
    fl_ful = True

    iam = sys.argv.pop(0)

    # check for flags:
    while len(sys.argv) > 0:
        arg = sys.argv.pop(0)

        # do the .ini file creation thing:
        if arg == '--create':
            create_ini()
            sys.exit(0)

        # if they want a different .ini file:
        if arg == '-i':
            g_ini_file = sys.argv.pop(0)
            continue

        # do the help thing:
        if arg == '-h' or arg == '-?' or arg == '--help':
            print(iam, 'usage:')
            print('    --create to output a new .ini file')
            print('    -i <alternate ini file> to use a different .ini file')
            print('    -c for CPU info')
            print('    -d for disk info')
            print('    -m for memory/swap info')
            print('    -n for network info')
            print('    -p to ping all known systems')
            print('    -s to check all services')
            sys.exit(0)

        if arg.startswith('-'):
            sys.argv.append(arg)

        # all the others:
        if '-c' not in sys.argv:
            fl_cpu = False
            fl_ful = False

        if '-d' not in sys.argv:
            fl_dsk = False
            fl_ful = False

        if '-m' not in sys.argv:
            fl_mem = False
            fl_ful = False

        if '-n' not in sys.argv:
            fl_net = False
            fl_ful = False

        if '-p' not in sys.argv:
            fl_png = False
            fl_ful = False

        if '-s' not in sys.argv:
            fl_svc = False
            fl_ful = False

        # ignore any other flags we find, carry on
        break

    broken = False
    diag = Diag()

#    lclhost = subprocess.check_output(['/usr/bin/hostname'], stderr=subprocess.STDOUT)
    cmd = subprocess.Popen(['/bin/hostname'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    result = cmd.communicate()
    lclhost = result[0].decode('utf-8').rstrip() # single-line response needs rstrip()

    if diag.sysname != lclhost:
        # we can do better here with proper string formatting:
        print("system_name entry '" + diag.sysname + \
                "' not the same as '" + lclhost + "'")
    else:
        print('system:    ', diag.sysname)

    print('OS version:', diag.os_version)
    print('uptime:    ', diag.uptime)
    print('date/time: ', diag.datestamp)
    print()

    # only do these on a full output:
    if fl_ful == True:
        print('disk_count:', diag.disk_count)
        print('network:   ', diag.net_interface)
        print()

    if fl_dsk == True:
        print('Disks:')
        diag.disk_print()
        print()

    if fl_cpu == True:
        print('CPU loads:')
        diag.cpus_print()
        print()

    if fl_mem == True:
        print('Memory and Swap space:')
        diag.swapmem_print()
        print()

    if fl_net == True:
        print('Network info:')
        diag.network_print()
        print()

    if fl_png == True:
        print('Sysping:', end=' ')
        if len(diag.netping_lines) == 0:
            print('OK')
        else:
            print()
            for l in diag.netping_lines:
                print(l)
        print()

    if fl_svc == True:
        print('Services:')
        svccount = len(diag.services)
        running   = svccount
        notrunning = 0
        unknown = 0

        for svc in diag.services:
            x = diag.services[svc].split()
            if len(x) > 0:
                if 'running...' in x:
                    print('    ', diag.services[svc])
                    continue

                if 'not' in x or 'stopped' in x:
                    notrunning += 1
                    print('    ', diag.services[svc])
                    continue;

                if 'unknown' in x:
                    unknown += 1
                    print('    ', diag.services[svc])
                    continue;

                if 'Usage:' in x:
                    print('EDIT:', svc, 'in sysdiag.ini')
                    continue

                print('     svc', svc, ':', diag.services[svc])
                continue

        if notrunning == 0:
            print('    all', str(running) + ' services are running')
        else:
            print()
            if notrunning == 1:
                print('    1 service is down')
            else:
                print(str(notrunning).rjust(5), 'services are down')

            if unknown == 1:
                print('    1 service is unknown')
            else:
                print(str(unknown).rjust(5), 'services are unknown')

            print(str(running).rjust(5), 'services are running')

        print()

    print()

    """ use this when we want to examine the dictionaries:
    pp = pprint.PrettyPrinter(indent=4)
    print
    print 'CPU dictionary:'
    pp.pprint(diag.cpus)
    print
    print 'disks dictionary:'
    pp.pprint(diag.disks)
    print
    print 'memory dictionary:'
    pp.pprint(diag.memory)
    print
    print 'network dictionary:'
    pp.pprint(diag.network)
    print
    print 'swap dictionary:'
    pp.pprint(diag.swapinfo)
    print
    print 'services dictionary:'
    pp.pprint(diag.services)
    print
#   """

# -----------------------------------------------------------------------------
# 
# -----------------------------------------------------------------------------

# EOF:
