#!/usr/bin/env python3
import json, os, re, socketserver, subprocess, sys

CONFIG_PATH = '/config/wg_confs'
CONFIG_FILE = 'wg0.conf'

PEER_NAMES = {}

def normalize_public_key(key: str) -> str:
    return re.sub(r'\s+', '', key.strip()).ljust(44, '=')[:44]

def load_peer_names() -> dict:
    cfg = os.path.join(CONFIG_PATH, CONFIG_FILE)

    if not os.path.exists(cfg):
        return {}

    peers = {}

    with open(cfg) as wg_cfg:
        in_peer_block = False
        current_name = None

        for line in wg_cfg:
            line = line.strip()

            if line.startswith("[Peer]"):
                in_peer_block = True
                current_name = None
                continue

            if in_peer_block:
                if line.startswith("#"):
                    current_name = line.lstrip("#").split("_")[1].strip()
                elif line.lower().startswith("publickey"):
                    public_key = normalize_public_key(line.split("=", 1)[1].strip())
                    if current_name:
                        peers[public_key] = current_name
                elif not line or line.startswith("["):
                    in_peer_block = False
                    current_name = None

    return peers

def fetch_wireguard_stats() -> dict:
    data = {}
    for line in subprocess.run(['wg', 'show', 'all', 'dump'], capture_output=True, text=True, check=True).stdout.strip().splitlines():
        parts = line.split('\t')
        if len(parts) < 9:
            continue
        iface, pk = parts[0], normalize_public_key(parts[1])
        data.setdefault(iface, {'peers': []})['peers'].append({
            'public_key': parts[1],
            'peer_name': PEER_NAMES.get(pk, ''),
            'endpoint': parts[3] if parts[3] != '(none)' else '',
            'allowed_ips': parts[4],
            'latest_handshake': int(parts[5]) if parts[5] != '0' else 0,
            'rx': int(parts[6]),
            'tx': int(parts[7])
        })
    return json.dumps(data).encode('utf-8')


class WGHandler(socketserver.BaseRequestHandler):
    def handle(self):
        data = fetch_wireguard_stats()
        self.request.sendall(b"HTTP/1.1 200 OK\r\n"
                             b"Content-Type: application/json\r\n"
                             b"Content-Length: %d\r\n\r\n%s"
                             % (len(data), data))

if __name__ == "__main__":
    PEER_NAMES = load_peer_names();
    with socketserver.TCPServer(('0.0.0.0', '51822'), WGHandler) as server:
        server.serve_forever()
