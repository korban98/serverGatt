import dbus.service
from gatt_server import Service, Characteristic
from gi.repository import GLib
import numpy
import random
import json

GATT_CHRC_IFACE =              'org.bluez.GattCharacteristic1'
UART_BATTERY_SERVICE_UUID =            '6e400001-b5a3-f393-e0a9-e50e24dcca9e'
UART_BATTERY_RX_CHARACTERISTIC_UUID =  '6e400002-b5a3-f393-e0a9-e50e24dcca9e'
UART_BATTERY_TX_CHARACTERISTIC_UUID =  '6e400003-b5a3-f393-e0a9-e50e24dcca9e'

CHARGE_STATES = ["NOT_SIGNIFICANT", "CHARGING", "BALANCING", "END_OF_CHARGE"]

class Battery_TxCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_BATTERY_TX_CHARACTERISTIC_UUID,
                                ['notify'], service)
        self.notifying = False
        self.timeout_id = None

    def send_battery_data(self):
        if not self.notifying:
            return
        
         # Genera dati del veicolo casuali
        stateOfHealth = random.randrange(0, 100)
        stateOfCharge = random.randrange(0, 100)
        remainingEnergy = random.randrange(0, 100000)
        chargeState = random.choice(CHARGE_STATES)
        
        # Costruisci la stringa JSON con i dati della batteria
        battery_data = {
            "stateOfHealth": stateOfHealth,
            "stateOfCharge": stateOfCharge,
            "remainingEnergy": remainingEnergy,
            "chargeState": chargeState
        }

        # Converti il dizionario in una stringa JSON
        battery_json = json.dumps(battery_data)

        # Converti la stringa JSON in una lista di byte
        value = [dbus.Byte(c.encode()) for c in battery_json]

        # Invia i dati del veicolo
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])

        # Ripeti la chiamata ogni secondo
        GLib.timeout_add_seconds(1, self.send_battery_data)

    def StartNotify(self):
        if not self.notifying:
            self.notifying = True
            self.PropertiesChanged(GATT_CHRC_IFACE, {'Notifying': True}, [])
            if self.timeout_id is None:
                self.timeout_id = GLib.timeout_add_seconds(1, self.send_battery_data)

    def StopNotify(self):
        if self.notifying:
            self.notifying = False
            self.PropertiesChanged(GATT_CHRC_IFACE, {'Notifying': False}, [])
            if self.timeout_id is not None:
                self.timeout_id = None

class Battery_RxCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_BATTERY_RX_CHARACTERISTIC_UUID,
                                ['write'], service)

    def WriteValue(self, value, options):
        print('remote: {}'.format(bytearray(value).decode()))

class UartBatteryService(Service):
    def __init__(self, bus, index, name):
        Service.__init__(self, bus, index, UART_BATTERY_SERVICE_UUID, True, name)
        self.add_characteristic(Battery_TxCharacteristic(bus, 0, self))
        self.add_characteristic(Battery_RxCharacteristic(bus, 1, self))
