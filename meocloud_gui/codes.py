(
    CORE_INITIALIZING,
    CORE_AUTHORIZING,
    CORE_WAITING,
    CORE_SYNCING,
    CORE_READY,
    CORE_PAUSED,
    CORE_ERROR,
    CORE_SELECTIVE_SYNC,
    CORE_RESTARTING,
    CORE_OFFLINE
) = xrange(0, 10)

# TODO Make sure we're handling all these
# System notifications
(
    STATE_CHANGED,
    NETWORK_SETTINGS_CHANGED,
    SHARED_FOLDER_ADDED,
    SHARED_FOLDER_UNSHARED,
    SHARE_LINK_CREATED,
    SHARE_FOLDER_REQUESTED,
    VIEW_LINK_CREATED
) = xrange(7)

# Statuses
(
    STATUS_OK,
    ERROR_AUTH_TIMEOUT,
    ERROR_ROOTFOLDER_GONE,
    ERROR_UNKNOWN,
    ERROR_THREAD_CRASH,
    ERROR_CANNOT_WATCH_FS
) = xrange(6)

# Synchronizing statuses
SYNC_INDEXING = 0x00000001
SYNC_UPLOADING = 0x00000002
SYNC_DOWNLOADING = 0x00000004
SYNC_LISTING_CHANGES = 0x00000008

SYNC_ALL = (SYNC_INDEXING |
            SYNC_UPLOADING |
            SYNC_DOWNLOADING |
            SYNC_LISTING_CHANGES)

## User notifications
# File changes
(
    USER_NOTIFY_FILE_ADDED,
    USER_NOTIFY_FILE_DELETED,
    USER_NOTIFY_FILE_UPDATED,
    USER_NOTIFY_FILES_ADDED,
    USER_NOTIFY_FILES_DELETED,
    USER_NOTIFY_FILES_UPDATED,
    USER_NOTIFY_FILES_CHANGED,
    USER_NOTIFY_CONNECTION_LOST,
) = xrange(200, 208)

# Shared folder changes
(
    USER_NOTIFY_SHARED_FOLDER_ADDED,
    USER_NOTIFY_SHARED_FOLDER_DELETED,
    USER_NOTIFY_SHARED_FOLDER_UNSHARED
) = xrange(250, 253)

# Errors
(
    USER_NOTIFY_QUOTA_EXCEEDED,
    USER_NOTIFY_CANNOT_SYNC_PERM,
    USER_NOTIFY_CANNOT_SYNC_SPACE,
    USER_NOTIFY_CANNOT_SYNC_BUSY,
    USER_NOTIFY_CANNOT_WATCH_FS
) = xrange(500, 505)

STR_OK = 'OK'
STR_ERROR = 'ERR'
STR_NOTFOUND = 'NOTFOUND'

# Message types
USER_NOTIFY_TYPE_RESET = 0
USER_NOTIFY_TYPE_MASK_PERSISTENT = 1 << 0
USER_NOTIFY_TYPE_MASK_MENU_BAR = 1 << 1
USER_NOTIFY_TYPE_MASK_ALERT_WINDOW = 1 << 2
USER_NOTIFY_TYPE_MASK_BALLOON = 1 << 3

# Remote directory listing codes
REMOTE_DIR_LIST_OK = 0
REMOTE_DIR_LIST_ERROR = 1
