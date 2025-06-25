#!/usr/bin/env python

# import normal packages
import platform
import logging
import sys
import os
if sys.version_info.major == 2:
    import gobject
else:
    from gi.repository import GLib as gobject
import time
import math
import requests # for http GET
import configparser # for config/ini file

# our own packages from victron
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService

VoltageLNAvg = 7
CurrentLSumImExSum = 33
PowerActiveL1ImExDiff = 39
PowerActiveL2ImExDiff = 48
PowerActiveL3ImExDiff = 57
PowerActiveLSumImExDiff = 74
EnergyActiveLSumImport = 209
EnergyActiveLSumImExSum = 213
FrequencyLAvg = 364

index_map = [
    ('/Ac/L1/Power', PowerActiveL1ImExDiff),
    ('/Ac/L2/Power', PowerActiveL2ImExDiff),
    ('/Ac/L3/Power', PowerActiveL3ImExDiff),
    ('/Ac/Power', PowerActiveLSumImExDiff),
    ('/Ac/Voltage', VoltageLNAvg),
    ('/Ac/Frequency', FrequencyLAvg),
    ('/Current', CurrentLSumImExSum)
]

"""
Wallbox settings:

PV Excess needs to be activated and configured to use "auto" mode (PV Excess)
External control also needs to be activated
"""

class DbusWARPChargerService:
    def __init__(self, servicename, paths, productname='warp-charger', connection='WARP-Charger HTTP API service'):
        config = self._getConfig()
        deviceinstance = int(config['DEFAULT']['Deviceinstance'])
        self.ip = str(config['DEFAULT']['IP'])
        self.acposition = int(config['DEFAULT']['Position'])

        self._dbusservice = VeDbusService("{}.http_{:02d}".format(servicename, deviceinstance), register=False)
        self._paths = paths

        self.enable_charging = True # start/stop

        logging.debug("%s /DeviceInstance = %d" % (servicename, deviceinstance))

        # get general data from WARP-Charger
        version = self.getWARPChargerData("/info/version")
        name = self.getWARPChargerData("/info/name")
        displayname = self.getWARPChargerData("/info/display_name")

        # Create the management objects, as specified in the ccgx dbus-api document
        self._dbusservice.add_path('/Mgmt/ProcessName', __file__)
        self._dbusservice.add_path('/Mgmt/ProcessVersion', 'Unkown version, and running on Python ' + platform.python_version())
        self._dbusservice.add_path('/Mgmt/Connection', connection)

        # Create the mandatory objects
        self._dbusservice.add_path('/DeviceInstance', deviceinstance)
        self._dbusservice.add_path('/ProductId', 0xFFFF)
        self._dbusservice.add_path('/ProductName', name["display_type"])
        self._dbusservice.add_path('/CustomName', displayname["display_name"])
        self._dbusservice.add_path('/FirmwareVersion', version['firmware'])
        self._dbusservice.add_path('/Serial', name["uid"])
        self._dbusservice.add_path('/HardwareVersion', name["type"])
        self._dbusservice.add_path('/Connected', 1)
        self._dbusservice.add_path('/UpdateIndex', 0)
        self._dbusservice.add_path('/Position', self.acposition) # 0: ac out, 1: ac in

        # add path values to dbus
        for path, settings in self._paths.items():
            self._dbusservice.add_path(path, settings['initial'], gettextcallback=settings['textformat'], writeable=True, onchangecallback=self._handlechangedvalue)

        self._dbusservice.register()

        # last update
        self._lastUpdate = 0

        # charging time in float
        self._chargingTime = 0.0

        # add _update function 'timer'
        gobject.timeout_add(self._getUpdateInterval() * 1000, self._update)

        # add _signOfLife 'timer' to get feedback in log every 5minutes
        gobject.timeout_add(self._getSignOfLifeInterval()*60*1000, self._signOfLife)

        self._meter_config = None
        self._meter_value_indices = None
        self._energy_import_meter_value_index = None
        self._last_evse_uptime_start = None
        self._last_evse_uptime_start_change = None

    def _getConfig(self):
        config = configparser.ConfigParser()
        config.read("%s/config.ini" % (os.path.dirname(os.path.realpath(__file__))))
        return config


    def _getSignOfLifeInterval(self):
        config = self._getConfig()
        value = config['DEFAULT']['SignOfLifeLog']

        if not value:
            value = 0

        return int(value)

    def _getUpdateInterval(self):
        config = self._getConfig()
        value = config['DEFAULT']['UpdateInterval']

        if not value:
            value = 1

        return int(value)


    def _handlechangedvalue(self, path, value):
        logging.critical("someone else updated %s to %s" % (path, value))

        if path == '/MaxCurrent':
            self.setWARPChargerValue("/evse/global_current", {"current": int(value * 1000)})
        elif path == '/SetCurrent':
            self.setWARPChargerValue("/evse/external_current", {"current": int(value * 1000)})
        elif path == '/AutoStart':
            if value == 0:
                self.setWARPChargerValue("/evse/auto_start_charging", {"auto_start_charging": False})
            else:
                self.setWARPChargerValue("/evse/auto_start_charging", {"auto_start_charging": True})
        elif path == '/Mode':
            if value == 0: # manual
                self.setWARPChargerValue("/power_manager/charge_mode", {"mode": 0}) # fast
            elif value == 1: # automatic
                self.setWARPChargerValue("/power_manager/charge_mode", {"mode": 2}) # pv
            elif value == 2:
                pass # schedule not implemented

        elif path == '/StartStop':
            if value == 0:
                self.setWARPChargerValue("/evse/stop_charging", {})
                self.enable_charging = False
            else:
                self.setWARPChargerValue("/evse/start_charging", {})
                self.enable_charging = True


    def setWARPChargerValue(self, path, dat):
        requests.put(url = "http://" + self.ip + path, json = dat, timeout=5)

    def getWARPChargerData(self, path):
        return requests.get(url="http://" + self.ip + path, timeout=5).json()

    def _signOfLife(self):
        self._update_meter_value_id_cache()
        logging.info("--- Start: sign of life ---")
        logging.info("Last _update() call: %s" % (self._lastUpdate))
        logging.info("Last '/Ac/Power': %s" % (self._dbusservice['/Ac/Power']))
        logging.info("--- End: sign of life ---")
        return True

    def _update_meter_value_id_cache(self):
        self._meter_value_indices = None
        self._energy_import_meter_value_index = None

        config = self.getWARPChargerData("/meters/0/config")

        if config is None or config[1] is None:
            return

        value_ids = self.getWARPChargerData("/meters/0/value_ids")
        if value_ids is None:
            return

        if self._meter_value_indices is None:
            self._meter_value_indices = [0] * len(index_map)

        for i, tup in enumerate(index_map):
            _, mvID = tup
            try:
                self._meter_value_indices[i] = value_ids.index(mvID)
            except ValueError:
                self._meter_value_indices[i] = None

        try:
            self._energy_import_meter_value_index = value_ids.index(EnergyActiveLSumImport)
        except ValueError:
            try:
                self._energy_import_meter_value_index = value_ids.index(EnergyActiveLSumImExSum)
            except ValueError:
                pass

    def _update(self):
        try:
            if self._meter_value_indices is None:
                self._update_meter_value_id_cache()

            # read out meter values (only WARP Pro Charger)

            energy_import = float('nan')
            if self._meter_value_indices is not None:
                # read meter data
                values = self.getWARPChargerData("/meters/0/values")
                if values is not None:
                    for i, idx in enumerate(self._meter_value_indices):
                        if idx is None:
                            continue
                        self._dbusservice[index_map[i][0]] = values[idx]

                    if self._energy_import_meter_value_index is not None:
                        energy_import = values[self._energy_import_meter_value_index]

            # read mode stuff
            pmcm = self.getWARPChargerData("/power_manager/charge_mode")
            if pmcm is not None:
                if pmcm["mode"] == 0: # fast
                    self._dbusservice['/Mode'] = 0 # manual
                elif pmcm["mode"] == 1: # disabled
                    self._dbusservice['/Mode'] = 0 # manual
                    self._dbusservice['/StartStop'] = 0 # disabled
                elif pmcm["mode"] == 2 or pmcm["mode"] == 3: # pv / pv+min
                    self._dbusservice['/Mode'] = 1 # automatic

            # Cache evse_uptime_start changes to not have to download evse/low_level_state
            cc = self.getWARPChargerData("/charge_tracker/current_charge")
            if cc is not None:
                evse_uptime_start = cc["evse_uptime_start"]

                # TODO fetch evse/low_level_state["time_since_state_change"]
                # if self._last_evse_uptime_start is None and evse_uptime_start is not 0
                # That means that the script restarted while charging

                if self._last_evse_uptime_start != evse_uptime_start:
                    self._last_evse_uptime_start = evse_uptime_start
                    self._last_evse_uptime_start_change = time.time()

                self._dbusservice['/ChargingTime'] = 0 if evse_uptime_start == 0 else (time.time() - self._last_evse_uptime_start_change)
                self._dbusservice['/Ac/Energy/Forward'] = float(energy_import - cc["meter_start"]) # calculate charged energy

            esl = self.getWARPChargerData("/evse/slots")
            if esl is not None:
                self._dbusservice['/MaxCurrent'] = float(esl[5]["max_current"] / 1000.0) # external config slot
                self._dbusservice['/SetCurrent'] = float(esl[8]["max_current"] / 1000.0) # external config slot
                self._dbusservice['/AutoStart'] = 0 if esl[4]["clear_on_disconnect"] else 1 # autostart/button slot

            es = self.getWARPChargerData("/evse/state")
            if es["charger_state"] == 0: # not connected
                self._dbusservice['/Status'] = 0 # not connected
            elif es["charger_state"] == 1: # connected - wait for ok
                self._dbusservice['/Status'] = 5 # waiting for RFID
            elif es["charger_state"] == 2: # ready to charge
                self._dbusservice['/Status'] = 6 # waiting for start
            elif es["charger_state"] == 3: # charging
                self._dbusservice['/Status'] = 2 # charging
            elif es["charger_state"] == 4: # error
                if es["error_state"] == 2:
                    self._dbusservice['/Status'] = 8 # PLACEHOLDER: ground test error
                elif es["error_state"] == 3:
                    self._dbusservice['/Status'] = 11 # residual current
                elif es["error_state"] == 4:
                    self._dbusservice['/Status'] = 9 # welded contacts
                elif es["error_state"] == 5:
                    self._dbusservice['/Status'] = 10 # communication error
                else:
                    self._dbusservice['/Status'] = 8 # PLACEHOLDER: ground test error
            else:
                self._dbusservice['/Status'] = 8 # PLACEHOLDER: ground test error

            if not self.enable_charging:
                self._dbusservice['/StartStop'] = 0
            else:
                self._dbusservice['/StartStop'] = 1

            # logging
            #logging.debug("Wallbox Consumption (/Ac/Power): %s" % (self._dbusservice['/Ac/Power']))
            #logging.debug("Wallbox Forward (/Ac/Energy/Forward): %s" % (self._dbusservice['/Ac/Energy/Forward']))
            #logging.debug("---")

            # increment UpdateIndex - to show that new data is available
            index = self._dbusservice['/UpdateIndex'] + 1  # increment index
            if index > 255:   # maximum value of the index
                index = 0       # overflow from 255 to 0
            self._dbusservice['/UpdateIndex'] = index

            # update lastupdate vars
            self._lastUpdate = time.time()

            #TODO: missing values
            """
            '/PCB/Temperature',
            '/MCU/Temperature',
            '/Handle/Temperature',
            '/History/ChargingCycles',
            '/History/ConnectorCycles',
            '/History/Ac/Energy/Forward',
            '/History/Uptime',
            '/History/ChargingTime',
            '/History/Alerts',
            '/History/AverageStartupTemperature',
            '/History/AbortedChargingCycles',
            '/History/ThermalFoldbacks'
            """

        except Exception as e:
            logging.critical('Error at %s', '_update', exc_info=e)
            logging.critical(e)

        # return true, otherwise add_timeout will be removed from GObject - see docs http://library.isr.ist.utl.pt/docs/pygtk2reference/gobject-functions.html#function-gobject--timeout-add
        return True


def main():
    # configure logging
    logging.basicConfig(  format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                          datefmt='%Y-%m-%d %H:%M:%S',
                          level=logging.INFO,
                          handlers=[
                              logging.FileHandler("%s/current.log" % (os.path.dirname(os.path.realpath(__file__)))),
                              logging.StreamHandler()
                          ]
                        )

    try:
        logging.info("Start")

        from dbus.mainloop.glib import DBusGMainLoop
        # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
        DBusGMainLoop(set_as_default=True)

        # formatting
        _kwh = lambda p, v: (str(round(v, 2)) + 'kWh')
        _a = lambda p, v: (str(round(v, 1)) + 'A')
        _w = lambda p, v: (str(round(v, 1)) + 'W')
        _v = lambda p, v: (str(round(v, 1)) + 'V')
        _degC = lambda p, v: (str(v) + '°C')
        _s = lambda p, v: (str(v) + 's')
        _n = lambda p, v: (str(v))

        # start our main-service
        pvac_output = DbusWARPChargerService(
          servicename='com.victronenergy.evcharger',
          paths={
            '/Ac/Power': {'initial': 0, 'textformat': _w},
            '/Ac/L1/Power': {'initial': 0, 'textformat': _w},
            '/Ac/L2/Power': {'initial': 0, 'textformat': _w},
            '/Ac/L3/Power': {'initial': 0, 'textformat': _w},
            '/Ac/Voltage': {'initial': 0, 'textformat': _v},
            '/Ac/Frequency': {'initial': 0, 'textformat': _v},
            '/Ac/Energy/Forward': {'initial': 0, 'textformat': _kwh},

            '/Current': {'initial': 0, 'textformat': _a},
            '/MaxCurrent': {'initial': 0, 'textformat': _a},
            '/SetCurrent': {'initial': 0, 'textformat': _a},

            '/AutoStart': {'initial': 0, 'textformat': _n},
            '/ChargingTime': {'initial': 0, 'textformat': _s},
            '/Mode': {'initial': 0, 'textformat': _n},
            '/StartStop': {'initial': 0, 'textformat': _n},
            '/Status': {'initial': 0, 'textformat': _n},
          }
        )

        logging.info('Connected to dbus, and switching over to gobject.MainLoop() (= event based)')
        mainloop = gobject.MainLoop()
        mainloop.run()
    except Exception as e:
        logging.critical('Error at %s', 'main', exc_info=e)

if __name__ == "__main__":
    main()
