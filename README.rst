dbus-warp-charger
=================

**Work in progress**

This repo integrates a WARP Charger Wallbox into a Victron Venus OS device (e.g. Cerbo GX). The integration
is using the Victron evcharger model (com.victronenergy.evcharger) and is basically mimic a Victron wallbox.
Therefore switching between 1-phase and 3-phase charging is not supported, since it is not supported by Victrons wallbox.

It is possible to see the current charging status (not connected, connected, rfid missing, charging etc.) and you can control the maximum charging current (Settings->Max charging current).
As charge mode you can select between manual and automatic (scheduled is not implemented right now). Manual mode is basically the normal charging mode where you can control the charging current and start/stop the charging process.
In automatic mode pv excess mode is selected. So this option is only available if pv excess mode is available at the WARP charger. If the wallbox is a WARP Charger Pro wallbox also the energy measurements are shown.

Setup
-----

Copy the files to the data folder ``/data/`` e.g. ``/data/dbus-warp-charger``.
Afterwards modify the ``config.ini`` file such that it points to your WARP charger.
After that call the install.sh script. 

At the WARP charger webinterface enable ``external control`` (Wallbox->Einstellungen->Externe Steuerung), press save and restart the wallbox.

Discussions on Tinkerunity (forum)
----------------------------------

This project is discussed in our forum:
- https://www.tinkerunity.org/topic/12371-integration-in-victron-vrm/#comment-55709

Credit
------

This project is based on the go-e charger integration repo: https://github.com/vikt0rm/dbus-goecharger
