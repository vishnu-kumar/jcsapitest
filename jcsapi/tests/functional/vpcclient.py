from botocore import session

def get_vpc_client():
	connection_data = {
            'config_file': (None, 'AWS_CONFIG_FILE', None),
            'region': ('region', 'BOTO_DEFAULT_REGION', "RegionOne"),
        }

	sess = session.get_session(connection_data)
        sess.set_debug_logger()
	sess.set_credentials("aws_access_key_test_user_2", "aws_access_key_test_user_2")
        vpcclient = sess.create_client("ec2",region_name="RegionOne", api_version='2016-03-01',
					endpoint_url="https://vpc.ind-west-1.staging.jiocloudservices.com:8788",
                                        aws_access_key_id="aws_access_key_test_user_2", 
					aws_secret_access_key="aws_access_key_test_user_2")

	print vpcclient.describe_vpcs()

def get_ec2_client():
        sess = session.get_session()
        sess.set_debug_logger()
        ec2client = sess.create_client("ec2",region_name="RegionOne", api_version='2016-03-01',
                                        endpoint_url="http://10.140.214.69:8788",
                                        aws_access_key_id="aws_access_key_test_user_2",
                                        aws_secret_access_key="aws_access_key_test_user_2")

        print ec2client.describe_images()
if __name__ == "__main__":
	try:
		get_vpc_client()
	except:
		pass

	try:
		get_ec2_client()
	except:
		pass
