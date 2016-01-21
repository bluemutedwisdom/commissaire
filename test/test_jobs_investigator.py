# Copyright (C) 2016  Red Hat, Inc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Test cases for the commissaire.authentication.httpauth module.
"""

import etcd
import mock

from . import TestCase
from commissaire.jobs.investigator import investigator
from gevent.queue import Queue
from mock import MagicMock


class Test_JobsInvestigator(TestCase):
    """
    Tests for the investigator job.
    """

    etcd_host = ('{"address": "10.2.0.2", "ssh_priv_key": "dGVzdAo=",'
                 ' "status": "available", "os": "atomic",'
                 ' "cpus": 2, "memory": 11989228, "space": 487652,'
                 ' "last_check": "2015-12-17T15:48:18.710454"}')

    def test_investigator(self):
        """
        Verify investigator ....
        """
        with mock.patch('commissaire.transport.ansibleapi.Transport') as _tp:
            _tp().get_info.return_value = (
                0,
                {
                    'os': 'fedora',
                    'cpus': 2,
                    'memory': 11989228,
                    'space': 487652,
                }
            )

            q = Queue()
            client = etcd.Client()
            client.get = MagicMock('get')
            client.get.return_value = MagicMock(value=self.etcd_host)
            client.set = MagicMock('set')
            client.set.return_value = self.etcd_host

            to_investigate = {
                'address': '10.0.0.2',
            }
            ssh_priv_key = 'dGVzdAo='

            q.put_nowait((to_investigate, ssh_priv_key))
            investigator(q, client, True)

            self.assertEquals(1, client.get.call_count)
            self.assertEquals(1, client.set.call_count)