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


class InstanceTypesTest(base.EC2TestCase):

    ExpectednstanceTypes = [
        {
            "InstanceTypeRAM": "3.75", 
            "InstanceTypeCPU": "1", 
            "InstanceTypeId": "c1.small"
        }, 
        {
            "InstanceTypeRAM": "15.0", 
            "InstanceTypeCPU": "4", 
            "InstanceTypeId": "c1.large"
        }, 
        {
            "InstanceTypeRAM": "7.5", 
            "InstanceTypeCPU": "2", 
            "InstanceTypeId": "c1.medium"
        }, 
        {
            "InstanceTypeRAM": "30.0", 
            "InstanceTypeCPU": "8", 
            "InstanceTypeId": "c1.xlarge"
        }
    ]
    def test_describe_instance_types(self):
        resp, data = self.ec2_client.DescribeInstanceTypes()
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        for actualType, expectedType in zip(data['InstanceTypes'], self.ExpectednstanceTypes) :
		self.assertEqual(actualType['InstanceTypeId'], expectedType["InstanceTypeId"])
		self.assertEqual(actualType['InstanceTypeCPU'], expectedType["InstanceTypeCPU"])
		self.assertEqual(actualType['InstanceTypeRAM'], expectedType["InstanceTypeRAM"])
