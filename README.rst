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

From git
--------

Clone the git repository to obtain the main branch::

    git clone https://github.com/djnrrd/obs_streamdeck_controls.git

From releases
-------------

Download the required release from the `releases page <https://github
.com/djnrrd/obs_streamdeck_controls/releases>`_

Installing
**********

Change directory into the downloaded folder and install locally via pip. It
is recommended that you use the --user flag to install in your user directory.::

   cd obs_streamdeck_controls
   pip install --user --use-feature=in-tree-build .

This will install the command line program ``obs-streamdeck-ctl`` to your
``$HOME/.local/bin`` folder. Add::

   PATH=$PATH:$HOME/.local/bin

to your ``.bashrc`` file, if you haven't already.

Initial Setup
-------------

After installing OBS Streamdeck Controls you will need to provide information
regarding your OBS WebSockets password, and names of your Microphone, Desktop,
and alert overlay sources.  Run the setup wizard on a terminal with the
following command::

   obs-streamdeck-ctl setup

Usage
=====

::

    $ ./obs-streamdeck-ctl -h
    usage: obs-streamdeck-ctl [-h]
                      {start_stop,mute_mic,mute_desk,mute_all,panic_button,scene}
                      ...

    positional arguments:
       {start_stop,mute_mic,mute_desk,mute_all,panic_button,scene}

    optional arguments:
       -h, --help            show this help message and exit

    $ ./obs-streamdeck-ctl scene -h
    usage: obs-streamdeck-ctl scene [-h] scene_number

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