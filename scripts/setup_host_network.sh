#!/bin/bash
# Run on the HOST (not in Docker). Sets a fixed IP on the wired NIC used for the lidar.
# Usage: ./scripts/setup_host_network.sh [interface] [host_ip]
#   e.g. ./scripts/setup_host_network.sh enp5s0 192.168.1.5
set -e

IFACE="${1:-}"
HOST_IP="${2:-192.168.1.5}"
CON_NAME="livox"

if [ -z "$IFACE" ]; then
  echo "Wired interfaces on this computer:"
  ip -br link | awk '$1 ~ /^(en|eth)/ {print "  " $1 "  " $2}'
  echo
  echo "Usage: $0 <interface> [host_ip]   e.g. $0 enp5s0 192.168.1.5"
  exit 1
fi

if nmcli -t -f NAME con show | grep -qx "$CON_NAME"; then
  echo "Connection '$CON_NAME' exists, updating it."
  sudo nmcli con mod "$CON_NAME" connection.interface-name "$IFACE" \
       ipv4.method manual ipv4.addresses "$HOST_IP/24" ipv6.method disabled
else
  sudo nmcli con add type ethernet ifname "$IFACE" con-name "$CON_NAME" \
       ipv4.method manual ipv4.addresses "$HOST_IP/24" ipv6.method disabled
fi
sudo nmcli con up "$CON_NAME"
ip -br addr show "$IFACE"
echo
echo "Done. Undo with: sudo nmcli con delete $CON_NAME"
