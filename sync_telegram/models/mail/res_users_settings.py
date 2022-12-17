from odoo import fields, models


class ResUsersSettings(models.Model):
    _inherit = "res.users.settings"

    is_discuss_sidebar_category_telegram_open = fields.Boolean(
        "Is category telegram open", default=True
    )
    telegram_user_id = fields.Char(
        "Telegram user ID"
    )
    telegram_xml_id = fields.Char(
        "Path or xml_id or id"
    )
