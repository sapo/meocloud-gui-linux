import urlparse
import threading
import keyring

# GLib and Gdk
from gi.repository import GLib, Gdk

from meocloud_gui.protocol.ttypes import NetworkSettings, Account
#from meocloud_gui.settings import RC4_KEY
#from meocloud.client.linux.daemon import rc4
from meocloud_gui.utils import get_proxy, get_ratelimits


def get_account_dict(ui_config):
    account_dict = dict()

    class AccountCallback: 
        def __init__(self, ui_config):
            self.ui_config = ui_config 
            self.event = threading.Event() 
            self.result = None 
        def __call__(self): 
            Gdk.threads_enter() 
            try:
                account_dict['clientID'] = keyring.get_password('meocloud', 'clientID')
                account_dict['authKey'] = keyring.get_password('meocloud', 'authKey')
                account_dict['email'] = self.ui_config.get('Account', 'email', None)
                account_dict['name'] = self.ui_config.get('Account', 'name', None)
                account_dict['deviceName'] = self.ui_config.get('Account', 'deviceName', None)
            finally: 
                Gdk.flush() 
                Gdk.threads_leave() 
                self.event.set() 
            return False
    
    # Keyring must run in the main thread,
    # otherwise we segfault.
    account_callback = AccountCallback(ui_config)
    account_callback.event.clear()
    GLib.idle_add(account_callback)
    account_callback.event.wait()
    
    return account_dict


def unlink(core_client, ui_config):
    account_dict = get_account_dict(ui_config)
    if account_dict['clientID'] and account_dict['authKey']:
        account = Account(**account_dict)
        GLib.idle_add(lambda: keyring.delete_password('meocloud', 'clientID'))
        GLib.idle_add(lambda: keyring.delete_password('meocloud', 'authKey'))
        ui_config.put('Account', 'email', '')
        ui_config.put('Account', 'name', '')
        ui_config.put('Account', 'deviceName', '')
        core_client.unlink(account)
        return True
    return False


def get_network_settings(ui_config):
    network_settings = NetworkSettings()

    download_limit, upload_limit = get_ratelimits(ui_config)
    network_settings.downloadBandwidth = download_limit * 1024  # KB/s to B/s
    network_settings.uploadBandwidth = upload_limit * 1024  # KB/s to B/s

    proxy_url = get_proxy(ui_config)
    if proxy_url:
        try:
            parsed = urlparse.urlparse(proxy_url)
        except Exception:
            # Something went wrong while trying to parse proxy_url
            # Ignore and just don't use any proxy
            pass
        else:
            if parsed.hostname:
                network_settings.proxyAddress = parsed.hostname
                network_settings.proxyType = 'http'
                network_settings.proxyPort = parsed.port or 3128
                network_settings.proxyUser = parsed.user if hasattr(parsed, 'user') else ''
                network_settings.proxyPassword = parsed.password if hasattr(parsed, 'password') else ''

    return network_settings