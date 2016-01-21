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

import falcon
import etcd

from commissaire.model import Model
from commissaire.jobs import POOLS
from commissaire.resource import Resource


class Status(Model):
    """
    Representation of a Host.
    """
    _json_type = dict
    _attributes = (
        'etcd', 'investigator')


class StatusResource(Resource):
    """
    Resource for working with Status.
    """

    def on_get(self, req, resp):
        """
        Handles GET requests for Status.

        :param req: Request instance that will be passed through.
        :type req: falcon.Request
        :param resp: Response instance that will be passed through.
        :type resp: falcon.Response
        """
        # Fail closed
        kwargs = {
            'etcd': {
                'status': 'FAILED',
            },
            'investigator': {
                'status': 'FAILED',
                'info': {
                    'size': 0,
                    'in_use': 0,
                    'errors': [],
                }
            },
        }
        resp.status = falcon.HTTP_503

        # Check etcd connection
        try:
            self.store.get('/')
            kwargs['etcd']['status'] = 'OK'
        except etcd.EtcdKeyNotFound:
            kwargs['etcd']['status'] = 'FAILED'

        # Check the investigator pool
        kwargs['investigator']['info']['size'] = POOLS['investigator'].size
        kwargs['investigator']['info']['in_use'] = (
            POOLS['investigator'].size - POOLS['investigator'].free_count())

        exceptions = False
        for thread in POOLS['investigator'].greenlets:
            if thread.exception:
                exceptions = True
                POOLS['investigator']['info']['errors'].append(
                    thread.exception)

        if POOLS['investigator'].free_count() == 0:
            if not exceptions:
                kwargs['investigator']['status'] = 'OK'

        resp.status = falcon.HTTP_200
        req.context['model'] = Status(**kwargs)
