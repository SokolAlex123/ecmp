#!/bin/bash
set -e

echo "Настройка ECMP-стенда..."

ip netns del ns1 2>/dev/null || true
ip netns del ns2 2>/dev/null || true
ip netns del ns3 2>/dev/null || true

ip netns add ns1
ip netns add ns2
ip netns add ns3

ip link add veth1 type veth peer name veth1_root
ip link add veth2 type veth peer name veth2_root
ip link add veth3 type veth peer name veth3_root

ip link set veth1 netns ns1
ip link set veth2 netns ns2
ip link set veth3 netns ns3

ip netns exec ns1 ip addr add 10.0.1.2/24 dev veth1
ip netns exec ns1 ip link set veth1 up
ip netns exec ns1 ip link set lo up
ip addr add 10.0.1.1/24 dev veth1_root
ip link set veth1_root up

ip netns exec ns2 ip addr add 10.0.2.2/24 dev veth2
ip netns exec ns2 ip link set veth2 up
ip netns exec ns2 ip link set lo up
ip addr add 10.0.2.1/24 dev veth2_root
ip link set veth2_root up

ip netns exec ns3 ip addr add 10.0.3.2/24 dev veth3
ip netns exec ns3 ip link set veth3 up
ip netns exec ns3 ip link set lo up
ip addr add 10.0.3.1/24 dev veth3_root
ip link set veth3_root up


sysctl -w net.ipv4.ip_forward=1 >/dev/null

sysctl -w net.ipv4.fib_multipath_hash_policy=1 >/dev/null

sysctl -w net.ipv4.fib_multipath_use_neigh=0 >/dev/null

ip route del 192.168.100.1/32 2>/dev/null || true 

ip route add 192.168.100.1/32 proto static\
    nexthop via 10.0.2.2 dev veth2_root weight 1 \
    nexthop via 10.0.3.2 dev veth3_root weight 1

ip netns exec ns1 ip route del 192.168.100.1/32 2>/dev/null || true

ip netns exec ns1 ip route add 192.168.100.1/32 via 10.0.1.1 dev veth1

echo "Стенд готов."

echo "Проверка маршрута:"

ip route show 192.168.100.1

