# Copyright 2021 ilya ilchenko <http://github.com/mentalko>
# License MIT (https://opensource.org/licenses/MIT).

from odoo import models
from odoo.tools import config


class Attachment(models.Model):
    _inherit = "ir.attachment"

    def _public_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        if config.get('proxy_mode', False) and not base_url.startswith('https://') and base_url.find('http://') != -1:
            base_url = 'https://' + base_url.split('http://')[1]
        self.generate_access_token()
        return "%s/web/content/%s/%s?access_token=%s" % (
            base_url,
            self.id,
            self.name,
            self.access_token,
        )
