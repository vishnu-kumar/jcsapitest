# Copyright 2015 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

import netaddr
from oslo_log import log
from tempest_lib.common.utils import data_utils
import time
from jcsapi.tests.functional import base
from jcsapi.tests.functional import config
from jcsapi.tests.functional.scenario import base as scenario_base
from jcsapi.tests.functional import ssh
import sys,os
CONF = config.CONF
LOG = log.getLogger(__name__)

instance_types = {"c1.small": {   
            		"InstanceTypeRAM": 3.75,
            		"InstanceTypeCPU": "1",
            		"InstanceTypeId": "c1.small"
        		},
        	 "c1.large" :{	   
            		"InstanceTypeRAM": 15,
            		"InstanceTypeCPU": "4",
            		"InstanceTypeId": "c1.large"
        		},
        	 "c1.medium" :{
            		"InstanceTypeRAM": 7.5,
            		"InstanceTypeCPU": "2",
            		"InstanceTypeId": "c1.medium"
        		},
        	 "c1.xlarge":{
            		"InstanceTypeRAM": 30,
            		"InstanceTypeCPU": "8",
            		"InstanceTypeId": "c1.xlarge"
        	}
		}
imagesData = {"jmi-bf82713e" : {"name":"Windows Server 2012"},
                  "jmi-57bf447e" : {"name":"Ubuntu 14.04"},
                  "jmi-09b48b3b" : {"name":"CentOS release 6.7 (Final)"},
                  "jmi-96ef2b43" : {"name":"CentOS Linux release 7.2.1511 (Core)"}
               }
	
class Instance_Sshable_ExecuteCommand_VPCTest(scenario_base.BaseScenarioTest):

    @classmethod
    @base.safe_setup
    def setUpClass(cls):
        super(Instance_Sshable_ExecuteCommand_VPCTest, cls).setUpClass()
        if not CONF.aws.image_id:
            raise cls.skipException('aws image_id does not provided')

    def _open_sg(self, group_id):
	kwargs = {
            'GroupId': group_id,
            'IpPermissions': [{
                'IpProtocol': 'icmp',
                'FromPort': -1,
                'ToPort': -1,
                'IpRanges': [{
                    'CidrIp': '0.0.0.0/0'
                }],
            },
            {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{
                    'CidrIp': '0.0.0.0/0'
                }],
            }
           ]
        }
	try:
        	resp, data = self.vpc_client.AuthorizeSecurityGroupIngress(*[], **kwargs)
        	self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
	except:
		pass

    def _test_instances(self, subnet_size, image_id, instance_type_id, image_user):
        cidr = netaddr.IPNetwork('10.20.0.0/8')
        cidr.prefixlen = subnet_size
        vpc_id, subnet_id = self.create_vpc_and_subnet(str(cidr))
        #gw_id = self.create_and_attach_internet_gateway(vpc_id)
        #self.prepare_vpc_default_security_group(vpc_id)
        #self.prepare_route(vpc_id, gw_id)

        key_name = data_utils.rand_name('testkey')
        pkey = self.create_key_pair(key_name)

        first_ip = str(netaddr.IPAddress(cidr.first + 4))
        last_ip = str(netaddr.IPAddress(cidr.last - 1))
        instance_id1 = self.run_instance(KeyName=key_name, SubnetId=subnet_id, ImageId=image_id, InstanceTypeId=instance_type_id)

	resp, data = self.ec2_client.DescribeInstances(InstanceIds=[instance_id1])
	sg_id = data["Instances"][0]["SecurityGroups"][0]["GroupId"]
	
	self._open_sg(sg_id)

	"""
        instance_id2 = self.run_instance(KeyName=key_name, SubnetId=subnet_id,
            PrivateIpAddress=last_ip)
        instance = self.get_instance(instance_id1)
        self.assertEqual(first_ip, instance['PrivateIpAddress'])
        instance = self.get_instance(instance_id2)
        self.assertEqual(last_ip, instance['PrivateIpAddress'])
	"""
	
        ip_address = self.get_instance_ip(instance_id1)
        ssh_client = ssh.Client(ip_address, image_user, pkey=pkey)

        waiter = base.EC2Waiter(ssh_client.exec_command)
        waiter.wait_no_exception('ping %s -c 1' % ip_address)
	
	waiter.wait_no_exception('/bin/uname')

	xcpu = instance_types[instance_type_id]["InstanceTypeCPU"]
	xarch = "x86_64"
        self.verify_cpu_arch_info(ssh_client, xcpu, xarch)

        xos_version = imagesData[image_id]["name"]
	self.verify_os_info(ssh_client, xos_version)

	xmem = instance_types[instance_type_id]["InstanceTypeRAM"]*1048576
	self.verify_memory_info(ssh_client, xmem)

	#import time
	#time.sleep(10)
	#output  = ssh_client.exec_command("/bin/uname")
	#self.assertEqual("Linux\n", output, "SSH command /bin/uname not executed successfully")

	self.ec2_client.TerminateInstances(InstanceIds=[instance_id1])
	time.sleep(5)
	self.get_instance_waiter().wait_delete(instance_id1)

    """
	imagesData = {"jmi-bf82713e" : {"name":"Windows Server 2012"},
                  "jmi-57bf447e" : {"name":"Ubuntu 14.04"},
                  "jmi-09b48b3b" : {"name":"CentOS 6.7"},
                  "jmi-96ef2b43" : {"name":"CentOS 7"}
                }
    """
    """
	cat /proc/meminfo | head -2
	MemTotal:       30884480 kB
	MemFree:         7374152 kB
    """

    """
	 lsb_release -a
	No LSB modules are available.
	Distributor ID:	Ubuntu
	Description:	Ubuntu 14.04.3 LTS
	Release:	14.04
	Codename:	trusty
    """
    """
    nproc   returns 8
    """
    """
     lscpu
Architecture:          x86_64
CPU op-mode(s):        32-bit, 64-bit
Byte Order:            Little Endian
CPU(s):                8
On-line CPU(s) list:   0-7
Thread(s) per core:    1
Core(s) per socket:    1
Socket(s):             8
NUMA node(s):          1
Vendor ID:             GenuineIntel
CPU family:            6
Model:                 42
Stepping:              1
CPU MHz:               2593.748
BogoMIPS:              5187.49
Virtualization:        VT-x
Hypervisor vendor:     KVM
Virtualization type:   full
L1d cache:             32K
L1i cache:             32K
L2 cache:              4096K
NUMA node0 CPU(s):     0-7
    """ 
    def verify_memory_info(self, ssh_client, xmem):
	output  = ssh_client.exec_command("/bin/cat /proc/meminfo").split("\n")
	mem = int(output[0].split("MemTotal:")[1].split("kB")[0].strip())
	ex_mem = xmem
	self.assertEqual(abs(ex_mem-mem)*100/ex_mem < 5, True, 
			"actual Mem = %s, ExpectedMem=%s delta=%f "%(mem, ex_mem, abs(ex_mem-mem)*100/ex_mem))

    def verify_cpu_arch_info(self, ssh_client, xcpus, xarch):
        output  = ssh_client.exec_command("/usr/bin/lscpu").split("\n")
	arch = output[0].split("Architecture:")[1].strip()
        self.assertEqual(arch, xarch)
	cpus = output[3].split("CPU(s):")[1].strip()
	self.assertEqual(cpus, xcpus)

    """
	['Distributor ID:\tUbuntu',
 'Description:\tUbuntu 14.04.3 LTS',
 'Release:\t14.04',
 'Codename:\ttrusty',
 '']
    """
    def get_centos_info(self, ssh_client):
	output = ssh_client.exec_command("cat /etc/centos-release").split("\n")

	return output
    def get_ubuntuos_info(self, ssh_client):
        output = ssh_client.exec_command("/usr/bin/lsb_release -a").split("\n")
	return output
    def verify_os_info(self, ssh_client, xos_version):
	if("centos" in xos_version.lower()):
		output = self.get_centos_info(ssh_client)
		self.assertEqual(output[0].strip(), xos_version)
	elif ( "ubuntu" in xos_version.lower()):
		output  = ssh_client.exec_command("/usr/bin/lsb_release -a").split("\n")
        	#self.assertEqual(output, "")
		dist = output[0].split("Distributor ID:\t")[1].strip()
		version = output[2].split("Release:\t")[1].strip()
		os_version = dist + " " + version
		self.assertEqual(os_version, xos_version)

    def test_ubuntu_instance(self):
	self._test_instances(16, "jmi-57bf447e", "c1.small", "ubuntu")	
    def test_centos_67_instance(self):
        self._test_instances(16, "jmi-09b48b3b", "c1.large", "centos")
    def test_centos_7_instance(self):
        self._test_instances(16, "jmi-96ef2b43", "c1.xlarge", "centos")
    def __test_instances_in_min_subnet(self):
        self._test_instances(28)

    def __test_instances_in_max_subnet(self):
        self._test_instances(16)
