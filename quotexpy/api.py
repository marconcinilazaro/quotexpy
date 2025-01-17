"""Module for Quotex websocket"""
import os
import time
import json
import ssl
import threading
import collections
import urllib3
import certifi
from collections import defaultdict as default_dict

from quotexpy import global_value
from quotexpy.logger import logger
from quotexpy.http.login import Login
from quotexpy.http.logout import Logout
from quotexpy.ws.channels.ssid import Ssid
from quotexpy.ws.channels.trade import Trade
from quotexpy.exceptions import QuotexTimeout
from quotexpy.ws.channels.candles import GetCandles
from quotexpy.ws.objects.timesync import TimeSync
from quotexpy.ws.objects.candles import Candles
from quotexpy.ws.objects.profile import Profile
from quotexpy.ws.objects.listinfodata import ListInfoData
from quotexpy.ws.client import WebsocketClient


def nested_dict(n, typeof):
    if n == 1:
        return default_dict(typeof)
    return default_dict(lambda: nested_dict(n - 1, typeof))


urllib3.disable_warnings()

cert_path = certifi.where()
os.environ["SSL_CERT_FILE"] = cert_path
os.environ["WEBSOCKET_CLIENT_CA_BUNDLE"] = cert_path
cacert = os.environ.get("WEBSOCKET_CLIENT_CA_BUNDLE")


class QuotexAPI(object):
    """Class for communication with Quotex API"""

    socket_option_opened = {}
    trade_id = {}
    trace_ws = False
    buy_expiration = None
    current_asset = None
    trade_successful = {}
    account_balance = None
    account_type = None
    instruments = None
    training_balance_edit_request = None
    profit_in_operation = None
    sold_options_respond = None
    sold_digital_options_respond = None
    listinfodata = ListInfoData()
    timesync = TimeSync()
    candles = Candles()

    def __init__(self, host, email, password, proxies=None, browser=False):
        """
        :param str host: The hostname or ip address of a Quotex server.
        :param str email: The email of a Quotex server.
        :param str password: The password of a Quotex server.
        :param proxies: The proxies of a Quotex server.
        """
        self._temp_status = ""
        self.settings_list = {}
        self.email = email
        self.password = password
        self.signal_data = nested_dict(2, dict)
        self.get_candle_data = {}
        self.candle_v2_data = {}
        self.cookies = None
        self.profile = None
        self.websocket_thread = None
        self.wss_url = f"wss://ws2.{host}/socket.io/?EIO=3&transport=websocket"
        self.websocket_client = None
        self.set_ssid = None
        self.user_agent = None
        self.token_login2fa = None
        self.proxies = proxies
        self.browser = browser
        self.realtime_price = {}
        self.profile = Profile()

    @property
    def websocket(self):
        """Property to get websocket.

        :returns: The instance of :class:`WebSocket <websocket.WebSocket>`.
        """
        return self.websocket_client.wss

    def get_candle_v2(self):
        payload = {"_placeholder": True, "num": 0}
        data = f'451-["history/list/v2", {json.dumps(payload)}]'
        return self.send_websocket_request(data)

    def subscribe_realtime_candle(self, asset, size, period):
        self.realtime_price[asset] = collections.deque([], size)
        payload = {"asset": asset, "period": period}
        data = f'42["instruments/update", {json.dumps(payload)}]'
        return self.send_websocket_request(data)

    def unsubscribe_realtime_candle(self, asset):
        data = f'42["subfor", {json.dumps(asset)}]'
        return self.send_websocket_request(data)

    @property
    def logout(self):
        """Property for get Quotex http login resource.
        :returns: The instance of :class:`Login
            <quotexpy.http.login.Login>`.
        """
        return Logout(self)

    @property
    def login(self):
        """Property for get Quotex http login resource.
        :returns: The instance of :class:`Login
            <quotexpy.http.login.Login>`.
        """
        return Login(self)

    @property
    def ssid(self):
        """Property for get Quotex websocket ssid channel.
        :returns: The instance of :class:`Ssid
            <quotexpy.ws.channels.ssid.Ssid>`.
        """
        return Ssid(self)

    @property
    def trade(self):
        """Property for get Quotex websocket ssid channel.
        :returns: The instance of :class:`Trade
            <quotexpy.ws.channels.trade.Trade>`.
        """
        return Trade(self)

    @property
    def get_candles(self):
        """Property for get Quotex websocket candles channel.

        :returns: The instance of :class:`GetCandles
            <quotexpy.ws.channels.candles.GetCandles>`.
        """
        return GetCandles(self)

    def check_session(self):
        data = {}
        if os.path.isfile(".session.json"):
            with open(".session.json") as file:
                data = json.loads(file.read())
            self.user_agent = data.get("user_agent")
        return data.get("ssid"), data.get("cookies")
        # if global_value.session:
        #     data = global_value.session
        #     self.user_agent = data.get("user_agent")
        # return data.get("ssid"), data.get("cookies")

    def send_websocket_request(self, data, no_force_send=True):
        """Send websocket request to Quotex server.
        :param str data: The websocket request data.
        :param bool no_force_send: Default None.
        """
        # while (global_value.ssl_Mutual_exclusion or global_value.ssl_Mutual_exclusion_write) and no_force_send:
        #     pass
        global_value.ssl_Mutual_exclusion_write = True
        # self.websocket.send('42["tick"]')
        # self.websocket.send('42["indicator/list"]')
        # self.websocket.send('42["drawing/load"]')
        # self.websocket.send('42["pending/list"]')
        # self.websocket.send('42["instruments/update",{"asset":"%s","period":60}]' % self.current_asset)
        # self.websocket.send('42["chart_notification/get"]')
        # self.websocket.send('42["depth/follow","%s"]' % self.current_asset)
        self.websocket.send(data)
        logger.debug(data)
        global_value.ssl_Mutual_exclusion_write = False

    def edit_training_balance(self, amount):
        data = f'42["demo/refill",{json.dumps(amount)}]'
        self.send_websocket_request(data)

    async def get_ssid(self):
        ssid, cookies = self.check_session()
        if not ssid:
            logger.info("Authenticating user...")
            ssid, cookies = await self.login(
                self.email,
                self.password,
                self.browser,
            )
            logger.info("Login successful!!!")
        return ssid, cookies

    def start_websocket(self):
        global_value.check_websocket_if_connect = None
        global_value.check_websocket_if_error = False
        global_value.websocket_error_reason = None
        self.websocket_client = WebsocketClient(self)
        self.websocket_thread = threading.Thread(
            target=self.websocket.run_forever,
            kwargs={
                "ping_interval": 2,
                "ping_payload": "2",
                "origin": "https://qxbroker.com",
                "host": "ws2.qxbroker.com",
                "sslopt": {
                    "check_hostname": False,
                    "cert_reqs": ssl.CERT_NONE,
                    "ca_certs": cacert,
                },
            },
        )
        self.websocket_thread.daemon = True
        self.websocket_thread.start()
        while True:
            try:
                if global_value.check_websocket_if_error:
                    return False, global_value.websocket_error_reason
                if global_value.check_websocket_if_connect == 0:
                    logger.info("Websocket connection closed.")
                    logger.debug("Websocket connection closed.")
                    return False, "Websocket connection closed."
                if global_value.check_websocket_if_connect == 1:
                    logger.debug("Websocket successfully connected!!!")
                    return True, "Websocket successfully connected!!!"
            except:
                pass

    def send_ssid(self):
        self.profile.msg = None
        self.ssid(global_value.SSID)
        count = 0
        while not self.profile.msg:
            time.sleep(0.1)
            count += 1
            if count == 50:
                raise QuotexTimeout(f"Sending authorization with SSID '{global_value.SSID}' took too long to respond")
        if not self.profile.msg:
            return False
        return True

    async def connect(self):
        """Method for connection to Quotex API"""
        global_value.ssl_Mutual_exclusion = False
        global_value.ssl_Mutual_exclusion_write = False
        if global_value.check_websocket_if_connect:
            self.close()
        ssid, self.cookies = await self.get_ssid()
        check_websocket, websocket_reason = self.start_websocket()
        if not check_websocket:
            return check_websocket, websocket_reason
        if not global_value.SSID:
            global_value.SSID = ssid
        return check_websocket, websocket_reason

    def close(self):
        if self.websocket_client:
            self.websocket.close()
            self.websocket_thread.join()

    def websocket_alive(self):
        return self.websocket_thread.is_alive()
