#######################
OBS Streamdeck Controls
#######################

Introduction
============

A command line tool for controlling OBS Studio via the `OBS WebSockets API
<https://github.com/Palakis/obs-websocket>`_, designed for use with tools
such as the Elgato Stream Deck, notably on Linux when using the
`streamdeck_ui <https://timothycrosley.github.io/streamdeck-ui/>`_ program.

Features
********

* Start/Stop streaming
* Mute/Unmute Microphone and Desktop Audio sources, including supporting custom audio sources
* Scene switching
* Panic Button to combat the effects of hate raids.

Installation
============

Requirements
************

* Python >= 3.6
* Pip and Internet access
* `OBS WebSockets API <https://github.com/Palakis/obs-websocket>`_

Streamlabs OBS/SLOBS is *not* supported

Downloading
***********

Clone the git repository to obtain the main branch::

    git clone https://github.com/djnrrd/obs_streamdeck_controls.git

Installing
**********

Currently this program is designed to work in a virtual environment with a
shell script as a wrapper.

Preparing the virtual environment
---------------------------------

::

    cd obs_streamdeck_controls
    chmod +x sd_controls.sh
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install --upgrade setuptools
    pip install simpleobsws

Preparing the ini file
----------------------

* Copy sd_controls.ini.example to sd_controls.ini
* Update obsws_password to use your password for OBS WebSockets
* Update mic_source and desktop_source if required
* Update alert_sources to match the Browser sources that are used for your alert overlays.  Multiple sources can be separated with a colon (:)

Usage
=====

::

    $ ./sd_controls.sh -h
    usage: sd_controls.py [-h]
                      {start_stop,mute_mic,mute_desk,mute_all,panic_button,scene}
                      ...

    positional arguments:
       {start_stop,mute_mic,mute_desk,mute_all,panic_button,scene}

    optional arguments:
       -h, --help            show this help message and exit

    $ ./sd_controls scene -h
    usage: sd_controls.py scene [-h] scene_number

    positional arguments:
       scene_number

    optional arguments:
       -h, --help    show this help message and exit

Arguments
*********

* start_stop - Start/Stop the stream
* mute_mic - Mute/Unmute the Microphone source
* mute_desk - Mute/Unmute the Desktop audio source
* mute_all - Mute/Unmute both Desktop and Microphone sources
* panic_button - Disable/Enable alert sources in case of hate raids
* scene X - The scene number to select (from the top down)