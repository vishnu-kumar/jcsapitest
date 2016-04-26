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

import testtools
import time
from jcsapi.tests.functional import base
from jcsapi.tests.functional import config

CONF = config.CONF


class VolumeTest(base.EC2TestCase):

    VPC_CIDR = '10.16.0.0/20'
    vpc_id = None
    SUBNET_CIDR = '10.16.0.0/24'
    subnet_id = None

    @classmethod
    @base.safe_setup
    def setUpClass(cls):
        super(VolumeTest, cls).setUpClass()

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
        	resp, data = cls.vpc_client.CreateSubnet(VpcId=cls.vpc_id,
                                             CidrBlock=cls.SUBNET_CIDR)
        	cls.assertResultStatic(resp, data)
        	cls.subnet_id = data['Subnet']['SubnetId']
        	cls.addResourceCleanUpStatic(cls.vpc_client.DeleteSubnet,
                                     SubnetId=cls.subnet_id)
      	  	#cls.get_subnet_waiter().wait_available(cls.subnet_id)
		time.sleep(1)
    """
    def _create_vpc_subnet(self):
	if(VolumeTest.vpc_id == None):
		resp, data = cls.vpc_client.CreateVpc(CidrBlock=cls.VPC_CIDR)
        	cls.assertResultStatic(resp, data)
        	cls.vpc_id = data['Vpc']['VpcId']
        	cls.addResourceCleanUpStatic(cls.vpc_client.DeleteVpc, VpcId=cls.vpc_id)
        	cls.get_vpc_waiter().wait_available(cls.vpc_id)

        	aws_zone = CONF.aws.aws_zone
        	resp, data = cls.vpc_client.CreateSubnet(VpcId=cls.vpc_id,
                                             CidrBlock=cls.SUBNET_CIDR,
                                             AvailabilityZone=aws_zone)
        	cls.assertResultStatic(resp, data)
        	cls.subnet_id = data['Subnet']['SubnetId']
        	cls.addResourceCleanUpStatic(cls.vpc_client.DeleteSubnet,
                                     SubnetId=cls.subnet_id)
        	cls.get_subnet_waiter().wait_available(cls.subnet_id)

    """
    def test_create_delete_volume(self):
        kwargs = {
            'Size': 1
        }
        resp, data = self.ec2_client.CreateVolume(*[], **kwargs)
	self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        volume_id = data['VolumeId']
        res_clean = self.addResourceCleanUp(self.ec2_client.DeleteVolume,
                                            VolumeId=volume_id)

        self.get_volume_waiter().wait_available(volume_id)

        self.assertEqual(1, data['Size'])
        self.assertIsNotNone(data['CreateTime'])

        resp, data = self.ec2_client.DeleteVolume(VolumeId=volume_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean)
        self.get_volume_waiter().wait_delete(volume_id)

        resp, data = self.ec2_client.DescribeVolumes(VolumeIds=volume_id)
        self.assertEqual(404, resp.status_code)
        self.assertEqual('InvalidVolume.NotFound', data['Error']['Code'])

	
        #resp, data = self.ec2_client.DeleteVolume(VolumeId=volume_id)
        #self.assertEqual(400, resp.status_code)
        #self.assertEqual('InvalidVolume.NotFound', data['Error']['Code'])

    def test_describe_volumes(self):
        kwargs = {
            'Size': 1
        }
        resp, data = self.ec2_client.CreateVolume(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        volume_id = data['VolumeId']
        res_clean = self.addResourceCleanUp(self.ec2_client.DeleteVolume,
                                            VolumeId=volume_id)
        self.get_volume_waiter().wait_available(volume_id)

        resp, data = self.ec2_client.CreateVolume(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        volume_id_ext = data['VolumeId']
        res_clean_ext = self.addResourceCleanUp(self.ec2_client.DeleteVolume,
                                                VolumeId=volume_id_ext)
        self.get_volume_waiter().wait_available(volume_id_ext)

        resp, data = self.ec2_client.DescribeVolumes(VolumeIds=volume_id)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(data['Volumes']))

        volume = data['Volumes'][0]
        self.assertEqual(volume_id, volume['VolumeId'])
        self.assertEqual(1, volume['Size'])

        resp, data = self.ec2_client.DeleteVolume(VolumeId=volume_id_ext)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean_ext)
        self.get_volume_waiter().wait_delete(volume_id_ext)

        resp, data = self.ec2_client.DeleteVolume(VolumeId=volume_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean)
        self.get_volume_waiter().wait_delete(volume_id)

    def __test_describe_volume_status(self):
        kwargs = {
            'Size': 1
        }
        resp, data = self.ec2_client.CreateVolume(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        volume_id = data['VolumeId']
        res_clean = self.addResourceCleanUp(self.ec2_client.DeleteVolume,
                                            VolumeId=volume_id)

        self.get_volume_waiter().wait_available(volume_id)

        resp, data = self.ec2_client.DescribeVolumeStatus(VolumeIds=[volume_id])
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(data['VolumeStatuses']))

        volume_status = data['VolumeStatuses'][0]
        self.assertIn('Actions', volume_status)
        self.assertIn('Events', volume_status)
        self.assertIn('VolumeStatus', volume_status)

        resp, data = self.ec2_client.DeleteVolume(VolumeId=volume_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean)
        self.get_volume_waiter().wait_delete(volume_id)

    def test_attach_detach_volume(self):
        instance_type = CONF.aws.instance_type
        image_id = CONF.aws.image_id
        if not image_id:
            raise self.skipException('aws image_id does not provided')

        kwargs = {
            'ImageId': image_id,
            'InstanceTypeId': instance_type,
            'InstanceCount': 1,
	    'SubnetId' : self.subnet_id
        }
        resp, data = self.ec2_client.RunInstances(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']
        clean_i = self.addResourceCleanUp(self.ec2_client.TerminateInstances,
                                          InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id,
                                                  final_set=('running'))

	self.set_delete_on_termination_flag_root_vol(instance_id)
        kwargs = {
            'Size': 1
        }
        resp, data = self.ec2_client.CreateVolume(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        volume_id = data['VolumeId']
        clean_v = self.addResourceCleanUp(self.ec2_client.DeleteVolume,
                                          VolumeId=volume_id)
        self.get_volume_waiter().wait_available(volume_id)

        kwargs = {
            'Device': '/dev/vdb',
            'InstanceId': instance_id,
            'VolumeId': volume_id,
        }
        resp, data = self.ec2_client.AttachVolume(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        clean_vi = self.addResourceCleanUp(self.ec2_client.DetachVolume,
                                           VolumeId=volume_id)
        self.get_volume_attachment_waiter().wait_available(
            volume_id, final_set=('attached'))

        resp, data = self.ec2_client.DescribeVolumes(VolumeIds=volume_id)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(data['Volumes']))
        volume = data['Volumes'][0]
        self.assertEqual('in-use', volume['State'])
        """
	self.assertEqual(1, len(volume['Attachments']))
        attachment = volume['Attachments'][0]
        if CONF.aws.run_incompatible_tests:
            self.assertFalse(attachment['DeleteOnTermination'])
        self.assertIsNotNone(attachment['Device'])
        self.assertEqual(instance_id, attachment['InstanceId'])
        self.assertEqual(volume_id, attachment['VolumeId'])
	"""
        resp, data = self.ec2_client.DescribeInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(data.get('Instances', [])))
        bdms = data['Instances'][0]['BlockDeviceMappings']
        self.assertNotEmpty(bdms)
        self.assertIn('DeviceName', bdms[0])

        resp, data = self.ec2_client.DetachVolume(VolumeId=volume_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(clean_vi)
	self.get_volume_waiter().wait_available(volume_id)

        resp, data = self.ec2_client.DescribeVolumes(VolumeIds=volume_id)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(data['Volumes']))
        volume = data['Volumes'][0]
        self.assertEqual('available', volume['State'])
        self.assertEqual(0, len(volume['Attachments']))

        resp, data = self.ec2_client.DeleteVolume(VolumeId=volume_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(clean_v)
        self.get_volume_waiter().wait_delete(volume_id)

        resp, data = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(clean_i)
        self.get_instance_waiter().wait_delete(instance_id)

    def __test_attaching_stage(self):
        instance_type = CONF.aws.instance_type
        image_id = CONF.aws.image_id
        if not image_id:
            raise self.skipException('aws image_id does not provided')

        kwargs = {
            'ImageId': image_id,
            'InstanceTypeId': instance_type,
            'InstanceCount': 1,
	    'SubnetId' : self.subnet_id
        }
        resp, data = self.ec2_client.RunInstances(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']
        clean_i = self.addResourceCleanUp(self.ec2_client.TerminateInstances,
                                          InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id,
                                                  final_set=('running'))

        resp, data = self.ec2_client.CreateVolume(
            AvailabilityZone=CONF.aws.aws_zone, Size=1)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        volume_id = data['VolumeId']
        clean_v = self.addResourceCleanUp(self.ec2_client.DeleteVolume,
                                          VolumeId=volume_id)
        self.get_volume_waiter().wait_available(volume_id)

        kwargs = {
            'Device': '/dev/vdb',
            'InstanceId': instance_id,
            'VolumeId': volume_id,
        }
        resp, data = self.ec2_client.AttachVolume(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        clean_vi = self.addResourceCleanUp(self.ec2_client.DetachVolume,
                                           VolumeId=volume_id)
        self.assertEqual('attaching', data['State'])

        if CONF.aws.run_incompatible_tests:
            bdt = self.get_instance_bdm(instance_id, '/dev/vdb')
            self.assertIsNotNone(bdt)
            self.assertEqual('attaching', bdt['Status'])

        self.get_volume_attachment_waiter().wait_available(
            volume_id, final_set=('attached'))

        resp, data = self.ec2_client.DetachVolume(VolumeId=volume_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(clean_vi)
        self.get_volume_attachment_waiter().wait_delete(volume_id)

        resp, data = self.ec2_client.DeleteVolume(VolumeId=volume_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(clean_v)
        self.get_volume_waiter().wait_delete(volume_id)

        resp, data = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(clean_i)
        self.get_instance_waiter().wait_delete(instance_id)

    def __test_delete_detach_attached_volume(self):
        instance_type = CONF.aws.instance_type
        image_id = CONF.aws.image_id
        if not image_id:
            raise self.skipException('aws image_id does not provided')

        kwargs = {
            'ImageId': image_id,
            'InstanceTypeId': instance_type,
            'InstanceCount': 1,
	    'SubnetId' : self.subnet_id
        }
        resp, data = self.ec2_client.RunInstances(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']
        clean_i = self.addResourceCleanUp(self.ec2_client.TerminateInstances,
                                          InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id,
                                                  final_set=('running'))

        kwargs = {
            'Size': 1
        }
        resp, data = self.ec2_client.CreateVolume(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        volume_id = data['VolumeId']
        clean_v = self.addResourceCleanUp(self.ec2_client.DeleteVolume,
                                          VolumeId=volume_id)
        self.get_volume_waiter().wait_available(volume_id)

        kwargs = {
            'Device': '/dev/vdb',
            'InstanceId': instance_id,
            'VolumeId': volume_id,
        }
        resp, data = self.ec2_client.AttachVolume(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        clean_vi = self.addResourceCleanUp(self.ec2_client.DetachVolume,
                                           VolumeId=volume_id)
        self.get_volume_attachment_waiter().wait_available(
            volume_id, final_set=('attached'))

        resp, data = self.ec2_client.AttachVolume(*[], **kwargs)
        self.assertEqual(400, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual('VolumeInUse', data['Error']['Code'])

        kwargs['Device'] = '/dev/sdi'
        resp, data = self.ec2_client.AttachVolume(*[], **kwargs)
        self.assertEqual(400, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual('VolumeInUse', data['Error']['Code'])

        resp, data = self.ec2_client.DeleteVolume(VolumeId=volume_id)
        self.assertEqual(400, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual('VolumeInUse', data['Error']['Code'])

        resp, data = self.ec2_client.DetachVolume(VolumeId=volume_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(clean_vi)
        self.get_volume_attachment_waiter().wait_delete(volume_id)

        resp, data = self.ec2_client.DetachVolume(VolumeId=volume_id)
        self.assertEqual(400, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual('IncorrectState', data['Error']['Code'])

        resp, data = self.ec2_client.DeleteVolume(VolumeId=volume_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(clean_v)
        self.get_volume_waiter().wait_delete(volume_id)

        resp, data = self.ec2_client.DetachVolume(VolumeId=volume_id)
        self.assertEqual(400, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual('InvalidVolume.NotFound', data['Error']['Code'])

        resp, data = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(clean_i)
        self.get_instance_waiter().wait_delete(instance_id)

    def test_volume_auto_termination_swithed_off(self):
        instance_type = CONF.aws.instance_type
        image_id = CONF.aws.image_id
        if not image_id:
            raise self.skipException('aws image_id does not provided')

        kwargs = {
            'ImageId': image_id,
            'InstanceTypeId': instance_type,
            'InstanceCount': 1,
	    'SubnetId' : self.subnet_id
        }
        resp, data = self.ec2_client.RunInstances(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']
        clean_i = self.addResourceCleanUp(self.ec2_client.TerminateInstances,
                                          InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id,
                                                  final_set=('running'))
	self.set_delete_on_termination_flag_root_vol(instance_id)
        kwargs = {
            'Size': 1
        }
        resp, data = self.ec2_client.CreateVolume(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        volume_id = data['VolumeId']
        clean_v = self.addResourceCleanUp(self.ec2_client.DeleteVolume,
                                          VolumeId=volume_id)
        self.get_volume_waiter().wait_available(volume_id)

        kwargs = {
            'Device': '/dev/vdb',
            'InstanceId': instance_id,
            'VolumeId': volume_id,
        }
        resp, data = self.ec2_client.AttachVolume(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.addResourceCleanUp(self.ec2_client.DetachVolume, VolumeId=volume_id)
        self.get_volume_attachment_waiter().wait_available(
            volume_id, final_set=('attached'))

        resp, data = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(clean_i)
        self.get_instance_waiter().wait_delete(instance_id)

        resp, data = self.ec2_client.DescribeVolumes(VolumeIds=volume_id)
        self.assertEqual(200, resp.status_code)
        self.assertEqual(1, len(data['Volumes']))
        volume = data['Volumes'][0]
        self.assertEqual('available', volume['State'])
        if 'Attachments' in volume:
            self.assertEqual(0, len(volume['Attachments']))

        resp, data = self.ec2_client.DeleteVolume(VolumeId=volume_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(clean_v)
        self.get_volume_waiter().wait_delete(volume_id)

    #@testtools.skipUnless(CONF.aws.run_incompatible_tests,
    #                      "ModifyInstanceAttribute is not implemented")
    def test_volume_auto_termination_swithed_on(self):
        instance_type = CONF.aws.instance_type
        image_id = CONF.aws.image_id
        if not image_id:
            raise self.skipException('aws image_id does not provided')

        kwargs = {
            'ImageId': image_id,
            'InstanceTypeId': instance_type,
            'InstanceCount': 1,
	    'SubnetId' : self.subnet_id
        }
        resp, data = self.ec2_client.RunInstances(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']
        clean_i = self.addResourceCleanUp(self.ec2_client.TerminateInstances,
                                          InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id,
                                                  final_set=('running'))
	self.set_delete_on_termination_flag_root_vol(instance_id)
        kwargs = {
            'Size': 1
        }
        resp, data = self.ec2_client.CreateVolume(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        volume_id = data['VolumeId']
        self.addResourceCleanUp(self.ec2_client.DeleteVolume, VolumeId=volume_id)
        self.get_volume_waiter().wait_available(volume_id)

        kwargs = {
            'Device': '/dev/vdb',
            'InstanceId': instance_id,
            'VolumeId': volume_id,
        }
        resp, data = self.ec2_client.AttachVolume(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.addResourceCleanUp(self.ec2_client.DetachVolume, VolumeId=volume_id)
        self.get_volume_attachment_waiter().wait_available(
            volume_id, final_set=('attached'))

        resp, data = self.ec2_client.UpdateDeleteOnTerminationFlag(VolumeId=volume_id, DeleteOnTermination="True")
	self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
 
	resp, data = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(clean_i)
        self.get_instance_waiter().wait_delete(instance_id)

        resp, data = self.ec2_client.DescribeVolumes(VolumeIds=volume_id)
        self.assertEqual(404, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual('InvalidVolume.NotFound', data['Error']['Code'])
