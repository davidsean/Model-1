import common
import monitor
import unittest
import time

class TestInterface(unittest.TestCase):
    iface = monitor.Interface()

    def test_serial_number(self):
        # print("Hardware serial number: {}".format(iface.get_serial_number()))
        # this is only valid for the demo unit
        self.assertEqual(self.iface.get_serial_number(), "f8aa31fe")

    def Test_get_mac_address(self):
        # print("Hardware address (ethernet): {}".format(iface.get_mac_address()))
        self.assertEqual(self.iface.get_mac_address(), "b8:27:eb:ff:64:ab")

    def test_internet_connection(self):
        # print("Can contact the mothership: {}".format(iface.connects_to_internet()))
        self.assertTrue(self.iface.connects_to_internet())
        # print("Can contact the mothership: {}".format(iface.connects_to_internet(host = '35.183.143.177', port = 80)))
        self.assertTrue(self.iface.connects_to_internet(host='35.183.143.177', port=80))

    def serial_connection(self):
        # print("Has serial connection with Arduino: {}".format(iface.serial_connection.is_open()))
        self.unittest.assertTrue(self.iface.serial_connection.is_open())



#class TestArduino(unittest.TestCase):
        #arduino_handler = monitor.ArduinoDirectiveHandler()
#        mon = monitor.Sensors()
#        mon.verbosity=1
#        tags=['TP','TC','TD','TA','TS','TM','FM','CP','CC','CS','CA','CM','OP','OC','OS','OM','OA']
#        tags.append('time')
#        tags.append('ID')
#        tags.append('IV')
#        timeout = 0
#        while len(mon.sensorframe)!=0 and timeout<30:
            # leave some time to get a valid sensorframe
#            time.sleep(1)
#            timeout+=1
#            print(timeout, mon.sensorframe)

 
#        def test_message_rcv(self):
#            self.assertFalse(len(mon.sensorframe)==0)

#        def test_message_len(self):
#            print(len(self.tags))
#            print(self.mon.sensorframe)
#            self.assertTrue(len(self.mon.sensorframe)==len(self.tags))

#        def test_tags(self):
#            for tag in self.tags:
#                self.assertTrue(tag in self.mon.sensorframe)


class TestArduinoControl(unittest.TestCase):
    sensor_handler = monitor.Sensors()
    sensor_handler.verbosity = 0
    
    print("Notice: stalling tests for 30 seconds to allow the Arduino<->Pi link to get estblished.")
    time.sleep(30)
    
    def test_temperature_setpoint(self):
        self.sensor_handler.arduino_handler.enqueue_parameter_update("TP", 2500)
        time.sleep(10)
        self.assertTrue(self.sensor_handler.sensorframe["TP"] == 2500)
        
    def test_temperature_invalid_low_setpoint(self):
        self.sensor_handler.arduino_handler.enqueue_parameter_update("TP", 100)
        time.sleep(10)
        self.assertFalse(self.sensor_handler.sensorframe["TP"] == 100)
    
    def test_temperature_invalid_high_setpoint(self):
        self.sensor_handler.arduino_handler.enqueue_parameter_update("TP", 8500)
        time.sleep(10)
        self.assertFalse(self.sensor_handler.sensorframe["TP"] == 8500)
        

if __name__ == '__main__':
    unittest.main()
