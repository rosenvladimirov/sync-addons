# Copyright 2020 Ivan Yelizariev <https://twitter.com/yelizariev>
# Copyright 2021 Denis Mudarisov <https://github.com/trojikman>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import logging
from odoo import http

from ..lib.controllers.main import Website

_logger = logging.getLogger(__name__)


class Webhook(Website):
    @http.route(
        [
            "/website/action-json/<string:path_or_xml_id_or_id>",
            "/website/action-json/<string:path_or_xml_id_or_id>/<path:path>",
        ],
        type="json",
        auth="public",
        website=False,
        csrf=False,
    )
    def actions_server_json(self, path_or_xml_id_or_id, **post):
        res = self.actions_server(path_or_xml_id_or_id, **post)
        return res.data

    @http.route(
        [
            "/website/action-http/<string:path_or_xml_id_or_id>",
            "/website/action-http/<string:path_or_xml_id_or_id>/<path:path>",
        ],
        type="http",
        auth="public",
        website=True,
        csrf=False,
    )
    def actions_server_http(self, path_or_xml_id_or_id, **post):
        return self.actions_server(path_or_xml_id_or_id, **post)

    @http.route(
        [
            "/website/action-auth/<string:path_or_xml_id_or_id>",
            "/website/action-auth/<string:path_or_xml_id_or_id>/<path:path>",
        ],
        type="http",
        auth="user",
        website=True,
        csrf=True,
    )
    def actions_server_auth(self, path_or_xml_id_or_id, **post):
        post['odoo_user_id'] = http.request.env.uid
        return self.actions_server_auth(path_or_xml_id_or_id, **post)
