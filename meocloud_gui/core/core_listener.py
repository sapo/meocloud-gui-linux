# Python standard library imports
import os
import subprocess
import keyring
import locale

# GLib
from gi.repository import GLib

# Notifications
from gi.repository import Notify

# Thrift related imports
from meocloud_gui.protocol import UI
from meocloud_gui.protocol.ttypes import Account, State
from meocloud_gui.thrift_utils import ThriftListener

# Application specific imports
from meocloud_gui.settings import LOGGER_NAME, CLOUD_HOME_DEFAULT_PATH
#from meocloud.client.linux.daemon.communication import DaemonState, Events, AsyncResults
from meocloud_gui.core import api
#from meocloud.client.linux.utils import get_error_code
#from meocloud.client.linux.messages import DYING_MESSAGES
from meocloud_gui.strings import NOTIFICATIONS
import meocloud_gui.utils

# Logging
import logging
log = logging.getLogger(LOGGER_NAME)


class CoreListener(ThriftListener):
    def __init__(self, socket, core_client, ui_config, notifs_handler, app):
        handler = CoreListenerHandler(core_client, ui_config, notifs_handler, app)
        processor = UI.Processor(handler)
        super(CoreListener, self).__init__('CoreListener', socket, processor)


class CoreListenerHandler(UI.Iface):
    def __init__(self, core_client, ui_config, notifs_handler, app):
        super(CoreListenerHandler, self).__init__()
        self.core_client = core_client
        self.ui_config = ui_config
        self.notifs_handler = notifs_handler
        self.app = app
        
        Notify.init('MEOCloud')

    def start_sync(self):
        cloud_home = self.ui_config.get('Advanced', 'Folder', CLOUD_HOME_DEFAULT_PATH)
        if not cloud_home:
            log.warning('CoreListener.start_sync: no cloud_home in config, will unlink and shutdown')
            api.unlink(self.core_client, self.ui_config)
            Events.shutdown_required.set()
        else:
            if not os.path.isdir(cloud_home):
                log.warning('CoreListener.start_sync: cloud_home was found in config '
                            'with value {0} but it is not there'.format(cloud_home))
                self.update_state(DaemonState.ROOT_FOLDER_MISSING)
            else:
                self.core_client.startSync(cloud_home)
                self.update_state(DaemonState.AUTHORIZATION_OK)

    def update_state(self, new_state):
        DaemonState.current = new_state
        Events.state_changed.set()

    ### THRIFT METHODS ###

    def account(self):
        log.debug('CoreListener.account() <<<<')    
        
        account_dict = api.get_account_dict(self.ui_config)
   
        return Account(**account_dict)

    def beginAuthorization(self):
        log.debug('CoreListener.beginAuthorization() <<<<')
        GLib.idle_add(self.beginAuthorizationIdle)
        
    def beginAuthorizationIdle(self):
        self.app.setup.login_button.connect("clicked", self.beginAuthorizationBrowser)
        self.app.setup.show_all()
        
    def beginAuthorizationBrowser(self, w):
        subprocess.Popen(["xdg-open",
                        self.core_client.authorizeWithDeviceName
                        (self.app.setup.device_entry.get_text())])

    def authorized(self, account):
        log.debug('CoreListener.authorized({0}) <<<<'.format(account))
        account_dict = {
            'clientID': account.clientID,
            'authKey': account.authKey,
            'email': account.email,
            'name': account.name,
            'deviceName': account.deviceName
        }

        GLib.idle_add(lambda: keyring.set_password("meocloud", "clientID", account_dict['clientID']))
        GLib.idle_add(lambda: keyring.set_password("meocloud", "authKey", account_dict['authKey']))
        self.ui_config.put('Account', 'email', account_dict['email'])
        self.ui_config.put('Account', 'name', account_dict['name'])
        self.ui_config.put('Account', 'deviceName', account_dict['deviceName'])

        GLib.idle_add(self.app.setup.hide)
        meocloud_gui.utils.clean_cloud_path()
        meocloud_gui.utils.create_startup_file()
        self.app.restart_core()

    def endAuthorization(self):
        log.debug('CoreListener.endAuthorization() <<<<')

    def notifySystem(self, note):
        log.debug('CoreListener.notifySystem({0}, {1}) <<<<'.format(note.code, note.parameters))
        self.app.update_menu()

        def handleSystemNotification():
            if note.code == codes.STATE_CHANGED:
                log.debug('CoreListener: code: STATE_CHANGED')
                current_status = self.core_client.currentStatus()
                log.debug('CoreListener: {0}'.format(current_status))
                log.debug('CoreListener: State translation: {0}'.format(State._VALUES_TO_NAMES[current_status.state]))

                # TODO If we receive a state that indicates the wizard should be starting
                # but the user is not waiting for that (how do I know?), panic, kill everything,
                # and tell user to start over
                if current_status.state == State.WAITING:
                    self.start_sync()
                elif current_status.state == State.OFFLINE:
                    self.update_state(DaemonState.OFFLINE)
                    # TODO handle state change to offline in the middle of sync
                elif current_status.state == State.ERROR:
                    error_code = get_error_code(current_status.statusCode)
                    log.warning('CoreListener: Got error code: {0}'.format(error_code))
                    # TODO Error cases, gotta handle this someday...
                    if error_code == codes.ERROR_AUTH_TIMEOUT:
                        pass
                    elif error_code == codes.ERROR_ROOTFOLDER_GONE:
                        log.warning('CoreListener: Root folder is gone, will now shutdown')
                        self.update_state(DaemonState.ROOT_FOLDER_MISSING)
                        self.ui_config.set('dying_message', DYING_MESSAGES['root_folder_gone'])
                        Events.shutdown_required.set()
                    elif error_code == codes.ERROR_UNKNOWN:
                        pass
                    elif error_code == codes.ERROR_THREAD_CRASH:
                        pass
                    elif error_code == codes.ERROR_CANNOT_WATCH_FS:
                        log.warning('CoreListener: Cannot watch filesystem, will now shutdown')
                        self.ui_config.set('dying_message', DYING_MESSAGES['cannot_watch_fs'])
                        Events.shutdown_required.set()
                    else:
                        log.error('CoreListener: Got unknown error code: {0}'.format(error_code))
                        assert False
            elif note.code == codes.NETWORK_SETTINGS_CHANGED:
                log.debug('CoreListener: code: NETWORK_SETTINGS_CHANGED')
                # I was told this was not being used anymore...
                assert False
            elif note.code == codes.SHARED_FOLDER_ADDED:
                log.debug('CoreListener: code: SHARED_FOLDER_ADDED')
                # CLI can't handle this, no folder icons to update
            elif note.code == codes.SHARED_FOLDER_UNSHARED:
                log.debug('CoreListener: code: SHARED_FOLDER_UNSHARED')
                # CLI can't handle this, no folder icons to update
        #gevent.spawn(handleSystemNotification)

    def notifyUser(self, note):  # UserNotification note
        log.debug('CoreListener.notifyUser({0}) <<<<'.format(note))
        
        self.app.update_menu()

        loc = locale.getlocale()
        if 'pt' in loc or 'pt_PT' in loc or 'pt_BR' in loc:
            lang = 'pt'
        else:
            lang = 'en'

        if note.type != 0:
            notif_string = NOTIFICATIONS[lang][str(note.code) + 
                               "_description"].format(*note.parameters)
            notification = Notify.Notification.new(NOTIFICATIONS[lang][
                                str(note.code) + "_title"], notif_string, '')
            notification.show()

    def remoteDirectoryListing(self, statusCode, path, listing):  # i32 statusCode, string path, listing
        log.debug('CoreListener.remoteDirectoryListing({0}, {1}, {2}) <<<<'.format(statusCode, path, listing))
        print listing

    def networkSettings(self):
        log.debug('CoreListener.networkSettings() <<<<')
        return api.get_network_settings(self.ui_config)