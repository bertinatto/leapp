from leappto.driver.ssh import SSHDriver
from leappto import AbstractMachineProvider, MachineType, Machine, Disk, \
        Package, OperatingSystem, Installation


def inspect_machine(driver, shallow):
    cmd = """python -c 'import platform; print chr(0xa).join(platform.linux_distribution()[:2])'"""
    _, output, _ = driver.exec_command(cmd)
    distro, version = output.read().strip().replace('\r', '').split('\n', 1)
    cmd = """python -c 'import socket; print socket.gethostname()'"""
    _, output, _ = driver.exec_command(cmd)
    hostname = output.read().strip()
    cmd = "/sbin/ip -4 -o addr list | grep -E 'e(th|ns)' | sed 's/.*inet \\([0-9\\.]\\+\\)\\/.*$/\\1/g'\n"
    _, output, stderr = driver.exec_command(cmd)
    ips = [i.strip() for i in output.read().split('\n') if i.strip()]
    packages = []
    if not shallow:
        cmd = "python -c \"import rpm, json; print json.dumps([(app['name'], " + \
                "'{e}:{v}-{r}.{a}'.format(e=app['epoch'] or 0, v=app['version'], " + \
                "a=app['arch'], r=app['release'])) for app in rpm.ts().dbMatch()])\""
        _, output, _ = driver.exec_command(cmd)
        packages = [Package(e[0], e[1]) for e in json.loads(output.read())]
    return (ips, hostname, Installation(OperatingSystem(distro, version), packages))


class SSHMachine(Machine):
    def __init__(self, host, user=None, port=22, shallow_scan=True):
        self._driver = SSHDriver(host, user, port)
        self._driver.connect()
        ips, hostname, installation, packages = ([], host, None, [])
        try:
            ips, hostname, installation, packages = inspect_machine(self._driver, shallow_scan)
        except ValueError:
            raise
        super(Machine, self).__init__(host, hostname, ips, 'x86_64', MachineType.SSH, [], hostname, installation, None)


