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

import time

from oslo_log import log
from tempest_lib.common.utils import data_utils

from jcsapi.tests.functional import base
from jcsapi.tests.functional import config

CONF = config.CONF
LOG = log.getLogger(__name__)
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class BaseScenarioTest(base.EC2TestCase):

    def run_instance(self, **kwargs):
        if(not kwargs.has_key("ImageId")):
		kwargs.setdefault('ImageId', CONF.aws.image_id)
        if(not kwargs.has_key("InstanceTypeId")):
		kwargs.setdefault('InstanceTypeId', CONF.aws.instance_type)
        kwargs['InstanceCount'] = 1
        resp, data = self.ec2_client.RunInstances(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']
        
	self.addResourceCleanUp(self.ec2_client.TerminateInstances,
                                InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id,
                                                  final_set=('running'))

	self.set_delete_on_termination_flag_root_vol(instance_id)

        return instance_id

    def get_instance_ip(self, instance_id):
        instance = self.get_instance(instance_id)
        public_ip = instance.get('PublicIpAddress')
        if public_ip:
            return public_ip

       	#alloc_id, public_ip = self.allocate_address('VpcId' in instance)
	alloc_id, public_ip  = self.get_fip()

        kwargs = {'InstanceId': instance_id}
        kwargs['AllocationId'] = alloc_id

        resp, data = self.vpc_client.AssociateAddress(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        
	self.addResourceCleanUp(self.vpc_client.DisassociateAddress,
                                    AssociationId=data['AssociationId'])

        return public_ip

    def get_fip(self):
	resp, data = self.vpc_client.DescribeAddresses()
	for address in data["Addresses"]:
		if(not address.has_key("AssociationId")):
			return address["AllocationId"], address["PublicIp"]

	return allocate_address(True)

    def allocate_address(self, is_vpc):
        kwargs = dict()
        kwargs['Domain'] = 'vpc'
        resp, data = self.vpc_client.AllocateAddress(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        alloc_id = data.get('AllocationId')
        public_ip = data['PublicIp']
        self.addResourceCleanUp(self.vpc_client.ReleaseAddress,
                                    AllocationId=alloc_id)

        return alloc_id, public_ip

    def create_key_pair(self, key_name):
        resp, data = self.ec2_client.CreateKeyPair(KeyName=key_name)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.addResourceCleanUp(self.ec2_client.DeleteKeyPair, KeyName=key_name)
        return data.get('KeyMaterial')

    def create_standard_security_group(self):
        name = data_utils.rand_name('sgName')
        desc = data_utils.rand_name('sgDesc')
        kwargs = {'GroupName': name, 'Description': desc}
        resp, data = self.vpc_client.CreateSecurityGroup(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.addResourceCleanUp(self.vpc_client.DeleteSecurityGroup,
                                GroupName=name)
        time.sleep(2)

        kwargs = {
            'GroupName': name,
            'IpPermissions': [{
                'IpProtocol': 'icmp',
                'FromPort': -1,
                'ToPort': -1,
                'IpRanges': [{
                    'CidrIp': '0.0.0.0/0'
                }],
            }, {
                'IpProtocol': 'tcp',
                'FromPort': 22,
                'ToPort': 22,
                'IpRanges': [{
                    'CidrIp': '0.0.0.0/0'
                }],
            }]
        }
        resp, data = self.vpc_client.AuthorizeSecurityGroupIngress(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))

        return name

    def prepare_vpc_default_security_group(self, vpc_id):
        resp, data = self.vpc_client.DescribeSecurityGroups(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(data['SecurityGroups']))
        group_id = data['SecurityGroups'][0]['GroupId']
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
        resp, data = self.vpc_client.AuthorizeSecurityGroupIngress(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))

    def prepare_route(self, vpc_id, gw_id):
        resp, data = self.vpc_client.DescribeRouteTables(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(data['RouteTables']))

        kwargs = {
            'DestinationCidrBlock': '0.0.0.0/0',
            'RouteTableId': data['RouteTables'][0]['RouteTableId'],
            'GatewayId': gw_id
        }
        resp, data = self.vpc_client.CreateRoute(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))

    def create_vpc_and_subnet(self, cidr):
        if(CONF.aws.subnet_id != None):
                return CONF.aws.vpc_id, CONF.aws.subnet_id
        else:
		resp, data = self.vpc_client.CreateVpc(CidrBlock=cidr)
        	self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        	vpc_id = data['Vpc']['VpcId']
        	self.addResourceCleanUp(self.vpc_client.DeleteVpc, VpcId=vpc_id)
        	#self.get_vpc_waiter().wait_available(vpc_id)

        	resp, data = self.vpc_client.CreateSubnet(VpcId=vpc_id, CidrBlock=cidr)
        	self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        	subnet_id = data['Subnet']['SubnetId']
        	self.addResourceCleanUp(self.vpc_client.DeleteSubnet, SubnetId=subnet_id)

        	return vpc_id, subnet_id

    def create_network_interface(self, subnet_id):
        resp, data = self.vpc_client.CreateNetworkInterface(SubnetId=subnet_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        ni_id = data['NetworkInterface']['NetworkInterfaceId']
        self.addResourceCleanUp(self.vpc_client.DeleteNetworkInterface,
                                NetworkInterfaceId=ni_id)
        self.get_network_interface_waiter().wait_available(ni_id)

        return ni_id

    def create_and_attach_internet_gateway(self, vpc_id):
        resp, data = self.vpc_client.CreateInternetGateway()
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        gw_id = data['InternetGateway']['InternetGatewayId']
        self.addResourceCleanUp(self.vpc_client.DeleteInternetGateway,
                                InternetGatewayId=gw_id)
        resp, data = self.vpc_client.AttachInternetGateway(VpcId=vpc_id,
                                                       InternetGatewayId=gw_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.addResourceCleanUp(self.vpc_client.DetachInternetGateway,
                                VpcId=vpc_id,
                                InternetGatewayId=gw_id)

        return gw_id
