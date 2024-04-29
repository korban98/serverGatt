import dbus.service
from gatt_server import Service, Characteristic
from gi.repository import GLib
import numpy
import random
import json

GATT_CHRC_IFACE =              'org.bluez.GattCharacteristic1'
UART_ERROR_SERVICE_UUID =            '6e400007-b5a3-f393-e0a9-e50e24dcca9e'
UART_ERROR_RX_CHARACTERISTIC_UUID =  '6e400008-b5a3-f393-e0a9-e50e24dcca9e'
UART_ERROR_TX_CHARACTERISTIC_UUID =  '6e400009-b5a3-f393-e0a9-e50e24dcca9e'

class Error_TxCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_ERROR_TX_CHARACTERISTIC_UUID,
                                ['notify'], service)
        self.notifying = False
        self.timeout_id = None
        self.speed = 0

    def send_error_data(self):
        if not self.notifying:
            return
        
        # Genera dati del veicolo casuali
        random_index = random.randint(0, 15)
        error = ''.join('1' if i == random_index else '0' for i in range(16))

        # Costruisci la stringa JSON con i dati del veicolo
        error_data = {
            "error": error
        }     

        # Converti il dizionario in una stringa JSON
        error_json = json.dumps(error_data)

        # Converti la stringa JSON in una lista di byte
        value = [dbus.Byte(c.encode()) for c in error_json]

        # Invia i dati del veicolo
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])

        # Ripeti la chiamata ogni secondo
        GLib.timeout_add_seconds(10, self.send_error_data)

    def StartNotify(self):
        if not self.notifying:
            self.notifying = True
            self.PropertiesChanged(GATT_CHRC_IFACE, {'Notifying': True}, [])
            self.timeout_id = GLib.timeout_add_seconds(1, self.send_error_data)

    def StopNotify(self):
        if self.notifying:
            self.notifying = False
            self.PropertiesChanged(GATT_CHRC_IFACE, {'Notifying': False}, [])
            if self.timeout_id is not None:
                self.timeout_id = None

class Error_RxCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_ERROR_RX_CHARACTERISTIC_UUID,
                                ['write'], service)

    def WriteValue(self, value, options):
        print('remote: {}'.format(bytearray(value).decode()))

class UartErrorService(Service):
    def __init__(self, bus, index, name):
        Service.__init__(self, bus, index, UART_ERROR_SERVICE_UUID, True, name)
        self.add_characteristic(Error_TxCharacteristic(bus, 0, self))
        self.add_characteristic(Error_RxCharacteristic(bus, 1, self))
