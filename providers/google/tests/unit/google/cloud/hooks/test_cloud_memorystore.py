#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

from unittest import mock
from unittest.mock import PropertyMock

import pytest
from google.api_core.gapic_v1.method import DEFAULT
from google.cloud.exceptions import NotFound
from google.cloud.memcache_v1beta2.types import cloud_memcache
from google.cloud.redis_v1.types import Instance

from airflow import version
from airflow.exceptions import AirflowException
from airflow.providers.google.cloud.hooks.cloud_memorystore import (
    CloudMemorystoreHook,
    CloudMemorystoreMemcachedHook,
)

from unit.google.cloud.utils.base_gcp_mock import (
    GCP_PROJECT_ID_HOOK_UNIT_TEST,
    mock_base_gcp_hook_default_project_id,
    mock_base_gcp_hook_no_default_project_id,
)

TEST_GCP_CONN_ID = "test-gcp-conn-id"
TEST_LOCATION = "test-location"
TEST_INSTANCE_ID = "test-instance-id"
TEST_PROJECT_ID = "test-project-id"
TEST_RETRY = DEFAULT
TEST_TIMEOUT = 10.0
TEST_METADATA = [("KEY", "VALUE")]
TEST_PAGE_SIZE = 100
TEST_UPDATE_MASK = {"paths": ["memory_size_gb"]}
TEST_UPDATE_MASK_MEMCACHED = {"displayName": "updated name"}
TEST_PARENT = "projects/test-project-id/locations/test-location"
TEST_NAME = "projects/test-project-id/locations/test-location/instances/test-instance-id"
TEST_PARENT_DEFAULT_PROJECT_ID = f"projects/{GCP_PROJECT_ID_HOOK_UNIT_TEST}/locations/test-location"
TEST_NAME_DEFAULT_PROJECT_ID = (
    f"projects/{GCP_PROJECT_ID_HOOK_UNIT_TEST}/locations/test-location/instances/test-instance-id"
)


class TestCloudMemorystoreWithDefaultProjectIdHook:
    def setup_method(self):
        with mock.patch(
            "airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.__init__",
            new=mock_base_gcp_hook_default_project_id,
        ):
            self.hook = CloudMemorystoreHook(gcp_conn_id="test")

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=GCP_PROJECT_ID_HOOK_UNIT_TEST,
    )
    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_create_instance_when_exists(self, mock_get_conn, mock_project_id):
        mock_get_conn.return_value.get_instance.return_value = Instance(name=TEST_NAME)
        result = self.hook.create_instance(
            location=TEST_LOCATION,
            instance_id=TEST_INSTANCE_ID,
            instance=Instance(name=TEST_NAME),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.get_instance.assert_called_once_with(
            request=dict(name=TEST_NAME_DEFAULT_PROJECT_ID),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        assert Instance(name=TEST_NAME) == result

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=GCP_PROJECT_ID_HOOK_UNIT_TEST,
    )
    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_create_instance_when_not_exists(self, mock_get_conn, mock_project_id):
        mock_get_conn.return_value.get_instance.side_effect = [
            NotFound("Instance not found"),
            Instance(name=TEST_NAME),
        ]
        mock_get_conn.return_value.create_instance.return_value.result.return_value = Instance(name=TEST_NAME)
        result = self.hook.create_instance(
            location=TEST_LOCATION,
            instance_id=TEST_INSTANCE_ID,
            instance=Instance(name=TEST_NAME),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.get_instance.assert_has_calls(
            [
                mock.call(
                    request=dict(name=TEST_NAME_DEFAULT_PROJECT_ID),
                    retry=TEST_RETRY,
                    timeout=TEST_TIMEOUT,
                    metadata=TEST_METADATA,
                ),
                mock.call(
                    request=dict(name=TEST_NAME_DEFAULT_PROJECT_ID),
                    retry=TEST_RETRY,
                    timeout=TEST_TIMEOUT,
                    metadata=TEST_METADATA,
                ),
            ]
        )
        mock_get_conn.return_value.create_instance.assert_called_once_with(
            request=dict(
                parent=TEST_PARENT_DEFAULT_PROJECT_ID,
                instance=Instance(
                    name=TEST_NAME,
                    labels={"airflow-version": "v" + version.version.replace(".", "-").replace("+", "-")},
                ),
                instance_id=TEST_INSTANCE_ID,
            ),
            metadata=TEST_METADATA,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
        )
        assert Instance(name=TEST_NAME) == result

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=GCP_PROJECT_ID_HOOK_UNIT_TEST,
    )
    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_delete_instance(self, mock_get_conn, mock_project_id):
        self.hook.delete_instance(
            location=TEST_LOCATION,
            instance=TEST_INSTANCE_ID,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.delete_instance.assert_called_once_with(
            request=dict(name=TEST_NAME_DEFAULT_PROJECT_ID),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=GCP_PROJECT_ID_HOOK_UNIT_TEST,
    )
    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_get_instance(self, mock_get_conn, mock_project_id):
        self.hook.get_instance(
            location=TEST_LOCATION,
            instance=TEST_INSTANCE_ID,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.get_instance.assert_called_once_with(
            request=dict(name=TEST_NAME_DEFAULT_PROJECT_ID),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=GCP_PROJECT_ID_HOOK_UNIT_TEST,
    )
    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_list_instances(self, mock_get_conn, mock_project_id):
        self.hook.list_instances(
            location=TEST_LOCATION,
            page_size=TEST_PAGE_SIZE,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.list_instances.assert_called_once_with(
            request=dict(parent=TEST_PARENT_DEFAULT_PROJECT_ID, page_size=TEST_PAGE_SIZE),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=GCP_PROJECT_ID_HOOK_UNIT_TEST,
    )
    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_update_instance(self, mock_get_conn, mock_project_id):
        self.hook.update_instance(
            update_mask=TEST_UPDATE_MASK,
            instance=Instance(name=TEST_NAME),
            location=TEST_LOCATION,
            instance_id=TEST_INSTANCE_ID,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.update_instance.assert_called_once_with(
            request=dict(update_mask=TEST_UPDATE_MASK, instance=Instance(name=TEST_NAME_DEFAULT_PROJECT_ID)),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )


class TestCloudMemorystoreWithoutDefaultProjectIdHook:
    def setup_method(self):
        with mock.patch(
            "airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.__init__",
            new=mock_base_gcp_hook_no_default_project_id,
        ):
            self.hook = CloudMemorystoreHook(gcp_conn_id="test")

    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_create_instance_when_exists(self, mock_get_conn):
        mock_get_conn.return_value.get_instance.return_value = Instance(name=TEST_NAME)
        result = self.hook.create_instance(
            location=TEST_LOCATION,
            instance_id=TEST_INSTANCE_ID,
            instance=Instance(name=TEST_NAME),
            project_id=TEST_PROJECT_ID,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.get_instance.assert_called_once_with(
            request=dict(name="projects/test-project-id/locations/test-location/instances/test-instance-id"),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        assert Instance(name=TEST_NAME) == result

    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_create_instance_when_not_exists(self, mock_get_conn):
        mock_get_conn.return_value.get_instance.side_effect = [
            NotFound("Instance not found"),
            Instance(name=TEST_NAME),
        ]
        mock_get_conn.return_value.create_instance.return_value.result.return_value = Instance(name=TEST_NAME)
        result = self.hook.create_instance(
            location=TEST_LOCATION,
            instance_id=TEST_INSTANCE_ID,
            instance=Instance(name=TEST_NAME),
            project_id=TEST_PROJECT_ID,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.get_instance.assert_has_calls(
            [
                mock.call(
                    request=dict(
                        name="projects/test-project-id/locations/test-location/instances/test-instance-id"
                    ),
                    retry=TEST_RETRY,
                    timeout=TEST_TIMEOUT,
                    metadata=TEST_METADATA,
                ),
                mock.call(
                    request=dict(
                        name="projects/test-project-id/locations/test-location/instances/test-instance-id"
                    ),
                    retry=TEST_RETRY,
                    timeout=TEST_TIMEOUT,
                    metadata=TEST_METADATA,
                ),
            ]
        )

        mock_get_conn.return_value.create_instance.assert_called_once_with(
            request=dict(
                parent=TEST_PARENT,
                instance=Instance(
                    name=TEST_NAME,
                    labels={"airflow-version": "v" + version.version.replace(".", "-").replace("+", "-")},
                ),
                instance_id=TEST_INSTANCE_ID,
            ),
            metadata=TEST_METADATA,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
        )
        assert Instance(name=TEST_NAME) == result

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=None,
    )
    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_create_instance_without_project_id(self, mock_get_conn, mock_project_id):
        with pytest.raises(AirflowException):
            self.hook.create_instance(
                location=TEST_LOCATION,
                instance_id=TEST_INSTANCE_ID,
                instance=Instance(name=TEST_NAME),
                project_id=None,
                retry=TEST_RETRY,
                timeout=TEST_TIMEOUT,
                metadata=TEST_METADATA,
            )

    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_delete_instance(self, mock_get_conn):
        self.hook.delete_instance(
            location=TEST_LOCATION,
            instance=TEST_INSTANCE_ID,
            project_id=TEST_PROJECT_ID,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.delete_instance.assert_called_once_with(
            request=dict(name=TEST_NAME), retry=TEST_RETRY, timeout=TEST_TIMEOUT, metadata=TEST_METADATA
        )

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=None,
    )
    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_delete_instance_without_project_id(self, mock_get_conn, mock_project_id):
        with pytest.raises(AirflowException):
            self.hook.delete_instance(
                location=TEST_LOCATION,
                instance=Instance(name=TEST_NAME),
                project_id=None,
                retry=TEST_RETRY,
                timeout=TEST_TIMEOUT,
                metadata=TEST_METADATA,
            )

    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_get_instance(self, mock_get_conn):
        self.hook.get_instance(
            location=TEST_LOCATION,
            instance=TEST_INSTANCE_ID,
            project_id=TEST_PROJECT_ID,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.get_instance.assert_called_once_with(
            request=dict(name=TEST_NAME), retry=TEST_RETRY, timeout=TEST_TIMEOUT, metadata=TEST_METADATA
        )

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=None,
    )
    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_get_instance_without_project_id(self, mock_get_conn, mock_project_id):
        with pytest.raises(AirflowException):
            self.hook.get_instance(
                location=TEST_LOCATION,
                instance=Instance(name=TEST_NAME),
                project_id=None,
                retry=TEST_RETRY,
                timeout=TEST_TIMEOUT,
                metadata=TEST_METADATA,
            )

    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_list_instances(self, mock_get_conn):
        self.hook.list_instances(
            location=TEST_LOCATION,
            page_size=TEST_PAGE_SIZE,
            project_id=TEST_PROJECT_ID,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.list_instances.assert_called_once_with(
            request=dict(parent=TEST_PARENT, page_size=TEST_PAGE_SIZE),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=None,
    )
    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_list_instances_without_project_id(self, mock_get_conn, mock_project_id):
        with pytest.raises(AirflowException):
            self.hook.list_instances(
                location=TEST_LOCATION,
                page_size=TEST_PAGE_SIZE,
                project_id=None,
                retry=TEST_RETRY,
                timeout=TEST_TIMEOUT,
                metadata=TEST_METADATA,
            )

    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_update_instance(self, mock_get_conn):
        self.hook.update_instance(
            update_mask=TEST_UPDATE_MASK,
            instance=Instance(name=TEST_NAME),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
            project_id=TEST_PROJECT_ID,
        )
        mock_get_conn.return_value.update_instance.assert_called_once_with(
            request=dict(update_mask={"paths": ["memory_size_gb"]}, instance=Instance(name=TEST_NAME)),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=None,
    )
    @mock.patch("airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreHook.get_conn")
    def test_update_instance_without_project_id(self, mock_get_conn, mock_project_id):
        with pytest.raises(AirflowException):
            self.hook.update_instance(
                update_mask=TEST_UPDATE_MASK,
                instance=Instance(name=TEST_NAME),
                retry=TEST_RETRY,
                timeout=TEST_TIMEOUT,
                metadata=TEST_METADATA,
            )


class TestCloudMemorystoreMemcachedWithDefaultProjectIdHook:
    def setup_method(self):
        with mock.patch(
            "airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreMemcachedHook.__init__",
            new=mock_base_gcp_hook_default_project_id,
        ):
            self.hook = CloudMemorystoreMemcachedHook(gcp_conn_id="test")

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=GCP_PROJECT_ID_HOOK_UNIT_TEST,
    )
    @mock.patch(
        "airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreMemcachedHook.get_conn"
    )
    def test_create_instance_when_exists(self, mock_get_conn, mock_project_id):
        mock_get_conn.return_value.get_instance.return_value = cloud_memcache.Instance(name=TEST_NAME)
        result = self.hook.create_instance(
            location=TEST_LOCATION,
            instance_id=TEST_INSTANCE_ID,
            instance=cloud_memcache.Instance(name=TEST_NAME),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.get_instance.assert_called_once_with(
            name=TEST_NAME_DEFAULT_PROJECT_ID, retry=TEST_RETRY, timeout=TEST_TIMEOUT, metadata=TEST_METADATA
        )
        assert cloud_memcache.Instance(name=TEST_NAME) == result

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=GCP_PROJECT_ID_HOOK_UNIT_TEST,
    )
    @mock.patch(
        "airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreMemcachedHook.get_conn"
    )
    def test_create_instance_when_not_exists(self, mock_get_conn, mock_project_id):
        mock_get_conn.return_value.get_instance.side_effect = [
            NotFound("Instance not found"),
            cloud_memcache.Instance(name=TEST_NAME),
        ]
        mock_get_conn.return_value.create_instance.return_value.result.return_value = cloud_memcache.Instance(
            name=TEST_NAME
        )
        result = self.hook.create_instance(
            location=TEST_LOCATION,
            instance_id=TEST_INSTANCE_ID,
            instance=cloud_memcache.Instance(name=TEST_NAME),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.get_instance.assert_has_calls(
            [
                mock.call(
                    name=TEST_NAME_DEFAULT_PROJECT_ID,
                    retry=TEST_RETRY,
                    timeout=TEST_TIMEOUT,
                    metadata=TEST_METADATA,
                ),
                mock.call(
                    name=TEST_NAME_DEFAULT_PROJECT_ID,
                    retry=TEST_RETRY,
                    timeout=TEST_TIMEOUT,
                    metadata=TEST_METADATA,
                ),
            ]
        )
        mock_get_conn.return_value.create_instance.assert_called_once_with(
            resource=cloud_memcache.Instance(
                name=TEST_NAME,
                labels={"airflow-version": "v" + version.version.replace(".", "-").replace("+", "-")},
            ),
            instance_id=TEST_INSTANCE_ID,
            metadata=TEST_METADATA,
            parent=TEST_PARENT_DEFAULT_PROJECT_ID,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
        )
        assert cloud_memcache.Instance(name=TEST_NAME) == result

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=GCP_PROJECT_ID_HOOK_UNIT_TEST,
    )
    @mock.patch(
        "airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreMemcachedHook.get_conn"
    )
    def test_delete_instance(self, mock_get_conn, mock_project_id):
        self.hook.delete_instance(
            location=TEST_LOCATION,
            instance=TEST_INSTANCE_ID,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.delete_instance.assert_called_once_with(
            name=TEST_NAME_DEFAULT_PROJECT_ID, retry=TEST_RETRY, timeout=TEST_TIMEOUT, metadata=TEST_METADATA
        )

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=GCP_PROJECT_ID_HOOK_UNIT_TEST,
    )
    @mock.patch(
        "airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreMemcachedHook.get_conn"
    )
    def test_get_instance(self, mock_get_conn, mock_project_id):
        self.hook.get_instance(
            location=TEST_LOCATION,
            instance=TEST_INSTANCE_ID,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.get_instance.assert_called_once_with(
            name=TEST_NAME_DEFAULT_PROJECT_ID, retry=TEST_RETRY, timeout=TEST_TIMEOUT, metadata=TEST_METADATA
        )

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=GCP_PROJECT_ID_HOOK_UNIT_TEST,
    )
    @mock.patch(
        "airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreMemcachedHook.get_conn"
    )
    def test_list_instances(self, mock_get_conn, mock_project_id):
        self.hook.list_instances(
            location=TEST_LOCATION,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.list_instances.assert_called_once_with(
            parent=TEST_PARENT_DEFAULT_PROJECT_ID,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )

    @mock.patch(
        "airflow.providers.google.common.hooks.base_google.GoogleBaseHook.project_id",
        new_callable=PropertyMock,
        return_value=GCP_PROJECT_ID_HOOK_UNIT_TEST,
    )
    @mock.patch(
        "airflow.providers.google.cloud.hooks.cloud_memorystore.CloudMemorystoreMemcachedHook.get_conn"
    )
    def test_update_instance(self, mock_get_conn, mock_project_id):
        self.hook.update_instance(
            update_mask=TEST_UPDATE_MASK_MEMCACHED,
            instance=cloud_memcache.Instance(name=TEST_NAME),
            location=TEST_LOCATION,
            instance_id=TEST_INSTANCE_ID,
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
        mock_get_conn.return_value.update_instance.assert_called_once_with(
            update_mask=TEST_UPDATE_MASK_MEMCACHED,
            resource=cloud_memcache.Instance(name=TEST_NAME_DEFAULT_PROJECT_ID),
            retry=TEST_RETRY,
            timeout=TEST_TIMEOUT,
            metadata=TEST_METADATA,
        )
