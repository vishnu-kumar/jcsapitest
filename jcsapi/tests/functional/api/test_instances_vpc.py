# Copyright 2014 OpenStack Foundation
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

from oslo_log import log
import testtools
import time
from jcsapi.tests.functional import base
from jcsapi.tests.functional import config

CONF = config.CONF
LOG = log.getLogger(__name__)


class InstanceInVPCTest(base.EC2TestCase):

    VPC_CIDR = '10.16.0.0/20'
    vpc_id = None
    SUBNET_CIDR = '10.16.0.0/24'
    subnet_id = None

    @classmethod
    @base.safe_setup
    def setUpClass(cls):
        super(InstanceInVPCTest, cls).setUpClass()
        if not base.TesterStateHolder().get_vpc_enabled():
            raise cls.skipException('VPC is disabled')
        if not CONF.aws.image_id:
            raise cls.skipException('aws image_id does not provided')
	if(CONF.aws.subnet_id != None):
                cls.subnet_id = CONF.aws.subnet_id
		cls.vpc_id = CONF.aws.vpc_id
        else:
        	resp, data = cls.vpc_client.CreateVpc(CidrBlock=cls.VPC_CIDR)
        	cls.assertResultStatic(resp, data)
        	cls.vpc_id = data['Vpc']['VpcId']
        	cls.addResourceCleanUpStatic(cls.vpc_client.DeleteVpc, VpcId=cls.vpc_id)
        	#cls.get_vpc_waiter().wait_available(cls.vpc_id)
		time.sleep(1)
        	aws_zone = CONF.aws.aws_zone
        	resp, data = cls.vpc_client.CreateSubnet(VpcId=cls.vpc_id,
                                             CidrBlock=cls.SUBNET_CIDR)
        	cls.assertResultStatic(resp, data)
        	cls.subnet_id = data['Subnet']['SubnetId']
        	cls.addResourceCleanUpStatic(cls.vpc_client.DeleteSubnet,
                                     SubnetId=cls.subnet_id)
		time.sleep(1)
        #cls.get_subnet_waiter().wait_available(cls.subnet_id)
    def describe(self):
	resp, data = self.ec2_client.DescribeInstances()

    def delete_all_instances(self):
	resp, data = self.ec2_client.DescribeInstances()
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        #reservations = data.get('Instances', [])
        #self.assertNotEmpty(reservations)
        #instances = reservations[0].get('Instances', [])

	for instance in data["Instances"]:
		instanceId = instance['InstanceId']
		self.ec2_client.TerminateInstances(InstanceIds=[instanceId])
	
    def test_create_delete_instance(self):
        instance_type = CONF.aws.instance_type
        image_id = CONF.aws.image_id

        resp, data = self.ec2_client.RunInstances(
            ImageId=image_id, InstanceTypeId=instance_type, InstanceCount=1,
            SubnetId=self.subnet_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']
        res_clean = self.addResourceCleanUp(self.ec2_client.TerminateInstances,
                                            InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id,
                                                  final_set=('running'))

	self.set_delete_on_termination_flag_root_vol(instance_id)

        resp, data = self.ec2_client.DescribeInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instances = data.get('Instances', [])
        self.assertNotEmpty(instances)
        instance = instances[0]
        self.assertEqual(self.vpc_id, instance['VpcId'])
        self.assertEqual(self.subnet_id, instance['SubnetId'])

        resp, data = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean)
        self.get_instance_waiter().wait_delete(instance_id)

    def test_describe_instances_filter(self):
        instance_type = CONF.aws.instance_type
        image_id = CONF.aws.image_id

        resp, data = self.ec2_client.RunInstances(
            ImageId=image_id, InstanceTypeId=instance_type, InstanceCount=1,
            SubnetId=self.subnet_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']
        res_clean = self.addResourceCleanUp(self.ec2_client.TerminateInstances,
                                            InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id,
                                                  final_set=('running'))

	self.set_delete_on_termination_flag_root_vol(instance_id)

        resp, data = self.ec2_client.DescribeInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assert_instance(data, instance_id)
        instances = data['Instances']
        private_dns = instances[0]['PrivateDnsName']
        private_ip = instances[0]['PrivateIpAddress']

        resp, data = self.ec2_client.DescribeInstances(
            Filters=[{'Name': 'private-ip-address', 'Values': ['1.2.3.4']}])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual(0, len(data['Instances']))

        resp, data = self.ec2_client.DescribeInstances(
            Filters=[{'Name': 'private-ip-address', 'Values': [private_ip]},  {"Name":'subnet-id', "Values":[self.subnet_id]}])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assert_instance(data, instance_id)

        #by private dns
        resp, data = self.ec2_client.DescribeInstances(
            Filters=[{'Name': 'private-dns-name', 'Values': ['fake.com']}])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual(0, len(data['Instances']))

        resp, data = self.ec2_client.DescribeInstances(
            Filters=[{'Name': 'private-dns-name', 'Values': [private_dns]},  {"Name":'subnet-id', "Values":[self.subnet_id]}])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assert_instance(data, instance_id)

        #  by subnet id
        resp, data = self.ec2_client.DescribeInstances(
            Filters=[{'Name': 'subnet-id', 'Values': ['subnet-0']}])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual(0, len(data['Instances']))

        resp, data = self.ec2_client.DescribeInstances(
            Filters=[{'Name': 'subnet-id', 'Values': [self.subnet_id]}])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assert_instance(data, instance_id)

        #  by vpc id
        resp, data = self.ec2_client.DescribeInstances(
            Filters=[{'Name': 'vpc-id', 'Values': ['vpc-0']}])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual(0, len(data['Instances']))

        resp, data = self.ec2_client.DescribeInstances(
            Filters=[{'Name': 'vpc-id', 'Values': [self.vpc_id]}])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assert_instance(data, instance_id)

        resp, data = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean)
        self.get_instance_waiter().wait_delete(instance_id)

    def assert_instance(self, data, instance_id):
        instances = data.get('Instances', [])
        self.assertNotEmpty(instances)
	instanceIds = []
	for instance in instances:
		instanceIds.append(instance['InstanceId'])
	
        self.assertEqual(instance_id in instanceIds, True, "InstanceId=%s doesnt exists"%instance_id)

    def test_create_instance_with_private_ip(self):
        ip = '10.20.0.12'

        kwargs = {
            'ImageId': CONF.aws.image_id,
            'InstanceTypeId': CONF.aws.instance_type,
            'InstanceCount': 1,
            'SubnetId': self.subnet_id,
            'PrivateIpAddress': ip
        }
        resp, data = self.ec2_client.RunInstances(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']
        res_clean = self.addResourceCleanUp(self.ec2_client.TerminateInstances,
                                            InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id,
                                                  final_set=('running'))
	self.set_delete_on_termination_flag_root_vol(instance_id)

        instance = self.get_instance(instance_id)
        self.assertEqual(ip, instance['PrivateIpAddress'])

        resp, data = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean)
        self.get_instance_waiter().wait_delete(instance_id)

    def test_create_instance_with_invalid_params(self):
        kwargs = {
            'ImageId': CONF.aws.image_id,
            'InstanceTypeId': CONF.aws.instance_type,
            'InstanceCount': 1,
            'PrivateIpAddress': '10.20.0.2'
        }
        resp, data = self.ec2_client.RunInstances(*[], **kwargs)
        if resp.status_code == 200:
            self.addResourceCleanUp(
                self.ec2_client.TerminateInstances,
                InstanceIds=[data['Instances'][0]['InstanceId']])
        self.assertEqual(400, resp.status_code)
        #self.assertEqual('InvalidParameterCombination', data['Error']['Code']) #TBD Vishnu Kumar Check error Code
        self.assertEqual('InvalidParameterValue', data['Error']['Code'])

        kwargs = {
            'ImageId': CONF.aws.image_id,
            'InstanceTypeId': CONF.aws.instance_type,
            'InstanceCount': 1,
            'SubnetId': self.subnet_id,
            'PrivateIpAddress': '11.20.0.12'
        }
        resp, data = self.ec2_client.RunInstances(*[], **kwargs)
        if resp.status_code == 200:
            self.addResourceCleanUp(
                self.ec2_client.TerminateInstances,
                InstanceIds=[data['Instances'][0]['InstanceId']])
        self.assertEqual(400, resp.status_code)
        self.assertEqual('InvalidParameterValue', data['Error']['Code'])

