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
from wsmancmd import *
import testtools
CONF = config.CONF
LOG = log.getLogger(__name__)

class Instance_Win_Pingable_ExecuteCommand_VPCTest(scenario_base.BaseScenarioTest):

    @classmethod
    @base.safe_setup
    def setUpClass(cls):
        super(Instance_Win_Pingable_ExecuteCommand_VPCTest, cls).setUpClass()
        if not CONF.aws.image_id:
            raise cls.skipException('aws image_id does not provided')


    def _open_sg(self, group_id):
	kwargs_icmp = {
	  	'GroupId': group_id,
		'IpPermissions': [
            		{
                	'IpProtocol': 'icmp',
                	'FromPort': -1,
                	'ToPort': -1,
                	'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
            		}
		]
	}
	kwargs_ssh = {
                'GroupId': group_id,
                'IpPermissions': [  
                        {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                        }
                ]
        }

	kwargs_win_rdp = {
                'GroupId': group_id,
                'IpPermissions': [
                        {
                        'IpProtocol': 'tcp',
                        'FromPort': 5984,
                        'ToPort': 5987,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                        }
                ]
        }
	kwargs_win_winms = {
                'GroupId': group_id,
                'IpPermissions': [
                        {
                        'IpProtocol': 'tcp',
                        'FromPort': 3389,
                        'ToPort': 3389,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                        }
                ]
        }
	rules = [kwargs_win_rdp, kwargs_win_winms, kwargs_icmp, kwargs_ssh]
	for rule in rules:
		#resp, data = self.vpc_client.AuthorizeSecurityGroupIngress(*[], **kwargs)
		try:
			LOG.info("Authorize sg=%s"%rule)
        		resp, data = self.vpc_client.AuthorizeSecurityGroupIngress(*[], **rule)
        		self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
		except:
			pass

    def _get_password_data(self, instance_id, timeout=300):
	import time
	resp, data = self.ec2_client.GetPasswordData(InstanceId=instance_id)
	#self.assertEqual(data, "")
	st = time.time()
	while(True):
		LOG.info("Encrypted Password is : %s"%data["PasswordData"]) 
		if(data["PasswordData"] != None):			
			return data["PasswordData"]
		time.sleep(10)
		if(time.time() - st >300):
			raise testtools.TestCase.failureException('State change timeout exceeded! '
                    		'(%ds) While waiting for password data to be not None' %timeout)
		resp, data = self.ec2_client.GetPasswordData(InstanceId=instance_id)


    def _decrypt_password(self, password, privateKeyFile):
	 from decrypt_pswd import *
	 keyFile = open(privateKeyFile, "r")
         keyLines = keyFile.readlines()
         try:
                key = RSA.importKey(keyLines)
         except ValueError, ex:
                print "Could not import SSH Key (Is it an RSA key? Is it password protected?): %s" % ex
	 return decryptPassword(key,password)

    def get_password(self, instance_id):
	return self._decrypt_password(self._get_password_data(instance_id), "/home/vishnu/.ssh/id_rsa")

    def _test_instances(self, subnet_size):
        cidr = netaddr.IPNetwork('10.20.0.0/8')
        cidr.prefixlen = subnet_size
        vpc_id, subnet_id = self.create_vpc_and_subnet(str(cidr))

	"""
	key_name = data_utils.rand_name('testkey')
       	pkey = self.create_key_pair(key_name)
	"""
	LOG.info("Luanching windows instance")
	key_name = "windows_key_1"
	windows_image_id = "jmi-bf82713e"
        instance_id1 = self.run_instance(KeyName=key_name, SubnetId=subnet_id, ImageId=windows_image_id)

	resp, data = self.ec2_client.DescribeInstances(InstanceIds=[instance_id1])
	sg_id = data["Instances"][0]["SecurityGroups"][0]["GroupId"]
	
	self._open_sg(sg_id)

        ip_address = self.get_instance_ip(instance_id1)

	"""
	python wsmancmd.py -U https://10.140.213.50:5986/wsman -u Admin -p alRdtG4DzEVyi7QvpP5F 'powershell -Command Get-NetIPConfiguration'
        """
	
	url = "https://%s:5986/wsman"%ip_address
	user = "Admin"
	password  = self.get_password(instance_id1)

	LOG.info("wsman uri =%s"%url)
	LOG.info("User=%s Decrypted Password is : %s"%(user,password))

	time.sleep(60)
	cmd = ["powershell -Command Get-NetIPConfiguration"]
	LOG.info("Executing command = %s"%str(cmd))
        (std_out, std_err, status_code) = run_wsman_cmd(url, user, password, cmd) 

	#self.assertEqual(std_err,"")
	self.assertEqual(status_code, 0, "status code not ok Couldnt execute powershell -Command Get-NetIPConfiguration")
	#self.assertEqual(std_out, "")
	
	"""
	output  = ssh_client.exec_command("/bin/uname")
	LOG.debug("ssh command /bin/uname output = %s"%output)
	self.assertEqual("Linux\n", output, "SSH command /bin/uname not executed successfully")
	"""

	"""
	self.ec2_client.TerminateInstances(InstanceIds=[instance_id1])
	time.sleep(5)
	self.get_instance_waiter().wait_delete(instance_id1)
	"""
    def __test_instances_in_min_subnet(self):
        self._test_instances(28)

    def test_instances_sshable_execute_command(self):
        self._test_instances(16)
