# All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

from rally.benchmark.context import base
from rally.benchmark.scenarios import base as scenario_base
from rally.common.i18n import _
from rally.common import log as logging
from rally.common import utils as rutils
from rally import consts
from rally import osclients


LOG = logging.getLogger(__name__)


@base.context(name="fake_images", order=411)
class FakeImageGenerator(base.Context):
    """Context class for adding images to each user for benchmarks."""

    CONFIG_SCHEMA = {
        "type": "object",
        "$schema": consts.JSON_SCHEMA,
        "properties": {
            "disk_format": {
                "enum": ["qcow2", "raw", "vhd", "vmdk", "vdi", "iso", "aki",
                         "ari", "ami"],
            },
            "container_format": {
                "type": "string",
            },
            "images_per_tenant": {
                "type": "integer",
                "minimum": 1
            },
        },
        "required": ["disk_format", "container_format", "images_per_tenant"],
        "additionalProperties": False
    }

    @rutils.log_task_wrapper(LOG.info, _("Enter context: `Images`"))
    def setup(self):
        disk_format = self.config["disk_format"]
        container_format = self.config["container_format"]
        images_per_tenant = self.config["images_per_tenant"]

        for user, tenant_id in rutils.iterate_per_tenants(
                self.context["users"]):
            glance = osclients.Clients(user["endpoint"]).glance().images
            current_images = []
            for i in range(images_per_tenant):
                kw = {
                    "name": scenario_base.Scenario._generate_random_name(),
                    "container_format": container_format,
                    "disk_format": disk_format,
                    "size": 1000000,
                }
                image = glance.create(**kw)
                current_images.append(image.id)

            self.context["tenants"][tenant_id]["images"] = current_images

    @rutils.log_task_wrapper(LOG.info, _("Exit context: `Images`"))
    def cleanup(self):
        for user, tenant_id in rutils.iterate_per_tenants(
                self.context["users"]):
            glance = osclients.Clients(user["endpoint"]).glance().images
            for image in self.context["tenants"][tenant_id].get("images", []):
                with logging.ExceptionLogger(
                        LOG,
                        _("Failed to delete network for tenant %s")
                        % tenant_id):
                    glance.delete(image)
