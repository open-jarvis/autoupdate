"""
Copyright (c) 2021 Philipp Scheer
"""


import os
import sys
import json
import time
from jarvis import Logger, Config, MQTT

from processes import poller
from processes import downloader
from processes import installer


# initialize jarvis classes
logger = Logger("updater")
cnf = Config()
mqtt = MQTT(client_id="updater")


# initially set data server
if cnf.get("update-server", None) is None:
    cnf.set("update-server", "data.jarvis.philippscheer.com")


# define constants
DATASERVER = cnf.get("update-server", "data.jarvis.philippscheer.com")
TO_CHECK = [
    # ACTION:       if below                        >   this                            ;  then download this                               ; and install here      ; automatically install?
    [  f"http://{DATASERVER}/web/version"           ,   "/jarvis/web/version"           ,  f"http://{DATASERVER}/web-latest.tar.gz"         , "/jarvis/web"         , False ],
    [  f"http://{DATASERVER}/server/version"        ,   "/jarvis/server/version"        ,  f"http://{DATASERVER}/server-latest.tar.gz"      , "/jarvis/server"      , False ],
    [  f"http://{DATASERVER}/autoupdate/version"    ,   "/jarvis/autoupdate/version"    ,  f"http://{DATASERVER}/autoupdate-latest.tar.gz"  , "/jarvis/autoupdate"  , True  ]
]

DOWNLOADS_FOLDER = "/jarvis/downloads"
POLL_INTERVAL = 60 * 60 * 1 # CHECK EVERY HOUR FOR UPDATE
CURRENT_ACTION = "idle"


def download_pending():
    for el in TO_CHECK:
        remote, local = poller.poll(el[0], el[1])
        if remote > local:
            return True
    return False


def installation_pending():
    for fname in os.listdir(DOWNLOADS_FOLDER):
        if fname.startswith("server-latest") or fname.startswith("web-latest"):
            return True
    return False


def poll(download=False, install=False):
    global CURRENT_ACTION, DATASERVER, logger
    logger.i("polling", f"polling for updates from server {DATASERVER}")
    at_least_one_update = False
    for el in TO_CHECK:
        if el[4]:
            download = True
            install = True
        latest_file_name = el[2].split("/")[-1]
        downloaded_file_path = DOWNLOADS_FOLDER + "/" + latest_file_name
        local_installation_path = el[3]

        remote, local = poller.poll(el[0], el[1])
        if remote > local:
            at_least_one_update = True
            logger.i("available", f"update available from v{local} to v{remote}")
            mqtt.publish("jarvis/update/status", json.dumps({"type": "available", "version": {"current": str(local), "remote": str(remote) } } ))

            if download or cnf.get("auto-download-updates", False):
                CURRENT_ACTION = "downloading"
                mqtt.publish("jarvis/update/status", json.dumps({"type": "download", "action": "start", "version": {"current": str(local), "remote": str(remote) } }))
                size = downloader.store(el[2], downloaded_file_path)
                logger.i("download", f"downloaded update {remote}, size: {size}")
                mqtt.publish("jarvis/update/status", json.dumps({"type": "download", "action": "finished", "size": size, "version": {"current": str(local), "remote": str(remote) } }))
                CURRENT_ACTION = "idle"

            if install or cnf.get("auto-install-updates", False):
                CURRENT_ACTION = "installing"
                mqtt.publish("jarvis/update/status", json.dumps({"type": "installation", "action": "start", "version": {"current": str(local), "remote": str(remote) } }))
                installer.install(downloaded_file_path, local_installation_path)
                logger.i("install", f"installed update v{remote}")
                mqtt.publish("jarvis/update/status", json.dumps({"type": "installation", "action": "finished", "version": {"current": str(remote), "remote": str(remote) } }))
                if "autoupdate" in local_installation_path:
                    # automatically restart own application
                    os.execv(sys.executable, ['python3'] + [sys.argv[0]])
                else:
                    mqtt.publish("jarvis/backend/restart", json.dumps({}))
                CURRENT_ACTION = "idle"
    if not at_least_one_update:
        logger.i("polling", f"no update found on server {DATASERVER}")


#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@ 
#@        MQTT SPECIFICATIONS        @
#@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
"""
Published MQTT messages:
jarvis/update/status
    -> { type: available                              ,  version: { current: 0.0.1, remote: 0.0.2 } }
    -> { type: download,      action: start|finished  ,  version: { current: 0.0.1, remote: 0.0.2 } }
    -> { type: installation,  action: start|finished  ,  version: { current: 0.0.1, remote: 0.0.2 } }}

Listening to MQTT messages:
jarvis/update/poll          !!! NEED REPLY TO  !!!
    -> { success: true|false  , ?error = "No internet connection! "}
jarvis/update/download      !!! NEED REPLY TO !!!
    -> { success : true|false , ?error = "No update available!" }
jarvis/update/install       !!! NEED REPLY TO !!!
    -> { success: true|false ,  ?error = "No update available!" }
jarvis/update/status        !!! NEED REPLY TO !!!
    -> { current-action : idle|downloading|installing, available: download|installation|null, version: { current: 0.0.1, remote: 0.0.2 } }
"""

def _on_REQUEST(client: object, userdata: object, message: object):
    global CURRENT_ACTION, TO_CHECK
    topic = message.topic
    data = json.loads(message.payload.decode())
    # print("MQTT", topic, data)
    action = topic.split("/")[-1]

    result = { "success": True }

    if action == "poll":
        poll()
    if action == "download":
        if not download_pending():
            result["success"] = False
            result["error"] = "No update available!"
        else:
            poll(download=True)
    if action == "install":
        if not installation_pending():
            result["success"] = False
            result["error"] = "No update available!"
        else:
            poll(install=True)
    if action == "status":
        del result["success"]
        result["current-action"] = CURRENT_ACTION
        result["available"] = { "download": None, "install": None }
        remote, local = poller.poll(TO_CHECK[0][0], TO_CHECK[0][1])
        if download_pending():
            result["available"]["download"] = { "remote": str(remote), "local": str(local) }
        if installation_pending():
            result["available"]["install"] = { "remote": str(remote), "local": str(local) }     # TODO: remote version always stays the same

    if "reply-to" in data:
        mqtt.publish(data["reply-to"], json.dumps(result))


mqtt.on_message(_on_REQUEST)
mqtt.subscribe("jarvis/update/#")


while True:
    poll()
    for i in range(POLL_INTERVAL):
        time.sleep(1)