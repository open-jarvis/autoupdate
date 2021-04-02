# Autoupdater

This script checks for the newest Jarvis version from [http://data.jarvis.philippscheer.com](http://data.jarvis.philippscheer.com) and updates automatically if a new update is being published.


## Docker Installation

This code is being used in the [official Jarvis Docker Container](https://github.com/open-jarvis/docker) to update Jarvis services.  
The Autoupdater Docker Container can be found [here](https://hub.docker.com/r/openjarvis/autoupdater).


## Normal installation

``` bash
git clone https://github.com/open-jarvis/autoupdater
cd autoupdater
python3 autoupdater.py
# make sure this script always runs by adding it to 
# crontab @reboot or another high availablity service
```


### MQTT Endpopints

``` bash
Published MQTT messages:
jarvis/update/status
    -> { type: available                             , version: { current: 0.0.1, remote: 0.0.2 } }
    -> { type: download,      action: start|finished , version: { current: 0.0.1, remote: 0.0.2 } }
    -> { type: installation,  action: start|finished , version: { current: 0.0.1, remote: 0.0.2 } }}

Listening to MQTT messages:
jarvis/update/poll          !!! NEED REPLY TO  !!!
    -> { success: true|false  , ?error = "No internet connection! "}
jarvis/update/download      !!! NEED REPLY TO !!!
    -> { success : true|false , ?error = "No update available!" }
jarvis/update/install       !!! NEED REPLY TO !!!
    -> { success: true|false ,  ?error = "No update available!" }
jarvis/update/status        !!! NEED REPLY TO !!!
    -> { current-action : idle|downloading|installing, available: download|installation|null, version: { current: 0.0.1, remote: 0.0.2 } }
```
