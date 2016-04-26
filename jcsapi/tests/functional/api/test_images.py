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

from tempest_lib.common.utils import data_utils
import testtools

from jcsapi.tests.functional import base
from jcsapi.tests.functional import config

CONF = config.CONF

class ImageTest(base.EC2TestCase):

    VPC_CIDR = '10.16.0.0/20'
    vpc_id = None
    SUBNET_CIDR = '10.16.0.0/24'
    subnet_id = None

    imagesData = {"jmi-bf82713e" : {"name":"Windows Server 2012"},
                  "jmi-57bf447e" : {"name":"Ubuntu 14.04"},
                  "jmi-09b48b3b" : {"name":"CentOS 6.7"},
                  "jmi-96ef2b43" : {"name":"CentOS 7"}
                }

    #This test data need to be in some test files . Vishnu
    """
    "State": "available",
    "Architecture": "x86_64",
    "Public": true,
    "ImageType": "machine"
    """

    @classmethod
    @base.safe_setup
    def setUpClass(cls):
        super(ImageTest, cls).setUpClass()
        if not base.TesterStateHolder().get_vpc_enabled():
            raise cls.skipException('VPC is disabled')
        if not CONF.aws.image_id:
            raise cls.skipException('aws image_id does not provided')

	"""
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
    def test_describe_images_with_imageId(self):
        image_id = CONF.aws.image_id
        resp, data = self.ec2_client.DescribeImages(ImageIds=[image_id])
	self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual(1, len(data['Images']))

	self.assertEqual(image_id, data['Images'][0]['ImageId'])

    def test_describe_images(self):
	resp, data = self.ec2_client.DescribeImages()
	minImages = 0
	for image in data["Images"]:
		if(self.imagesData.has_key(image["ImageId"])):
			self.assertEqual(image["Name"], self.imagesData[image["ImageId"]]["name"])
			self.assertEqual(image["State"], "available")
			self.assertEqual(image["Architecture"], "x86_64")
			self.assertEqual(image["ImageType"], "machine")
			minImages = minImages+1
	self.assertEqual(len(self.imagesData.keys()), minImages, "Missing One of images : %s "%self.imagesData.keys())
			
		



"""
imagesSet>
    <item>
      <blockDeviceMapping>
        <deviceName>/dev/vda</deviceName>
        <deleteOnTermination>false</deleteOnTermination>
        <volumeSize>8</volumeSize>
        <snapshotId>snap-00000001</snapshotId>
      </blockDeviceMapping>
      <name>Ubuntu14.04</name>
      <isPublic>true</isPublic>
      <imageId>ami-8843cebc</imageId>
      <imageState>available</imageState>
      <architecture>x86_64</architecture>
      <imageType>machine</imageType>
    </item>
  </imagesSet>

"""
