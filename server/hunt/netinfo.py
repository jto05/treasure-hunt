
"""
netinfo.py uses the ip address of a client to look up
its corresponding MAC address in one way:

dnsmasq.leases: dnsmasq hands out DHCP leases to clients
connecting over wifi, which associates an IP address
with the MAC address. Reading the dnsmasq.leases lets us
find that MAC address.


Caveat: dependent on dnsmasq service :( if dnsmasq crashes and restarts
or something... new leases would be dished out, breaking the 
registered teams
"""

def ip_to_mac(ip, leases_path= "/var/lib/misc/dnsmasq.leases"):
    return _from_leases(ip, leases_path)


# dnsmasq.leases format, one lease per line, space-separated:
  #
  #   1790800000 a4:5e:60:12:34:56 10.42.0.23 iPhone-Red 01:a4:5e:60:12:34:56
  #   ^expiry    ^mac (fields[1])  ^ip (fields[2])  ^hostname ^client-id
  #
  # expiry: unix timestamp the lease expires at (or 0 = infinite)
  # hostname and client-id may be "*" if the device didn't report  one

def _strip_hwtype_prefix(mac):
    # some clients' DHCP client-id (type byte + address) ends up in the
    # hwaddr column instead of a bare address -- a real Ethernet/Wi-Fi
    # MAC is 6 groups, so drop a leading 7th group if present
    parts = mac.split(":")
    if len(parts) == 7:
        parts = parts[1:]
    return ":".join(parts)


def _from_leases(ip, path):
    # attempt to open file and write contents to lines
    try:
        with open(path) as f:
            lines = f.readlines()
    except FileNotFoundError:
        return None

    for line in lines:
        fields = line.split() # split fields at each line

        # check if fields is a sufficient length (>3) to have
        # an ip address
        if len(fields) >= 3 and fields[2] == ip:
            return _strip_hwtype_prefix(fields[1].lower()) # fields[1] is the MAC address

    return None
