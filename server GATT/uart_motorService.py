import dbus.service
from gatt_server import Service, Characteristic
from gi.repository import GLib
import numpy
import random
import json

GATT_CHRC_IFACE =              'org.bluez.GattCharacteristic1'
UART_MOTOR_SERVICE_UUID =            '6e400004-b5a3-f393-e0a9-e50e24dcca9e'
UART_MOTOR_RX_CHARACTERISTIC_UUID =  '6e400005-b5a3-f393-e0a9-e50e24dcca9e'
UART_MOTOR_TX_CHARACTERISTIC_UUID =  '6e400006-b5a3-f393-e0a9-e50e24dcca9e'

INVERTER_STATES = ["FORWARD", "REVERSE"]

class Motor_TxCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_MOTOR_TX_CHARACTERISTIC_UUID,
                                ['notify'], service)
        self.notifying = False
        self.timeout_id = None

    def send_motor_data(self):
        if not self.notifying:
            return
        
        # Genera dati del veicolo casuali
        keyStatus = random.choice([True, False])
        inverterStatusL = random.choice(INVERTER_STATES)
        inverterStatusR = random.choice(INVERTER_STATES)
        motorTemperatureL = random.randrange(-20, 50)
        motorTemperatureR = random.randrange(-20, 50)
        currentGear = random.randrange(0, 6)

        # Costruisci la stringa JSON con i dati del veicolo
        motor_data = {
            "keyStatus": keyStatus,
            "inverterStatusL": inverterStatusL,
            "inverterStatusR": inverterStatusR,
            "motorTemperatureL": motorTemperatureL,
            "motorTemperatureR": motorTemperatureR,
            "currentGear": currentGear
        }     

        # Converti il dizionario in una stringa JSON
        motor_json = json.dumps(motor_data)

        # Converti la stringa JSON in una lista di byte
        value = [dbus.Byte(c.encode()) for c in motor_json]

        # Invia i dati del veicolo
        self.PropertiesChanged(GATT_CHRC_IFACE, {'Value': value}, [])
            
        # Ripeti la chiamata ogni secondo
        GLib.timeout_add_seconds(1, self.send_motor_data)

    def StartNotify(self):
        if not self.notifying:
            self.notifying = True
            self.PropertiesChanged(GATT_CHRC_IFACE, {'Notifying': True}, [])
            if self.timeout_id is None:
                self.timeout_id = GLib.timeout_add_seconds(1, self.send_motor_data)

    def StopNotify(self):
        if self.notifying:
            self.notifying = False
            self.PropertiesChanged(GATT_CHRC_IFACE, {'Notifying': False}, [])
            if self.timeout_id is not None:
                self.timeout_id = None
            
class Motor_RxCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        Characteristic.__init__(self, bus, index, UART_MOTOR_RX_CHARACTERISTIC_UUID,
                                ['write'], service)

    def WriteValue(self, value, options):
        print('remote: {}'.format(bytearray(value).decode()))

class UartMotorService(Service):
    def __init__(self, bus, index, name):
        Service.__init__(self, bus, index, UART_MOTOR_SERVICE_UUID, True, name)
        self.add_characteristic(Motor_TxCharacteristic(bus, 0, self))
        self.add_characteristic(Motor_RxCharacteristic(bus, 1, self))
