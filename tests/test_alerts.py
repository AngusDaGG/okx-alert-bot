"""Offline regression tests; no credentials, HTTP or Discord delivery."""
import importlib
import sys
import unittest
from types import ModuleType
from unittest.mock import Mock, patch

config = ModuleType('config')
config.MIN_24H_VOLUME_USDT = 1000
config.ALERT_THRESHOLD_PCT = 2.0
config.TIMEFRAME = '5m'
config.ALERT_COOLDOWN_MINUTES = 60
config.DISCORD_WEBHOOK_URL = ''
with patch.dict(sys.modules, {'config': config}):
    scanner = importlib.import_module('scanner')
    notifier = importlib.import_module('discord_notifier')
import okx_client


class AlertTests(unittest.TestCase):
    def test_volume_filter_rejects_missing_low_volume_and_other_settlement(self):
        symbols = ['A-USDT-SWAP', 'B-USDT-SWAP', 'C-USDT-SWAP', 'D-USD-SWAP']
        with patch.object(scanner, 'get_swap_tickers', return_value={
            symbols[0]: {'quote_volume_usdt': 1000},
            symbols[1]: {'quote_volume_usdt': 999},
            symbols[3]: {'quote_volume_usdt': 2000},
        }):
            self.assertEqual(scanner.filter_by_24h_volume(symbols), [symbols[0]])

    def test_instruments_only_include_usdt_settlement(self):
        response = Mock(status_code=200)
        response.json.return_value = {'code': '0', 'data': [
            {'settleCcy': 'USDT', 'instId': 'BTC-USDT-SWAP'},
            {'settleCcy': 'USD', 'instId': 'BTC-USD-SWAP'},
        ]}
        with patch.object(okx_client.requests, 'get', return_value=response) as get:
            self.assertEqual(okx_client.get_usdt_swap_instruments(), ['BTC-USDT-SWAP'])
            self.assertEqual(get.call_args.kwargs['timeout'], 10)

    def test_cooldown_prevents_network_and_notification(self):
        with patch.object(scanner, 'get_usdt_swap_instruments', return_value=['BTC-USDT-SWAP']), \
             patch.object(scanner, 'filter_by_24h_volume', return_value=['BTC-USDT-SWAP']), \
             patch.object(scanner, 'load_state', return_value={'BTC-USDT-SWAP': 990}), \
             patch.object(scanner.time, 'time', return_value=1000), \
             patch.object(scanner, 'get_latest_candle') as candle, \
             patch.object(scanner, 'send_discord_message') as send:
            scanner.start_scan()
            candle.assert_not_called()
            send.assert_not_called()

    def check_delivery(self, success):
        with patch.object(scanner, 'get_usdt_swap_instruments', return_value=['BTC-USDT-SWAP']), \
             patch.object(scanner, 'filter_by_24h_volume', return_value=['BTC-USDT-SWAP']), \
             patch.object(scanner, 'load_state', return_value={}), \
             patch.object(scanner.time, 'time', return_value=10000), \
             patch.object(scanner.time, 'sleep'), \
             patch.object(scanner, 'get_latest_candle', return_value=(['0','100','104','99','103','10'], 'time')), \
             patch.object(scanner, 'send_discord_message', return_value=success) as send, \
             patch.object(scanner, 'save_state') as save:
            scanner.start_scan()
            self.assertIn('Pump Alert', send.call_args.args[0])
            self.assertIn('Volatility Alert', send.call_args.args[0])
            if success:
                save.assert_called_once_with({'BTC-USDT-SWAP': 10000})
            else:
                save.assert_not_called()

    def test_successful_delivery_records_cooldown(self):
        self.check_delivery(True)

    def test_failed_delivery_does_not_consume_cooldown(self):
        self.check_delivery(False)

    def test_missing_webhook_never_posts(self):
        with patch.object(notifier.requests, 'post') as post:
            self.assertFalse(notifier.send_discord_message('offline test'))
            post.assert_not_called()
