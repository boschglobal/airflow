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

from pathlib import Path
from typing import TYPE_CHECKING, Sequence

import pytest

from airflow.providers.edge.cli.edge_command import _EdgeWorkerCli
from airflow.providers.edge.models.edge_worker import (
    EdgeWorker,
    EdgeWorkerModel,
    EdgeWorkerState,
    EdgeWorkerVersionException,
)
from airflow.utils import timezone

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

pytestmark = pytest.mark.db_test


class TestEdgeWorker:
    @pytest.fixture
    def cli_worker(self, tmp_path: Path) -> _EdgeWorkerCli:
        test_worker = _EdgeWorkerCli(tmp_path / "dummy.pid", "dummy", None, 8, 5, 5)
        return test_worker

    @pytest.fixture(autouse=True)
    def setup_test_cases(self, session: Session):
        session.query(EdgeWorkerModel).delete()

    def test_assert_version(self):
        from airflow import __version__ as airflow_version
        from airflow.providers.edge import __version__ as edge_provider_version

        with pytest.raises(EdgeWorkerVersionException):
            EdgeWorker.assert_version({})

        with pytest.raises(EdgeWorkerVersionException):
            EdgeWorker.assert_version({"airflow_version": airflow_version})

        with pytest.raises(EdgeWorkerVersionException):
            EdgeWorker.assert_version({"edge_provider_version": edge_provider_version})

        with pytest.raises(EdgeWorkerVersionException):
            EdgeWorker.assert_version(
                {"airflow_version": "1.2.3", "edge_provider_version": edge_provider_version}
            )

        with pytest.raises(EdgeWorkerVersionException):
            EdgeWorker.assert_version(
                {"airflow_version": airflow_version, "edge_provider_version": "2023.10.07"}
            )

        EdgeWorker.assert_version(
            {"airflow_version": airflow_version, "edge_provider_version": edge_provider_version}
        )

    @pytest.mark.parametrize(
        "input_queues",
        [
            pytest.param(None, id="empty-queues"),
            pytest.param(["default", "default2"], id="with-queues"),
        ],
    )
    def test_register_worker(
        self, session: Session, input_queues: Sequence[str] | None, cli_worker: _EdgeWorkerCli
    ):
        EdgeWorker.register_worker(
            "test_worker", EdgeWorkerState.STARTING, queues=input_queues, sysinfo=cli_worker._get_sysinfo()
        )

        worker: list[EdgeWorkerModel] = session.query(EdgeWorkerModel).all()
        assert len(worker) == 1
        assert worker[0].worker_name == "test_worker"
        if input_queues:
            assert worker[0].queues == "default,default2"
        else:
            assert worker[0].queues is None

    def test_set_state(self, session: Session, cli_worker: _EdgeWorkerCli):
        rwm = EdgeWorkerModel(
            worker_name="test2_worker",
            state=EdgeWorkerState.IDLE,
            queues=["default", "default2"],
            first_online=timezone.utcnow(),
        )
        session.add(rwm)
        session.commit()

        EdgeWorker.set_state("test2_worker", EdgeWorkerState.RUNNING, 1, cli_worker._get_sysinfo())

        worker: list[EdgeWorkerModel] = session.query(EdgeWorkerModel).all()
        assert len(worker) == 1
        assert worker[0].worker_name == "test2_worker"
        assert worker[0].state == EdgeWorkerState.RUNNING
        assert worker[0].queues == "default,default2"
