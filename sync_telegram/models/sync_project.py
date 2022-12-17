# Copyright 2020,2022 Ivan Yelizariev <https://twitter.com/yelizariev>
# Copyright 2021 Denis Mudarisov <https://github.com/trojikman>
# License MIT (https://opensource.org/licenses/MIT).

import base64
import logging

import telebot  # pylint: disable=missing-manifest-dependency; disabled because pre-commit cannot find external dependency in manifest. https://github.com/itpp-labs/DINAR/issues/91
from lxml.html.clean import Cleaner

from odoo import api, models

from odoo.addons.multi_livechat.tools import get_multi_livechat_eval_context
from odoo.addons.sync.models.sync_project import AttrDict
from odoo.addons.sync.tools import LogExternalQuery, url2base64, url2bin

_logger = logging.getLogger(__name__)

MAX_SIZE_IMAGE = 10485760
MAX_SIZE_DOCUMENT = 52428800
MAX_SIZE_TO_DOWNLOAD = 20971520


class SyncProjectTelegram(models.Model):

    _inherit = "sync.project.context"

    @api.model
    def _eval_context_telegram(self, secrets, eval_context, create_mail_channel=None):
        """Adds telegram object:
        * telegram.sendMessage
        * telegram.setWebhook
        * telegram.parse_data

        * multi_livechat.*
        """
        if secrets.TELEGRAM_BOT_TOKEN:
            bot = telebot.TeleBot(token=secrets.TELEGRAM_BOT_TOKEN)
        else:
            raise Exception("Telegram bot token is not set")

        def _html_sanitize_telegram(html):
            allowed_tags = set({"b", "i", "u", "s", "a", "code", "pre"})
            cleaner = Cleaner(
                safe_attrs_only=True,
                safe_attrs=set(),
                allow_tags=allowed_tags,
                remove_unknown_tags=False,
            )
            html = cleaner.clean_html(html)
            # remove surrounding div
            return html[5:-6]

        def getFullPath(file_path):
            return "https://api.telegram.org/file/bot{}/{}".format(
                secrets.TELEGRAM_BOT_TOKEN, file_path
            )

        def create_mail_channel(partners, channel_name):
            vals = self.env["mail.channel"]._prepare_multi_livechat_channel_vals(
                "multi_livechat_telegram", channel_name, partners
            )
            return self.env["mail.channel"].sudo().create(vals)

        @LogExternalQuery("Telegram->sendMessage", eval_context)
        def sendMessage(chat_id, html, *args, **kwargs):
            channel = kwargs.pop("channel", None)
            try:
                bot.send_message(
                    chat_id, _html_sanitize_telegram(html), *args, **kwargs
                )
            except Exception as e:
                if channel is not None:
                    multi_livechat_context.message_post(channel, str(e))
                else:
                    raise

        @LogExternalQuery("Telegram->sendPhoto", eval_context)
        def sendPhoto(chat_id, datas, *args, **kwargs):
            channel = kwargs.pop("channel", None)
            try:
                bot.send_photo(chat_id, photo=base64.b64decode(datas))
            except Exception as e:
                if channel is not None:
                    multi_livechat_context.message_post(channel, str(e))
                else:
                    raise

        @LogExternalQuery("Telegram->sendDocument", eval_context)
        def sendDocument(chat_id, name, datas, *args, **kwargs):
            channel = kwargs.pop("channel", None)
            try:
                bot.send_document(
                    chat_id, base64.b64decode(datas), visible_file_name=name
                )
            except Exception as e:
                if channel is not None:
                    multi_livechat_context.message_post(channel, str(e))
                else:
                    raise

        @LogExternalQuery("Telegram->getDocumentFile", eval_context)
        def getDocumentFile(chat_id, file_data):
            file_name = file_data.file_name
            file_path = bot.get_file(file_data.file_id).file_path
            content = url2bin(getFullPath(file_path))
            return [file_name, content]

        @LogExternalQuery("Telegram->getMediaFile", eval_context)
        def getMediaFile(chat_id, file_data):
            file_path = bot.get_file(file_data.file_id).file_path
            content = url2bin(getFullPath(file_path))
            return [file_path.split("/")[-1], content]

        @LogExternalQuery("Telegram->getUserPhoto", eval_context)
        def getUserPhoto(chat_id):
            photo_list = bot.get_user_profile_photos(chat_id).photos
            if not photo_list:
                return None
            else:
                file_path = bot.get_file(photo_list[0][0].file_id).file_path
                return url2base64(getFullPath(file_path))

        @LogExternalQuery("Telegram-> setWebhook", eval_context)
        def setWebhook(*args, **kwargs):
            if bot.set_webhook(*args, **kwargs):
                res = bot.get_webhook_info()
                data = {
                    'url': res.url,
                    'has_custom_certificate': res.has_custom_certificate,
                    'last_error_message': res.last_error_message,
                }
                return data

        def authLogin(*args, **kwargs):
            token = False
            if kwargs.get('token'):
                token = kwargs['token']
            if args and token:
                url = args + "?token=%s" % token
                return url2base64(url)
            return False

        def login(*args, **kwargs):
            res_user = token = False
            if kwargs.get('token'):
                token = kwargs['token']
            if token and kwargs.get('user_id'):
                res_user = self.env['res.users.settings'].search([('telegram_user_id', '=', kwargs['user_id'])])
                if len(res_user) > 1:
                    res_user = res_user[0]
                return res_user.id
            if token and kwargs.get('odoo_user_id'):
                res_user = self.env['res.users.settings'].search([('user_id', '=', kwargs['odoo_user_id'])])
                if res_user:
                    res_user.write({
                        'telegram_xml_id': args,
                        'telegram_user_id': kwargs['user_id'],
                    })
                    return res_user.id
            return False

        def parse_data(data):
            return telebot.types.Update.de_json(data)

        def auth_data(data):
            _logger.info("Login: %s" % data)
            return {}

        multi_livechat_context = AttrDict(
            get_multi_livechat_eval_context(
                self.env, "multi_livechat_telegram", eval_context
            )
        )

        telegram = AttrDict(
            {
                "sendMessage": sendMessage,
                "sendPhoto": sendPhoto,
                "sendDocument": sendDocument,
                "getDocumentFile": getDocumentFile,
                "getMediaFile": getMediaFile,
                "getUserPhoto": getUserPhoto,
                "setWebhook": setWebhook,
                "authLogin": authLogin,
                "login": login,
                "parse_data": parse_data,
                "auth_data": auth_data,
                "create_mail_сhannel": create_mail_channel,
                "MAX_SIZE_IMAGE": MAX_SIZE_IMAGE,
                "MAX_SIZE_DOCUMENT": MAX_SIZE_DOCUMENT,
                "MAX_SIZE_TO_DOWNLOAD": MAX_SIZE_TO_DOWNLOAD,
            }
        )
        # _logger.info("TELEGRAM %s\n%s::%s::%s" % (create_mail_channel, telegram, Cleaner,multi_livechat_context))
        return {
            "telegram": telegram,
            "Cleaner": Cleaner,
            "multi_livechat": multi_livechat_context,
        }
