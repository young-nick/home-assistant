"""The tests for the Unifi WAP device tracker platform."""
import unittest
from unittest import mock
import urllib

from unifi import controller
import voluptuous as vol

from homeassistant.components.device_tracker import DOMAIN, unifi as unifi
from homeassistant.const import (CONF_HOST, CONF_USERNAME, CONF_PASSWORD,
                                 CONF_PLATFORM)


class TestUnifiScanner(unittest.TestCase):
    """Test the Unifiy platform."""

    @mock.patch('homeassistant.components.device_tracker.unifi.UnifiScanner')
    @mock.patch.object(controller, 'Controller')
    def test_config_minimal(self, mock_ctrl, mock_scanner):
        """Test the setup with minimal configuration."""
        config = {
            DOMAIN: unifi.PLATFORM_SCHEMA({
                CONF_PLATFORM: unifi.DOMAIN,
                CONF_USERNAME: 'foo',
                CONF_PASSWORD: 'password',
            })
        }
        result = unifi.get_scanner(None, config)
        self.assertEqual(mock_scanner.return_value, result)
        mock_ctrl.assert_called_once_with('localhost', 'foo', 'password',
                                          8443, 'v4', 'default')
        mock_scanner.assert_called_once_with(mock_ctrl.return_value)

    @mock.patch('homeassistant.components.device_tracker.unifi.UnifiScanner')
    @mock.patch.object(controller, 'Controller')
    def test_config_full(self, mock_ctrl, mock_scanner):
        """Test the setup with full configuration."""
        config = {
            DOMAIN: unifi.PLATFORM_SCHEMA({
                CONF_PLATFORM: unifi.DOMAIN,
                CONF_USERNAME: 'foo',
                CONF_PASSWORD: 'password',
                CONF_HOST: 'myhost',
                'port': 123,
                'site_id': 'abcdef01',
            })
        }
        result = unifi.get_scanner(None, config)
        self.assertEqual(mock_scanner.return_value, result)
        mock_ctrl.assert_called_once_with('myhost', 'foo', 'password',
                                          123, 'v4', 'abcdef01')
        mock_scanner.assert_called_once_with(mock_ctrl.return_value)

    def test_config_error(self):
        """Test for configuration errors."""
        with self.assertRaises(vol.Invalid):
            unifi.PLATFORM_SCHEMA({
                # no username
                CONF_PLATFORM: unifi.DOMAIN,
                CONF_HOST: 'myhost',
                'port': 123,
            })
        with self.assertRaises(vol.Invalid):
            unifi.PLATFORM_SCHEMA({
                CONF_PLATFORM: unifi.DOMAIN,
                CONF_USERNAME: 'foo',
                CONF_PASSWORD: 'password',
                CONF_HOST: 'myhost',
                'port': 'foo',  # bad port!
            })

    @mock.patch('homeassistant.components.device_tracker.unifi.UnifiScanner')
    @mock.patch.object(controller, 'Controller')
    def test_config_controller_failed(self, mock_ctrl, mock_scanner):
        """Test for controller failure."""
        config = {
            'device_tracker': {
                CONF_PLATFORM: unifi.DOMAIN,
                CONF_USERNAME: 'foo',
                CONF_PASSWORD: 'password',
            }
        }
        mock_ctrl.side_effect = urllib.error.HTTPError(
            '/', 500, 'foo', {}, None)
        result = unifi.get_scanner(None, config)
        self.assertFalse(result)

    def test_scanner_update(self):  # pylint: disable=no-self-use
        """Test the scanner update."""
        ctrl = mock.MagicMock()
        fake_clients = [
            {'mac': '123'},
            {'mac': '234'},
        ]
        ctrl.get_clients.return_value = fake_clients
        unifi.UnifiScanner(ctrl)
        ctrl.get_clients.assert_called_once_with()

    def test_scanner_update_error(self):  # pylint: disable=no-self-use
        """Test the scanner update for error."""
        ctrl = mock.MagicMock()
        ctrl.get_clients.side_effect = urllib.error.HTTPError(
            '/', 500, 'foo', {}, None)
        unifi.UnifiScanner(ctrl)

    def test_scan_devices(self):
        """Test the scanning for devices."""
        ctrl = mock.MagicMock()
        fake_clients = [
            {'mac': '123'},
            {'mac': '234'},
        ]
        ctrl.get_clients.return_value = fake_clients
        scanner = unifi.UnifiScanner(ctrl)
        self.assertEqual(set(['123', '234']), set(scanner.scan_devices()))

    def test_get_device_name(self):
        """Test the getting of device names."""
        ctrl = mock.MagicMock()
        fake_clients = [
            {'mac': '123', 'hostname': 'foobar'},
            {'mac': '234', 'name': 'Nice Name'},
            {'mac': '456'},
        ]
        ctrl.get_clients.return_value = fake_clients
        scanner = unifi.UnifiScanner(ctrl)
        self.assertEqual('foobar', scanner.get_device_name('123'))
        self.assertEqual('Nice Name', scanner.get_device_name('234'))
        self.assertEqual(None, scanner.get_device_name('456'))
        self.assertEqual(None, scanner.get_device_name('unknown'))
