import pytest
import rostest.util as u
from rostest.util import SSH

pytestmark = pytest.mark.skipif(u.arch != 'amd64', reason='amd64 network setup impossible to replicate for arm64')

cloud_config_path = './tests/integration/assets/test_10/cloud-config.yml'

net_args_arch = {'amd64': ['-net', 'nic,vlan=0,model=virtio'],
                 'arm64': ['-device', 'virtio-net-device']}
net_args_arch['arm'] = net_args_arch['arm64']
net_args = net_args_arch[u.arch]


@pytest.fixture(scope="module")
def qemu(request):
    q = u.run_qemu(request,
                   run_args=['--cloud-config', cloud_config_path] +
                   net_args + net_args + net_args + net_args + net_args + net_args + net_args)
    u.flush_out(q.stdout)
    return q


def test_network_interfaces_conf(qemu):
    SSH(qemu).check_call('''cat > test-merge << "SCRIPT"
set -x -e

ip link show dev br0
ip link show dev br0.100 | grep br0.100@br0
ip link show dev eth1.100 | grep 'master br0'

SCRIPT
sudo bash test-merge
    '''.strip())


def test_network_dns_conf(qemu):
    SSH(qemu).check_call('''cat > test-merge << "SCRIPT"
set -x -e

cat /etc/resolv.conf | grep "search mydomain.com example.com"
cat /etc/resolv.conf | grep "nameserver 208.67.222.123"
cat /etc/resolv.conf | grep "nameserver 208.67.220.123"

SCRIPT
sudo bash test-merge
    '''.strip())


def test_network_dns_ros_set(qemu):
    SSH(qemu).check_call('''
set -x -e

sudo ros config set rancher.network.dns.search '[a,b]'
if [ "$(sudo ros config get rancher.network.dns.search)" == "- a
 - b

 " ]; then
    sudo ros config get rancher.network.dns.search
    exit 1
 fi
    '''.strip())
