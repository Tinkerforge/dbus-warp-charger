dbus-warp-charger
=================

**Work in progress**

This repo integrates a WARP Charger Wallbox into a Victron Venus OS device (e.g. Cerbo GX). The integration
is using the Victron evcharger model (com.victronenergy.evcharger) and is basically mimic a Victron wallbox.
Therefore switching between 1-phase and 3-phase charging is not supported, since it is not supported by Victrons wallbox.

It is possible to see the current charging status (not connected, connected, rfid missing, charging etc.) and you can control the maximum charging current (Settings->Max charging current).
As charge mode you can select between manual and automatic (scheduled is not implemented right now). Manual mode is basically the normal charging mode where you can control the charging current and start/stop the charging process.
In automatic mode pv excess mode is selected. So this option is only available if pv excess mode is available at the WARP charger. If the wallbox is a WARP Charger Pro wallbox also the energy measurements are shown.

Repository Overview
-------------------

.. DO NOT EDIT THIS OVERVIEW MANUALLY! CHANGE https://github.com/Tinkerforge/esp32-firmware/repo_overview.rst AND COPY THAT BLOCK INTO ALL REPOS LISTED BELOW. TODO: AUTOMATE THIS

Software
~~~~~~~~
- `esp32-firmware <https://github.com/Tinkerforge/esp32-firmware>`__  **Please report any issues concerning WARP hard- and software here!** Source code of the ESP32 firmware shared between all WARP Chargers and Energy Managers

- `tfjson <https://github.com/Tinkerforge/tfjson>`__ SAX style JSON serializer and deserializer
- `tfmodbustcp <https://github.com/Tinkerforge/tfmodbustcp>`__ Modbus TCP server and client implementation
- `tfocpp <https://github.com/Tinkerforge/tfocpp>`__ OCPP 1.6 implementation
- `tftools <https://github.com/Tinkerforge/tftools>`__ Miscellaneous tools and helpers

- `esp32-remote-access <https://github.com/Tinkerforge/esp32-remote-access>`__ Source code of the my.warp-charger.com remote access server

- `warp-charger <https://github.com/Tinkerforge/warp-charger>`__ The source code of (docs.)warp-charger.com and the printed manual, released firmwares, datasheets and documents, as well as some tools and hardware design files
- `api.warp-charger.com <https://github.com/Tinkerforge/api.warp-charger.com>`__ Serves APIs that are used by WARP Chargers to obtain relevant public information like day ahead prices
- `vislog.warp-charger.com <https://github.com/Tinkerforge/vislog.warp-charger.com>`__ Visualizes WARP Charger logs and EVSE debug protocols
- `dbus-warp-charger <https://github.com/Tinkerforge/dbus-warp-charger>`__ Integrates WARP Chargers into a Victron Energy Venus OS device (e.g. Cerbo GX)

WARP Charger Hardware
~~~~~~~~~~~~~~~~~~~~~~

- `esp32-brick <https://github.com/Tinkerforge/esp32-brick>`__ Hardware design files of the ESP32 Brick
- `evse-bricklet <https://github.com/Tinkerforge/evse-bricklet>`__  Firmware source code and hardware design files of the EVSE Bricklet
- `rs485-bricklet <https://github.com/Tinkerforge/rs485-bricklet>`__ Firmware source code and hardware design files of the RS485 Bricklet

WARP2 Charger Hardware
~~~~~~~~~~~~~~~~~~~~~~

- `esp32-ethernet-brick <https://github.com/Tinkerforge/esp32-ethernet-brick>`__ Hardware design files of the ESP32 Ethernet Brick
- `evse-v2-bricklet <https://github.com/Tinkerforge/evse-v2-bricklet>`__ Firmware source code and hardware design files of the EVSE 2.0 Bricklet
- `nfc-bricklet <https://github.com/Tinkerforge/nfc-bricklet>`__ Firmware source code and hardware design files of the NFC Bricklet

WARP3 Charger Hardware
~~~~~~~~~~~~~~~~~~~~~~

- `warp-esp32-ethernet-brick <https://github.com/Tinkerforge/warp-esp32-ethernet-brick>`__ Hardware design files of the WARP ESP32 Ethernet Brick
- `evse-v3-bricklet <https://github.com/Tinkerforge/evse-v3-bricklet>`__ Firmware source code and hardware design files of the EVSE 3.0 Bricklet
- `nfc-bricklet <https://github.com/Tinkerforge/nfc-bricklet>`__ Firmware source code and hardware design files of the NFC Bricklet

WARP Energy Manager Hardware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- `esp32-ethernet-brick <https://github.com/Tinkerforge/esp32-ethernet-brick>`__ Hardware design files of the ESP32 Ethernet Brick
- `warp-energy-manager-bricklet <https://github.com/Tinkerforge/warp-energy-manager-bricklet>`__ Firmware source code and hardware design files of the WARP Energy Manager Bricklet

WARP Energy Manager 2.0 Hardware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- `esp32-ethernet-brick <https://github.com/Tinkerforge/esp32-ethernet-brick>`__ Hardware design files of the ESP32 Ethernet Brick
- `warp-energy-manager-v2-bricklet <https://github.com/Tinkerforge/warp-energy-manager-v2-bricklet>`__ Firmware source code and hardware design files of the WARP Energy Manager 2.0 Bricklet
- `warp-front-panel-bricklet <https://github.com/Tinkerforge/warp-front-panel-bricklet>`__ Firmware source code and hardware design files of the WARP Front Panel Bricklet

Forked/patched projects
~~~~~~~~~~~~~~~~~~~~~~~

- `arduino-esp32 <https://github.com/Tinkerforge/arduino-esp32>`__
- `esp32-arduino-libs <https://github.com/Tinkerforge/esp32-arduino-libs>`__
- `WireGuard-ESP32-Arduino <https://github.com/Tinkerforge/WireGuard-ESP32-Arduino>`__

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
