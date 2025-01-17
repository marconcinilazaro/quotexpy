"""Create a new Quotex Client instance"""
import sys
import math
import time
import logging
from collections import defaultdict as default_dict

from quotexpy import expiration
from quotexpy import global_value
from quotexpy.api import QuotexAPI
from quotexpy.constants import codes_asset


def nested_dict(n, typeof):
    if n == 1:
        return default_dict(typeof)
    return default_dict(lambda: nested_dict(n - 1, typeof))


def truncate(f, n):
    return math.floor(f * 10**n) / 10**n


class Quotex(object):
    __version__ = "1.0.40"

    def __init__(self, email, password, browser=False):
        self.size = [
            1,
            5,
            10,
            15,
            30,
            60,
            120,
            300,
            600,
            900,
            1800,
            3600,
            7200,
            14400,
            28800,
            43200,
            86400,
            604800,
            2592000,
        ]
        self.email = email
        self.password = password
        self.browser = browser
        self.set_ssid = None
        self.duration = None
        self.suspend = 0.5
        self.subscribe_candle = []
        self.subscribe_candle_all_size = []
        self.subscribe_mood = []
        self.websocket_client = None
        self.websocket_thread = None
        self.debug_ws_enable = False
        self.api = None

    @property
    def websocket(self):
        """Property to get websocket.

        :returns: The instance of :class:`WebSocket <websocket.WebSocket>`.
        """
        return self.websocket_client.wss

    @staticmethod
    def check_connect():
        if global_value.check_websocket_if_connect == 0:
            return False
        return True

    def re_subscribe_stream(self):
        try:
            for ac in self.subscribe_candle:
                sp = ac.split(",")
                self.start_candles_one_stream(sp[0], sp[1])
        except Exception:
            pass
        try:
            for ac in self.subscribe_candle_all_size:
                self.start_candles_all_size_stream(ac)
        except Exception:
            pass
        try:
            for ac in self.subscribe_mood:
                self.start_mood_stream(ac)
        except Exception:
            pass

    def get_instruments(self):
        time.sleep(self.suspend)
        self.api.instruments = None
        while self.api.instruments is None:
            try:
                self.api.get_instruments()
                start = time.time()
                while self.api.instruments is None and time.time() - start < 10:
                    pass
            except Exception:
                logging.error("**error** api.get_instruments need reconnect")
                self.connect()
        return self.api.instruments

    def get_all_asset_name(self):
        if self.api.instruments:
            return [instrument[2].replace("\n", "") for instrument in self.api.instruments]

    def check_asset_open(self, instrument):
        if self.api.instruments:
            for i in self.api.instruments:
                if instrument == i[2]:
                    return i[0], i[2], i[14]

    def get_candles(self, asset, offset, period=None):
        index = expiration.get_timestamp()
        if period:
            period = expiration.get_period_time(period)
        else:
            period = index
        self.api.current_asset = asset
        self.api.candles.candles_data = None
        while True:
            try:
                self.api.get_candles(codes_asset[asset], offset, period, index)
                while self.check_connect and self.api.candles.candles_data is None:
                    pass
                if self.api.candles.candles_data is not None:
                    break
            except Exception:
                logging.error("**error** get_candles need reconnect")
                self.connect()
        return self.api.candles.candles_data

    def get_candle_v2(self, asset, period):
        self.api.candle_v2_data[asset] = None
        size = 10
        self.stop_candles_stream(asset)
        self.api.subscribe_realtime_candle(asset, size, period)
        while self.api.candle_v2_data[asset] is None:
            time.sleep(1)
        return self.api.candle_v2_data[asset]

    async def connect(self):
        if global_value.check_websocket_if_connect:
            self.close()
        self.api = QuotexAPI(
            "qxbroker.com",
            self.email,
            self.password,
            browser=self.browser,
        )
        self.api.trace_ws = self.debug_ws_enable
        check, reason = await self.api.connect()
        if check:
            self.api.send_ssid()
            if global_value.check_accepted_connection == 0:
                check, reason = await self.connect()
                if not check:
                    check, reason = (
                        False,
                        "Access denied, session does not exist!!!",
                    )
        return check, reason

    def change_account(self, balance_mode="PRACTICE"):
        """Change active account `real` or `practice`"""
        if balance_mode.upper() == "REAL":
            self.api.account_type = 0
        elif balance_mode.upper() == "PRACTICE":
            self.api.account_type = 1
        else:
            logging.error(f"{balance_mode} does not exist")
            sys.exit(1)
        self.api.send_ssid()

    def edit_practice_balance(self, amount=None):
        self.api.training_balance_edit_request = None
        self.api.edit_training_balance(amount)
        while self.api.training_balance_edit_request is None:
            pass
        return self.api.training_balance_edit_request

    def get_balance(self):
        while not self.api.account_balance:
            time.sleep(0.1)
        balance = (
            self.api.account_balance.get("demoBalance")
            if self.api.account_type > 0
            else self.api.account_balance.get("liveBalance")
        )
        return round(balance, 2)

    def trade(self, action: str, amount, asset: str, duration):
        """Trade Binary option"""
        count = 0
        trade_status = False
        self.duration = duration
        request_id = expiration.get_timestamp()
        self.api.current_asset = asset
        self.api.trade_id[asset] = None
        self.api.trade_successful[asset] = None
        self.api.trade(
            action,
            amount,
            asset,
            duration,
            request_id,
        )
        while not self.api.trade_id[asset]:
            if count == 10:
                break
            count += 1
            time.sleep(1)
        else:
            trade_status = True
        return trade_status, self.api.trade_successful[asset]

    def get_payment(self):
        """Payment Quotex server"""
        assets_data = {}
        for i in self.api.instruments:
            assets_data[i[2]] = {
                "turbo_payment": i[18],
                "payment": i[5],
                "open": i[14],
            }
        return assets_data

    def check_win(self, id_number):
        """Check win based id"""
        # now_stamp = datetime.fromtimestamp(expiration.get_timestamp())
        # expiration_stamp = datetime.fromtimestamp(self.api.timesync.server_timestamp)
        # remaing_time = int((expiration_stamp - now_stamp).total_seconds())
        while True:
            try:
                list_info_data_dict = self.api.listinfodata.get(id_number)
                if list_info_data_dict["game_state"] == 1:
                    break
            except Exception:
                pass
            # remaing_time -= 1
            # time.sleep(1)
            # logger.info(f"\rRestando {remaing_time} segundos ...", end="")
        self.api.listinfodata.delete(id_number)
        # return list_info_data_dict["win"]
        return list_info_data_dict

    def start_candles_stream(self, asset, size, period=0):
        self.api.subscribe_realtime_candle(asset, size, period)

    def stop_candles_stream(self, asset):
        self.api.unsubscribe_realtime_candle(asset)

    def get_realtime_candles(self, asset):
        while True:
            if asset in self.api.realtime_price:
                if len(self.api.realtime_price[asset]) > 0:
                    return self.api.realtime_price[asset]

    def get_signal_data(self):
        return self.api.signal_data

    def get_profit(self):
        return self.api.profit_in_operation or 0

    def start_candles_one_stream(self, asset, size):
        if str(asset + "," + str(size)) not in self.subscribe_candle:
            self.subscribe_candle.append((asset + "," + str(size)))
        start = time.time()
        self.api.candle_generated_check[str(asset)][int(size)] = {}
        while True:
            if time.time() - start > 20:
                logging.error("**error** start_candles_one_stream late for 20 sec")
                return False
            try:
                if self.api.candle_generated_check[str(asset)][int(size)]:
                    return True
            except Exception:
                pass
            try:
                self.api.subscribe(codes_asset[asset], size)
            except Exception:
                logging.error("**error** start_candles_stream reconnect")
                self.connect()
            time.sleep(1)

    def start_candles_all_size_stream(self, asset):
        self.api.candle_generated_all_size_check[str(asset)] = {}
        if str(asset) not in self.subscribe_candle_all_size:
            self.subscribe_candle_all_size.append(str(asset))
        start = time.time()
        while True:
            if time.time() - start > 20:
                logging.error(f"**error** fail {asset} start_candles_all_size_stream late for 10 sec")
                return False
            try:
                if self.api.candle_generated_all_size_check[str(asset)]:
                    return True
            except Exception:
                pass
            try:
                self.api.subscribe_all_size(codes_asset[asset])
            except Exception:
                logging.error("**error** start_candles_all_size_stream reconnect")
                self.connect()
            time.sleep(1)

    def start_mood_stream(self, asset, instrument="turbo-option"):
        if asset not in self.subscribe_mood:
            self.subscribe_mood.append(asset)
        while True:
            self.api.subscribe_Traders_mood(asset[asset], instrument)
            try:
                self.api.traders_mood[codes_asset[asset]] = codes_asset[asset]
                break
            except Exception:
                time.sleep(5)

    def close(self):
        self.api.close()
