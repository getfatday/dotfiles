# WireGuard — station-wg

This directory holds only this README in the repo. `wg-station install` fetches
`station-wg.conf` from 1Password at runtime and writes it here (`chmod 600`,
dir `chmod 700`). Never commit `station-wg.conf` or any `*.conf` — see the
`.gitignore` next to this file.

Server facts:
- Server: "station-wg" on a UniFi UDR7, at the apartment
- Protocol: WireGuard over UDP 51820
- Tunnel subnet: 192.168.2.0/24
- DDNS name: and5-apt.duckdns.org

Notes:
- `.local` mDNS names don't resolve over the tunnel. Use LAN IPs, or resolve
  via the UDR7's DNS: `dig @192.168.2.1 <host>.localdomain`.
- Use `wg-station install|up|down|status|check` to manage the tunnel.
