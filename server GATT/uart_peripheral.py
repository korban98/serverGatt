import sys
import dbus, dbus.mainloop.glib
from gi.repository import GLib
from uart_errorService import UartErrorService
from uart_batteryService import UartBatteryService
from uart_motorService import UartMotorService
from advertisement import Advertisement
from advertisement import register_ad_cb, register_ad_error_cb
from gatt_server import register_app_cb, register_app_error_cb

BLUEZ_SERVICE_NAME =           'org.bluez'
DBUS_OM_IFACE =                'org.freedesktop.DBus.ObjectManager'
LE_ADVERTISING_MANAGER_IFACE = 'org.bluez.LEAdvertisingManager1'
GATT_MANAGER_IFACE =           'org.bluez.GattManager1'
GATT_CHRC_IFACE =              'org.bluez.GattCharacteristic1'
UART_ERROR_SERVICE_UUID =      '6e400007-b5a3-f393-e0a9-e50e24dcca9e'
UART_BATTERY_SERVICE_UUID =    '6e400001-b5a3-f393-e0a9-e50e24dcca9e'
UART_MOTOR_SERVICE_UUID =      '6e400004-b5a3-f393-e0a9-e50e24dcca9e'
LOCAL_NAME =                   'rpi-gatt-server'
mainloop = None

class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = '/'
        self.services = []
        dbus.service.Object.__init__(self, bus, self.path)
        self.add_service(UartErrorService(bus, 0, 'ERROR'))
        self.add_service(UartBatteryService(bus, 1, 'BATTERY'))
        self.add_service(UartMotorService(bus, 2, 'MOTOR'))

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature='a{oa{sa{sv}}}')
    def GetManagedObjects(self):
        response = {}
        for service in self.services:
            response[service.get_path()] = service.get_properties()
            chrcs = service.get_characteristics()
            for chrc in chrcs:
                response[chrc.get_path()] = chrc.get_properties()
        return response

class UartAdvertisement(Advertisement):
    def __init__(self, bus, index, uuid, service_name):
        Advertisement.__init__(self, bus, index, 'peripheral')
        self.add_service_uuid(uuid)
        self.add_local_name(LOCAL_NAME)
        self.add_service_name(service_name)
        self.include_tx_power = False

def find_adapter(bus):
    remote_om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'),
                               DBUS_OM_IFACE)
    objects = remote_om.GetManagedObjects()
    for o, props in objects.items():
        if LE_ADVERTISING_MANAGER_IFACE in props and GATT_MANAGER_IFACE in props:
            return o
        print('Skip adapter:', o)
    return None

def main():
    global mainloop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    bus = dbus.SystemBus()
    adapter = find_adapter(bus)
    if not adapter:
        print('BLE adapter not found')
        return

    service_manager = dbus.Interface(
                                bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                GATT_MANAGER_IFACE)
    ad_manager = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, adapter),
                                LE_ADVERTISING_MANAGER_IFACE)

    app = Application(bus)
    adv_Error = UartAdvertisement(bus, 0, UART_ERROR_SERVICE_UUID, "ERROR")
    adv_Battery = UartAdvertisement(bus, 1, UART_BATTERY_SERVICE_UUID, "BATTERY")
    adv_Motor = UartAdvertisement(bus, 2, UART_MOTOR_SERVICE_UUID, "MOTOR")

    mainloop = GLib.MainLoop()

    service_manager.RegisterApplication(app.get_path(), {},
                                        reply_handler=register_app_cb,
                                        error_handler=register_app_error_cb)
    
    ad_manager.RegisterAdvertisement(adv_Error.get_path(), {},
                                    reply_handler=lambda: register_ad_cb("'ERROR'"),
                                     error_handler=register_ad_error_cb)
    ad_manager.RegisterAdvertisement(adv_Battery.get_path(), {},
                                    reply_handler=lambda: register_ad_cb("'BATTERY'"),
                                     error_handler=register_ad_error_cb)
    ad_manager.RegisterAdvertisement(adv_Motor.get_path(), {},
                                    reply_handler=lambda: register_ad_cb("'MOTOR'"),
                                     error_handler=register_ad_error_cb)
    
    try:
        mainloop.run()
    except KeyboardInterrupt:
        adv_Battery.Release()
        adv_Motor.Release()

if __name__ == '__main__':
    main()