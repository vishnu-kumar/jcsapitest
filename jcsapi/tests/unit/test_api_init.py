# Copyright 2014
# The Cloudscaling Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uuid

from boto import exception as boto_exception
from cinderclient import exceptions as cinder_exception
from glanceclient.common import exceptions as glance_exception
from keystoneclient import exceptions as keystone_exception
import mock
from neutronclient.common import exceptions as neutron_exception
from novaclient import exceptions as nova_exception
from oslotest import base as test_base

from ec2api import api
from ec2api.api import apirequest
from ec2api import exception
from ec2api.tests.unit import fakes_request_response as fakes
from ec2api.tests.unit import matchers
from ec2api.tests.unit import tools
from ec2api import wsgi


class ApiInitTestCase(test_base.BaseTestCase):

    def setUp(self):
        super(ApiInitTestCase, self).setUp()

        controller_patcher = mock.patch('ec2api.api.cloud.VpcCloudController')
        self.controller_class = controller_patcher.start()
        self.controller = self.controller_class.return_value
        self.addCleanup(controller_patcher.stop)

        self.fake_context = mock.NonCallableMock(request_id=str(uuid.uuid4()))

        ec2_request = apirequest.APIRequest('FakeAction', 'fake_v1',
                                            {'Param': 'fake_param'})
        self.environ = {'REQUEST_METHOD': 'FAKE',
                        'ec2.request': ec2_request,
                        'ec2api.context': self.fake_context}
        self.request = wsgi.Request(self.environ)
        self.application = api.Executor()

    def test_execute(self):
        self.controller.fake_action.return_value = {'fakeTag': 'fake_data'}

        res = self.request.send(self.application)

        self.assertEqual(200, res.status_code)
        self.assertEqual('text/xml', res.content_type)
        expected_xml = fakes.XML_RESULT_TEMPLATE % {
            'action': 'FakeAction',
            'api_version': 'fake_v1',
            'request_id': self.fake_context.request_id,
            'data': '<fakeTag>fake_data</fakeTag>'}
        self.assertThat(res.body, matchers.XMLMatches(expected_xml))
        self.controller.fake_action.assert_called_once_with(self.fake_context,
                                                            param='fake_param')

    def test_execute_error(self):
        @tools.screen_all_logs
        def do_check(ex, status, code, message):
            self.controller.reset_mock()
            self.controller.fake_action.side_effect = ex

            res = self.request.send(self.application)

            self.assertEqual(status, res.status_code)
            self.assertEqual('text/xml', res.content_type)
            expected_xml = fakes.XML_ERROR_TEMPLATE % {
                'code': code,
                'message': message,
                'request_id': self.fake_context.request_id}
            self.assertThat(res.body, matchers.XMLMatches(expected_xml))
            self.controller.fake_action.assert_called_once_with(
                self.fake_context, param='fake_param')

        do_check(exception.EC2Exception('fake_msg'),
                 400, 'EC2Exception', 'fake_msg')
        do_check(KeyError('fake_msg'),
                 500, 'KeyError', 'Unknown error occurred.')
        do_check(exception.InvalidVpcIDNotFound('fake_msg'),
                 400, 'InvalidVpcID.NotFound', 'fake_msg')
        do_check(nova_exception.BadRequest(400, message='fake_msg'),
                 400, 'BadRequest', 'fake_msg')
        do_check(glance_exception.HTTPBadRequest(),
                 400, 'HTTPBadRequest', 'HTTPBadRequest (HTTP 400)')
        do_check(cinder_exception.BadRequest(400, message='fake_msg'),
                 400, 'BadRequest', 'fake_msg')
        do_check(neutron_exception.BadRequest(message='fake_msg'),
                 400, 'BadRequest', 'fake_msg')
        do_check(keystone_exception.BadRequest(message='fake_msg'),
                 400, 'BadRequest', 'fake_msg')
        do_check(boto_exception.S3ResponseError(400, '', 'fake_msg'),
                 400, 'S3ResponseError', 'fake_msg')
