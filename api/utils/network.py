import fcntl, socket, struct
from uuid import getnode as get_mac

def get_mac_address():
    mac = get_mac()
    return ':'.join(("%012X" % mac)[i:i + 2] for i in range(0, 12, 2))

