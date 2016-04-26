# 2016.03.07 14:17:10 IST
import time
from oslo_log import log
from tempest_lib.common.utils import data_utils
import testtools
from jcsapi.tests.functional import base
from jcsapi.tests.functional import config
CONF = config.CONF
LOG = log.getLogger(__name__)


class InstanceTest(base.EC2TestCase):
    VPC_CIDR = '10.16.0.0/20'
    vpc_id = None
    SUBNET_CIDR = '10.16.0.0/24'
    subnet_id = None
    image_id = CONF.aws.image_id

    @classmethod
    @base.safe_setup
    def setUpClass(cls):
        super(InstanceTest, cls).setUpClass()


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


    def test_create_delete_instance(self):
        instance_type = CONF.aws.instance_type
        image_id = CONF.aws.image_id
        (resp, data,) = self.ec2_client.RunInstances(ImageId=image_id, InstanceTypeId=instance_type, \
						InstanceCount=1, SubnetId=self.subnet_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']

        res_clean = self.addResourceCleanUp(self.ec2_client.TerminateInstances, InstanceIds=[instance_id])
        self.assertEqual(1, len(data['Instances']))
        self.get_instance_waiter().wait_available(instance_id, final_set='running')
	self.set_delete_on_termination_flag_root_vol(instance_id)
        (resp, data,) = self.ec2_client.DescribeInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instances = data.get('Instances', [])
        self.assertEqual(1, len(instances))
        (resp, data,) = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean)
        self.get_instance_waiter().wait_delete(instance_id)


    def test_describe_instances_filter(self):
        instance_type = CONF.aws.instance_type
        image_id = CONF.aws.image_id
        (resp, data,) = self.ec2_client.RunInstances(ImageId=image_id, InstanceCount=1, SubnetId=self.subnet_id, InstanceTypeId=instance_type)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']

        res_clean = self.addResourceCleanUp(self.ec2_client.TerminateInstances, InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id, final_set='running')
        self.set_delete_on_termination_flag_root_vol(instance_id)
	(resp, data,) = self.ec2_client.DescribeInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self._assert_instance(data, instance_id)
        instances = data['Instances']
        private_dns = instances[0]['PrivateDnsName']
        private_ip = instances[0]['PrivateIpAddress']
        (resp, data,) = self.ec2_client.DescribeInstances(InstanceIds=['i-0'])
        self.assertEqual(400, resp.status_code)
        self.assertEqual('InvalidInstanceID.NotFound', data['Error']['Code'])
        (resp, data,) = self.ec2_client.DescribeInstances(Filters=[{'Name': 'private-ip-address',
          'Values': ['1.2.3.4']}])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual(0, len(data['Instances']))
        (resp, data,) = self.ec2_client.DescribeInstances(Filters=[{'Name': 'private-ip-address',
          'Values': [private_ip]}, {"Name":'subnet-id', "Values":[self.subnet_id]}])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self._assert_instance(data, instance_id)
        (resp, data,) = self.ec2_client.DescribeInstances(Filters=[{'Name': 'private-dns-name',
          'Values': ['fake.com']}])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual(0, len(data['Instances']))
        (resp, data,) = self.ec2_client.DescribeInstances(Filters=[{'Name': 'private-dns-name',
          'Values': [private_dns]}, {"Name":'subnet-id', "Values":[self.subnet_id]}])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self._assert_instance(data, instance_id)
        (resp, data,) = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean)
        self.get_instance_waiter().wait_delete(instance_id)



    def _assert_instance(self, data, instance_id):
	LOG.info("instaces data : %s"%data)
        reservations = data.get('Instances', [])
        self.assertNotEmpty(reservations)
        instances = reservations
        self.assertNotEmpty(instances)
        self.assertEqual(instance_id, instances[0]['InstanceId'])



    def __test_get_password_data_and_console_output(self):
        instance_type = CONF.aws.instance_type
        image_id = CONF.aws.image_id
        (resp, data,) = self.ec2_client.RunInstances(ImageId=image_id, InstanceTypeId=instance_type, InstanceCount=1, SubnetId=self.subnet_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']
        res_clean = self.addResourceCleanUp(self.ec2_client.TerminateInstances, InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id, final_set='running')
        self.set_delete_on_termination_flag_root_vol(instance_id)
	(resp, data,) = self.ec2_client.GetPasswordData(InstanceId=instance_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual(instance_id, data['InstanceId'])
        self.assertIsNotNone(data['Timestamp'])
        self.assertIn('PasswordData', data)
        waiter = base.EC2Waiter(self.ec2_client.GetConsoleOutput)
        waiter.wait_no_exception(InstanceId=instance_id)
        (resp, data,) = self.ec2_client.GetConsoleOutput(InstanceId=instance_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual(instance_id, data['InstanceId'])
        self.assertIsNotNone(data['Timestamp'])
        self.assertIn('Output', data)
        (resp, data,) = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean)
        self.get_instance_waiter().wait_delete(instance_id)



    def test_stop_start_reboot_instance(self):
        instance_type = CONF.aws.instance_type
        image_id = CONF.aws.image_id

        #RunInstances
	(resp, data,) = self.ec2_client.RunInstances(ImageId=image_id, InstanceTypeId=instance_type, InstanceCount=1, SubnetId=self.subnet_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']
	
        res_clean = self.addResourceCleanUp(self.ec2_client.TerminateInstances, InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id, final_set='running')
       	self.set_delete_on_termination_flag_root_vol(instance_id) 
	#StopInstances
	(resp, data,) = self.ec2_client.StopInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        if CONF.aws.run_incompatible_tests:
            instances = data['StoppingInstances']
            self.assertEqual(1, len(instances))
            instance = instances[0]
            self.assertEqual(instance_id, instance['InstanceId'])
            self.assertEqual('running', instance['PreviousState']['Name'])
            self.assertEqual('stopping', instance['CurrentState']['Name'])
        self.get_instance_waiter().wait_available(instance_id, final_set='stopped')

	#StartInstances
        (resp, data,) = self.ec2_client.StartInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
	self.get_instance_waiter().wait_available(instance_id, final_set='running')
	
	#RebootInstances
        (resp, data,) = self.ec2_client.RebootInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.get_instance_waiter().wait_available(instance_id, final_set='running')

        #TerminateInstances
	(resp, data,) = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean)
        self.get_instance_waiter().wait_delete(instance_id)



    #@testtools.skipUnless(CONF.aws.run_incompatible_tests, "Openstack doesn't assign public ip automatically for new instance")
    def __test_public_ip_is_assigned(self):
        """Is public IP assigned to launched instnace?"""
        instance_type = CONF.aws.instance_type
        image_id = CONF.aws.image_id
        (resp, data,) = self.ec2_client.RunInstances(ImageId=image_id, InstanceTypeId=instance_type, InstanceCount=1, SubnetId=self.subnet_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual(1, len(data['Instances']))
        instance_id = data['Instances'][0]['InstanceId']
        res_clean = self.addResourceCleanUp(self.ec2_client.TerminateInstances, InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id, final_set='running')
        instance = self.get_instance(instance_id)
        self.assertIsNotNone(instance.get('PublicIpAddress'))
        self.assertIsNotNone(instance.get('PrivateIpAddress'))
        self.assertNotEqual(instance.get('PublicIpAddress'), instance.get('PrivateIpAddress'))
        (resp, data,) = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean)
        self.get_instance_waiter().wait_delete(instance_id)


    def test_launch_instance_with_creating_blank_volume(self):
        """Launch instance with creating blank volume."""
        device_name = '/dev/vdb'
        instance_type = CONF.aws.instance_type
        (resp, data,) = self.ec2_client.RunInstances(ImageId=CONF.aws.image_id, InstanceTypeId=instance_type, \
					InstanceCount=1, SubnetId=self.subnet_id, 
					BlockDeviceMappings=[{'DeviceName': device_name,'VolumeSize': 1, 'DeleteOnTermination':True}])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        instance_id = data['Instances'][0]['InstanceId']
        res_clean = self.addResourceCleanUp(self.ec2_client.TerminateInstances, InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id, final_set='running')
	self.set_delete_on_termination_flag_root_vol(instance_id)

        bdt = self.get_instance_bdm(instance_id, device_name)
        self.assertIsNotNone(bdt)
        volume_id = bdt.get('VolumeId')
        self.assertIsNotNone(volume_id)
        #self.assertTrue(bdt['Ebs']['DeleteOnTermination'])
        (resp, data,) = self.ec2_client.DescribeVolumes(VolumeIds=volume_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual(1, len(data['Volumes']))
        volume = data['Volumes'][0]
        self.assertEqual(1, volume['Size'])
        (resp, data,) = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean)
        self.get_instance_waiter().wait_delete(instance_id)
    def test_create_root_volume_snapshot(self):
        """Create snapshot of root volume of EBS-backed instance."""
        resp, data = self.ec2_client.RunInstances(
            ImageId=self.image_id, InstanceTypeId=CONF.aws.instance_type,
            InstanceCount=1, SubnetId=self.subnet_id )
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual(1, len(data['Instances']))
        instance_id = data['Instances'][0]['InstanceId']
        res_clean = self.addResourceCleanUp(self.ec2_client.TerminateInstances,
                                            InstanceIds=[instance_id])
        self.get_instance_waiter().wait_available(instance_id,
                                                  final_set=('running'))

	self.set_delete_on_termination_flag_root_vol(instance_id)

        rootDeviceName= "/dev/vda"
        bdt = self.get_instance_bdm(instance_id, rootDeviceName)
        self.assertIsNotNone(bdt)
        volume_id = bdt.get('VolumeId')
        self.assertIsNotNone(volume_id)

        resp, data = self.ec2_client.StopInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.get_instance_waiter().wait_available(instance_id,
                                                  final_set=('stopped'))

        resp, data = self.ec2_client.DescribeVolumes(VolumeIds=volume_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.assertEqual(1, len(data['Volumes']))

        kwargs = {
            'VolumeId': data['Volumes'][0]['VolumeId'],
            'Description': 'Description'
        }
        resp, data = self.ec2_client.CreateSnapshot(*[], **kwargs)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        snapshot_id = data['SnapshotId']
        res_clean_s = self.addResourceCleanUp(self.ec2_client.DeleteSnapshot,
                                              SnapshotId=snapshot_id)
        self.get_snapshot_waiter().wait_available(snapshot_id, final_set=('completed'))

        resp, data = self.ec2_client.TerminateInstances(InstanceIds=[instance_id])
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean)
        self.get_instance_waiter().wait_delete(instance_id)

        resp, data = self.ec2_client.DeleteSnapshot(SnapshotId=snapshot_id)
        self.assertEqual(200, resp.status_code, base.EC2ErrorConverter(data))
        self.cancelResourceCleanUp(res_clean_s)
        #self.get_snapshot_waiter().wait_delete(snapshot_id) #Vishnu Need some clean way to wait for snapshot delete
	
