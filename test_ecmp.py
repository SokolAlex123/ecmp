
import subprocess
import time
import signal
import pytest

def ns_exec(ns, cmd):
    full_cmd = ["ip", "netns", "exec", ns, "bash", "-c", cmd]
    return subprocess.check_output(full_cmd, stderr=subprocess.DEVNULL).decode()


def send_icmp_from_ns1(src_ip, dst_ip="192.168.100.1"):
    cmd = f"python3 -c \'from scapy.all import IP, ICMP, send; send(IP(src=\"{src_ip}\", dst=\"{dst_ip}\")/ICMP(), verbose=0, iface=\"veth1\")\'"

    ns_exec("ns1", cmd)

@pytest.fixture(scope="function")
def dump_interfaces():
    def _dump_args(source=''):
        if source:
            filter_expr = f"icmp and icmp[0] == 8 and src host {source}"
            filter_expr_error = f"icmp and icmp[0] == 3 and src host {source}"
        else:
            filter_expr = "icmp and icmp[0] == 8"
            filter_expr_error = "icmp and icmp[0] == 3"

        p2 = subprocess.Popen(
            ["tcpdump", "-i", "veth2_root", "-c", "100", "-n", filter_expr],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )

        p3 = subprocess.Popen(
            ["tcpdump", "-i", "veth3_root", "-c", "100", "-n", filter_expr],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )

        p2_error = subprocess.Popen(
            ["tcpdump", "-i", "veth2_root", "-c", "100", "-n", filter_expr_error],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )

        p3_error = subprocess.Popen(
            ["tcpdump", "-i", "veth3_root", "-c", "100", "-n", filter_expr_error],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )

        return p2, p3, p2_error, p3_error

    yield _dump_args

def test_same_source_ip_always_same_path(dump_interfaces):
    src = "10.0.1.2"

    p2, p3, p2_error, p3_error = dump_interfaces(src)

    time.sleep(0.5)

    for _ in range(10):
        send_icmp_from_ns1(src)
        time.sleep(0.05)

    time.sleep(1.5)

    p2.send_signal(signal.SIGINT)
    p3.send_signal(signal.SIGINT)
    p2_error.send_signal(signal.SIGINT)
    p3_error.send_signal(signal.SIGINT)

    out2, _ = p2.communicate(timeout=3)
    out3, _ = p3.communicate(timeout=3)
    out2_error, _ = p2_error.communicate(timeout=3)
    out3_error, _ = p3_error.communicate(timeout=3)

    diff2 = len(out2.decode().splitlines())
    diff3 = len(out3.decode().splitlines())
    diff2_error = len(out2_error.decode().splitlines())
    diff3_error = len(out3_error.decode().splitlines())

    print(f"ICMP через veth2: {diff2}, через veth3: {diff3}, "
          f"icmp-error veth2: {diff2_error}, icmp-error veth3: {diff3_error}")
    
    assert (diff2 - diff2_error == 10 and diff3 - diff3_error == 0) or (diff2 - diff2_error == 0 and diff3 - diff3_error == 10), \
    "Одинаковые source IP должны всегда выбирать один путь"

def test_different_source_ips_use_both_paths(dump_interfaces):
    p2, p3, p2_error, p3_error = dump_interfaces()  

    time.sleep(0.5)

    for i in range(10, 20):
        send_icmp_from_ns1(f"10.0.1.{i}")
        time.sleep(0.05)

    time.sleep(1.5)

    p2.send_signal(signal.SIGINT)
    p3.send_signal(signal.SIGINT)
    p2_error.send_signal(signal.SIGINT)
    p3_error.send_signal(signal.SIGINT)

    out2, _ = p2.communicate(timeout=3)
    out3, _ = p3.communicate(timeout=3)

    out2_error, _ = p2_error.communicate(timeout=3)
    out3_error, _ = p3_error.communicate(timeout=3)

    diff2 = len(out2.decode().splitlines())
    diff3 = len(out3.decode().splitlines())
    diff2_error = len(out2_error.decode().splitlines())
    diff3_error = len(out3_error.decode().splitlines())

    print(f"ICMP через veth2: {diff2}, через veth3: {diff3}, "
          f"icmp-error veth2: {diff2_error}, icmp-error veth3: {diff3_error}")

    assert diff2 - diff2_error > 0 and diff3 - diff3_error > 0, "Оба пути должны быть задействованы"

