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
"""
This module allows to connect to a InfluxDB database.

.. spelling:word-list::

    FluxTable
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from influxdb_client import InfluxDBClient
from influxdb_client.client.write.point import Point
from influxdb_client.client.write_api import SYNCHRONOUS

from airflow.providers.influxdb.version_compat import BaseHook

if TYPE_CHECKING:
    import pandas as pd
    from influxdb_client.client.flux_table import FluxTable

    from airflow.models import Connection


class InfluxDBHook(BaseHook):
    """
    Interact with InfluxDB.

    Performs a connection to InfluxDB and retrieves client.

    :param influxdb_conn_id: Reference to :ref:`Influxdb connection id <howto/connection:influxdb>`.
    """

    conn_name_attr = "influxdb_conn_id"
    default_conn_name = "influxdb_default"
    conn_type = "influxdb"
    hook_name = "Influxdb"

    def __init__(self, conn_id: str = default_conn_name, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.influxdb_conn_id = conn_id
        self.connection = kwargs.pop("connection", None)
        self.client: InfluxDBClient | None = None
        self.extras: dict = {}
        self.uri = None

    @classmethod
    def get_connection_form_widgets(cls) -> dict[str, Any]:
        """Return connection widgets to add to connection form."""
        from flask_appbuilder.fieldwidgets import BS3TextFieldWidget
        from flask_babel import lazy_gettext
        from wtforms import StringField

        return {
            "token": StringField(lazy_gettext("Token"), widget=BS3TextFieldWidget(), default=""),
            "org": StringField(
                lazy_gettext("Organization Name"),
                widget=BS3TextFieldWidget(),
                default="",
            ),
        }

    def get_client(self, uri, kwargs) -> InfluxDBClient:
        return InfluxDBClient(url=uri, **kwargs)

    def get_uri(self, conn: Connection):
        """Add additional parameters to the URI based on InfluxDB host requirements."""
        conn_scheme = "https" if conn.schema is None else conn.schema
        conn_port = 7687 if conn.port is None else conn.port
        return f"{conn_scheme}://{conn.host}:{conn_port}"

    def get_conn(self) -> InfluxDBClient:
        """Initiate a new InfluxDB connection with token and organization name."""
        self.connection = self.get_connection(self.influxdb_conn_id)
        self.extras = self.connection.extra_dejson.copy()

        self.uri = self.get_uri(self.connection)
        self.log.info("URI: %s", self.uri)

        if self.client is not None:
            return self.client

        self.client = self.get_client(self.uri, self.extras)

        return self.client

    def query(self, query) -> list[FluxTable]:
        """
        Run the query.

        Note: The bucket name should be included in the query.

        :param query: InfluxDB query
        :return: List
        """
        client = self.get_conn()

        query_api = client.query_api()
        return query_api.query(query)

    def query_to_df(self, query) -> pd.DataFrame:
        """
        Run the query and return a pandas dataframe.

        Note: The bucket name should be included in the query.

        :param query: InfluxDB query
        :return: pd.DataFrame
        """
        client = self.get_conn()

        query_api = client.query_api()
        return query_api.query_data_frame(query)

    def write(self, bucket_name, point_name, tag_name, tag_value, field_name, field_value, synchronous=False):
        """
        Write a Point to the bucket specified.

        Example: ``Point("my_measurement").tag("location", "Prague").field("temperature", 25.3)``
        """
        # By defaults its Batching
        if synchronous:
            write_api = self.client.write_api(write_options=SYNCHRONOUS)
        else:
            write_api = self.client.write_api()

        p = Point(point_name).tag(tag_name, tag_value).field(field_name, field_value)

        write_api.write(bucket=bucket_name, record=p)

    def create_organization(self, name):
        """Create a new organization."""
        return self.client.organizations_api().create_organization(name=name)

    def delete_organization(self, org_id):
        """Delete an organization by ID."""
        return self.client.organizations_api().delete_organization(org_id=org_id)

    def create_bucket(self, bucket_name, description, org_id, retention_rules=None):
        """Create a bucket for an organization."""
        return self.client.buckets_api().create_bucket(
            bucket_name=bucket_name, description=description, org_id=org_id, retention_rules=None
        )

    def find_bucket_id_by_name(self, bucket_name):
        """Get bucket ID by name."""
        bucket = self.client.buckets_api().find_bucket_by_name(bucket_name)

        return "" if bucket is None else bucket.id

    def delete_bucket(self, bucket_name):
        """Delete bucket by name."""
        bucket = self.find_bucket_id_by_name(bucket_name)
        return self.client.buckets_api().delete_bucket(bucket)
