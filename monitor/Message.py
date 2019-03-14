import base64
import binascii
import json
import uuid
import serial
import socket
import struct
import sys
import threading
import time
import fcntl
import commands
import random

"""
.. module:: Message
    :platform: Raspbian
    :synopsis: Incubator module for serial communication between RPi and Arduino

"""


class ArduinoDirectiveHandler():
    """ Class that handles sending commands to the arduino and verifying
    that the csommands have been accepted and acted uopn by the control
    board.
    """

    def __init__(self):
        ''' Initialization

        Args:
          None
        '''
        self.queue_dictionary = {}
        
        self.queue_lock = threading.Lock()

    def enqueue_parameter_update(self, param, value):
        """ Adds a parameter to the update queue, the updates will be sent
        at a later time.  If this update follows another requested update,
        overwrite it.  The item will remain in the queue until the action
        has been verified

        Args:
            param (str): the identifier of the parameter to update
            value (int): the value of the parameter to update
        """
        with self.queue_lock:
            if param in self.queue_dictionary:
                print("The " + param +
                      " parameter was already in the dictionary, updating.")
            self.queue_dictionary[param] = value

    def get_arduino_command_string(self):
        """ Returns a complete string to send to the arduino in order to
        update the running parameters.  Commands can be no longer than 50
        characters and won't involve removing the command from the queue,
        a separate system will verify that the change has been made.

        Args:
          None
        """
        arduino_command_string = ""
        with self.queue_lock:
            for param in self.queue_dictionary:
                if (len(arduino_command_string) + len(param) + len(str(self.queue_dictionary[param])) + 2) <= 50:
                    if len(arduino_command_string) > 0:
                        arduino_command_string = arduino_command_string + "&"
                    arduino_command_string = arduino_command_string + \
                        param + "|" + str(self.queue_dictionary[param])
        commandLen = len(arduino_command_string)
        arduino_command_string = arduino_command_string + "\r"
        calcCRC = binascii.crc32(arduino_command_string.encode()) & 0xFFFFFFFF
        
        arduino_command_string = str(commandLen) + "~" + format(calcCRC,
                                                                'x') + "$" + arduino_command_string + "\n"

        return arduino_command_string

    def verify_arduino_status(self, last_sensor_frame):
        """ Will check all commands in the queuedictionary and pop off any
        for which the state coming from the arduino matches the desired level

        Args:
          last_sensor_frame (dict): the last sensorframe received from the Arduino
        """
        
        with self.queue_lock:
            queue_copy = self.queue_dictionary.copy()
            for param in queue_copy:
                if (param == 'ID' or param == 'IP4' or param == 'MRW' or param == 'MRF'):
                    print("The queue dictionary contained a " + param + " parameter during a standard check, it was deleted.")
                    self.queue_dictionary.pop(param)
                else:
                    if (self.queue_dictionary[param] == int(last_sensor_frame[param])):
                        print("Removing the " + param + " parameter from the queue")
                        self.queue_dictionary.pop(param)
                    else:
                        print("Unable to remove " + param + " from the queue due to mismatch (" + str(self.queue_dictionary[param]) + "|" + str(int(last_sensor_frame[param])) + ")")

    def clear_queue(self):
        """
        Command to erase everything in the queue.

        Args:
            None
        """
        with self.queue_lock:
            self.queue_dictionary.clear()

    def get_arduino_mac_update_command_string(self, param="MWR", mac_addr="00:00:00:00:00:00"):
        """ Should only be called shortly after a boot

        Args:
          param (str): three-letter code for the start of the parameter (MWR for Ethernet, MWF for Wifi)
          mac_addr (str): colon-separated string of the current system's MAC address
        """
        self.clear_queue()
        self.enqueue_parameter_update(param, "".join(mac_addr.split(":")))
        cmd_string = self.get_arduino_command_string()
        self.clear_queue()
        return cmd_string

    def get_arduino_ip_update_command_string(self, ip_addr):
        """ Should only be called after a boot or when noticing an IP
        change

        Args:
          ip_addr (str): string containing the IP address of the item
        """
        self.clear_queue()
        self.enqueue_parameter_update("IP4", ip_addr)
        cmd_string = self.get_arduino_command_string()
        self.clear_queue()
        return cmd_string

    def get_arduino_serial_update_command_string(self, serial):
        """ Should only be called after a boot

        Args:
          serial (str): string containing the serial of the rPi
        """
        self.clear_queue()
        self.enqueue_parameter_update("ID", serial)
        cmd_string = self.get_arduino_command_string()
        self.clear_queue()
        return cmd_string


class Interface():
    """ Class that holds everything important concerning communication.

    Mainly stuff about the serial connection, but also
    identification and internet connectivity. Objects indended
    to be displayed on the Incubator LCD should be found in this class.

    Attributes:
        serial_connection (:obj:`Serial`): serial connection from GPIO
    """

    def __init__(self):
        ''' Initialization
        Args:

          None
        '''
        self.serial_connection = serial.Serial(port='/dev/serial0', baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, xonxoff=False, rtscts=False, dsrdtr=False)

    def connects_to_internet(self, host="8.8.8.8", port=53, timeout=3):
        """ Tests internet connectivity
        Test intenet connectivity by checking with Google
        Host: 8.8.8.8 (google-public-dns-a.google.com)
        OpenPort: 53/tcp
        Service: domain (DNS/TCP)

        Args:
          host (str): the host to test connection
          port (int): the port to use
          timeout (timeout): the timeout value (in seconds)
        """
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except Exception as err:
            print(err.message)
            return False

    def get_serial_number(self):
        """ Get uniqeu serial number
        Get a unique serial number from the cpu, shortened
        for easy readability.

        Args:
          None
        """
        serial = "0000000000"
        try:
            with open('/proc/cpuinfo', 'r') as fp:
                for line in fp:
                    if line[0:6] == 'Serial':
                        serial = line[10:26]
                        serial = serial.lstrip("0")
            if serial == "0000000000":
                raise TypeError('Could not extract serial from /proc/cpuinfo')
        except FileExistsError as err:
            serial = "0000000000"
            print(err.message)

        except TypeError as err:
            serial = "0000000000"
            print(err.message)
        return serial

    def get_iface_list(self):
        """ Get the list of interfaces
        
        Args:
          None
          
        Returns:
        """
        return "Not implemented" 
        
    def get_iface_hardware_address(self, iface):
        """ Get the hardware (MAC) address of the given interface
        
        Args:
          iface (str): interface to return the mac off.
          
        Returns:
          str: colon-delimited hardware address
        """
        try:
            mac = open('/sys/class/net/'+iface+'/address').readline()
        except:
            hex = uuid.getnode()
            mac = ':'.join(['{:02x}'.format((hex >> ele) & 0xff)
                              for ele in range(0, 8*6, 8)][::-1])

        return mac[0:17]
            
    def get_mac_address(self):
        """ Get the ethernet MAC address
        This returns in the MAC address in the canonical human-reable form

        Args:
          None
        """
        hex = uuid.getnode()
        formatted = ':'.join(['{:02x}'.format((hex >> ele) & 0xff)
                              for ele in range(0, 8*6, 8)][::-1])
        return formatted
        
    def get_ip_address(self):
        """ Get the primary IP address
        
        Args:
          None
        
        Returns:
          String: standard representation of the device's IP address
        """
        ip = commands.getoutput('hostname -I')
        ip = ip.rstrip()
        return ip
        
    def send_message_to_arduino(self, msg):
        '''
        Will transmit a string to the Arduino via the serial link.

        Args:
            msg (string): The message string to be sent to the Arduino, including checksums et all.
        '''

        try:
            self.serial_connection.write(msg.encode())
            self.serial_connection.flush()
        except BaseException as e:
            time.sleep(1)
            print('Error: ', e)



class Sensors():
    """ Class to handle sensor communication

    Attributes:
        sensorframe (dict : Dictionary holding all sensor key-value pairs
        verbosity (int) : set sthe amount of information printed to screen
        arduino_link (): Instance of the Interface() class
        lock (): Instance of threading Lock to
        monitor (): Process that continuously read incomming serial messages
    """

    def __init__(self):
        """ Initialization
        """
        # dictionary to hold incubator status
        self.sensorframe = {}

        # set verbosity=1 to view more
        self.verbosity = 1

        self.arduino_interface = Interface()
        self.arduino_handler = ArduinoDirectiveHandler()

        self.lock = threading.Lock()
        self.perform_monitoring = True
        self.interface = threading.Thread(target=self.incubator_connector_thread)
        self.interface.setDaemon(True)
        self.interface.start()

    def __str__(self):
        with self.lock:
            toReturn = self.sensorframe
        return str(toReturn)

    def json_sensorframe(self):
        """ JSON object containing arduino serial message
        Returns a JSON formated string of the current state

        Args:
            None
        """
        with self.lock:
            toReturn = {'incubator': self.sensorframe}
        return toReturn

    def incubator_connector_thread(self):
        """ This function will handle the main Arduino
        monitoring and control loop.  The loop will
        consist of verifying how the update dictionary
        compares to the most recent frame, popping any
        updates which don't need to be performed; 
        sending an update command to the Arduino; and 
        processing the next frame coming from the 
        Arduino.
        
        Args:
          None
        """
        if (self.verbosity == 1):
            print("Starting Arduino communication thread.")

        self.init_arduino_runtime()
        
        while self.perform_monitoring:
            self.arduino_handler.verify_arduino_status(self.sensorframe)
            if (self.arduino_handler.queue_dictionary):
                msg = self.arduino_handler.get_arduino_command_string()
                if (self.verbosity == 1):
                    print("Sending message to Arduino: " + msg)
                self.arduino_interface.send_message_to_arduino(msg)
            self.get_incubator_message()
            
    
    def get_incubator_message(self):
        ''' Wait for and processes a serial message 
        from the Arduino.  Escape after five failed 
        attempts or the reception of the good frame

        Args:
            None
        '''
        wait_for_new_frame = True
        attempts_remaining = 5
        
        while wait_for_new_frame:
#            if self.arduino_link.serial_connection.in_waiting:
                try:
                    line = self.arduino_interface.serial_connection.readline().rstrip()
                    if self.checksum_passed(line):
                        wait_for_new_frame = False
                        if (self.verbosity == 1):
                            print("checksum passed")
                        with self.lock:
                            self.save_message_dict(line)
                        if (self.verbosity == 1):
                            print(self.sensorframe)
                    else:
                        if (self.verbosity == 1):
                            print('Ign: ' + line.decode().rstrip())
                except BaseException as e:
                    attempts_remaining = attempts_remaining - 1
                    if attempts_remaining < 1:
                        wait_for_new_frame = False
                    time.sleep(1)
                    print('Error: ', e)
#           else:
 #               print('Waiting... ' + format(self.arduino_link.serial_connection.in_waiting))        
  #              time.sleep(4)

    def pop_param(self, msg, char):
        ''' pop

        Args:
            char (char): a special character occuring only once
            msg (str): a string containing the the special character

        Returns:
            (sub_msg[0], sub_msg[1]) : two sub strings on either side of char.
            When there is more than one occurence of char (or when it is not present),
            returns the tuple (False, msg)
        '''

        msg = msg.decode().split(char)
        if len(msg) != 2:
            if (self.verbosity == 1):
                print("Corrupt message: while splitting with special character '{}' ".format(char))
            return False, msg
        return msg[0], msg[1]

    def checksum_passed(self, msg):
        ''' Check if the checksum passed
        recompute message checksum and compares with appended hash

        Args:
            msg (str): a string containing the message, having the following
                          format: Len~CRC32$Param|Value&Param|Value

        Returns:
            `True` when `msg` passes the checksum, `False` otherwise
        '''
        # pop the Len
        msg_len, msg = self.pop_param(msg, '~')
        if msg_len == False:
            return False
        # pop the Crc
        msg_crc, msg = self.pop_param(msg, '$')
        if msg_crc == False:
            return False

        # compare CRC32
        calcCRC = binascii.crc32(msg.rstrip()) & 0xffffffff
        if format(calcCRC, 'x') == msg_crc.lstrip("0"):
            return True
        else:
            if (self.verbosity == 1):
                print(
                    "CRC32 Fail: calculated " +
                    format(calcCRC, 'x') +
                    " but received " +
                    msg_crc)
            return False

    def save_message_dict(self, msg):
        '''
        Takes the serial output from the incubator and creates a dictionary
        using the two letter ident as a key and the value as a value.

        Args:
            msg (string): The raw serial message (including the trailing checksum)

        Only use a message that passed the checksum!
        '''

        # pop the Len and CRC out
        tmp, msg = self.pop_param(msg, '$')

        if tmp == False:
            return False
        self.sensorframe = {}
        for params in msg.split('&'):
            kvp = params.split("|")
            if len(kvp) != 2:
                print("ERROR: bad key-value pair")
            else:
                self.sensorframe[kvp[0].encode("utf-8")] = kvp[1].encode("utf-8")
        self.sensorframe['Time'] = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.gmtime())
        return
        
    def init_arduino_runtime(self):
        """ 
        Initialize the arduino's first-boot run-time information
        such as serial ID, IP, MAC, etc.
        
        Args:
          none
          
        """
        
        msg0 = self.arduino_handler.get_arduino_serial_update_command_string(self.arduino_interface.get_serial_number())
        if (self.verbosity == 1):
            print("Sending message: " + msg0.rstrip())
        self.arduino_interface.send_message_to_arduino(msg0)
        time.sleep(5) # Required to prevent a buffer overflow on the arduino.

        msg1 = self.arduino_handler.get_arduino_ip_update_command_string(self.arduino_interface.get_ip_address())
        if (self.verbosity == 1):
            print("Sending message: " + msg1.rstrip())
        self.arduino_interface.send_message_to_arduino(msg1)
        time.sleep(5)  # Required to prevent a buffer overflow on the arduino.

        msg2 = self.arduino_handler.get_arduino_mac_update_command_string("MWR", self.arduino_interface.get_iface_hardware_address("eth0"))
        if (self.verbosity == 1):
            print("Sending message: " + msg2.rstrip())
        self.arduino_interface.send_message_to_arduino(msg2)
        time.sleep(5) # Required to prevent a buffer overflow on the arduino.

        msg3 = self.arduino_handler.get_arduino_mac_update_command_string("MWF", self.arduino_interface.get_iface_hardware_address("wlan0"))
        if (self.verbosity == 1):
            print("Sending message: " + msg3.rstrip())
        self.arduino_interface.send_message_to_arduino(msg3)

    
             

if __name__ == '__main__':
    print("PySerial version: " + serial.__version__)

    test_connections = False
    #test_connections = True
    if test_connections:
        iface = Interface()
        print("Hardware serial number: {}".format(iface.get_serial_number()))
        print("Network interfaces: {}".format(iface.get_iface_list()))
        print("Hardware address (ethernet): {}".format(iface.get_iface_hardware_address("eth0")))
        print("Hardware address (wifi): {}".format(iface.get_iface_hardware_address("wlan0")))
        print("Primary IP address: {}".format(iface.get_ip_address()))
        print("Can connect to the internet: {}".format(iface.connects_to_internet()))
        print("Can contact the mothership: {}".format(
            iface.connects_to_internet(host='35.183.143.177', port=80)))
        print("Has serial connection with Arduino: {}".format(iface.serial_connection.is_open))
        del iface

    test_commandset = False
    #test_commandset = True
    if test_commandset:
        arduino_handler = ArduinoDirectiveHandler()
        mon = Sensors()

        msg0 = arduino_handler.get_arduino_serial_update_command_string(mon.arduino_interface.get_serial_number())
        print("Sending message: " + msg0)
        mon.arduino_interface.send_message_to_arduino(msg0)
        time.sleep(5)

        msg1 = arduino_handler.get_arduino_ip_update_command_string(mon.arduino_interface.get_ip_address())
        print("Sending message: " + msg1)
        mon.arduino_interface.send_message_to_arduino(msg1)
        time.sleep(5)
        
        msg2 = arduino_handler.get_arduino_mac_update_command_string("MWR", mon.arduino_interface.get_iface_hardware_address("eth0"))
        print("Sending message: " + msg2)
        mon.arduino_interface.send_message_to_arduino(msg2)
        time.sleep(5)
        
        msg3 = arduino_handler.get_arduino_mac_update_command_string("MWF", mon.arduino_interface.get_iface_hardware_address("wlan0"))
        print("Sending message: " + msg3)
        mon.arduino_interface.send_message_to_arduino(msg3)

        del arduino_handler
        del mon

    monitor_serial = False
    #monitor_serial = True
    if monitor_serial:
        mon = Sensors()
        mon.verbosity = 0
        print("Has serial connection with Arduino: {}".format(
            mon.arduino_link.serial_connection.is_open))
        print("Displaying serial data")
        while True:
            time.sleep(5)
            # print("trying...")
            print(mon.sensorframe)
            # print(mon.arduino_link.serial_connection.readline())
        del mon
        
        
    standard_run = True
    if standard_run:
        print("Spawning sensor handling thread.")
        sensor_handler = Sensors()
        sensor_handler.verbosity = 1
        
        print("Main thread is sleeping for 60 seconds to allow the Arduino to get its runtime configuration")
        time.sleep(60)
        
        while True:
            op = random.randint(1,4)
            if (op == 1):
                val = random.randint(2000,4000)
                print("Attempting to set Temperature to " + str(val))
                sensor_handler.arduino_handler.enqueue_parameter_update("TP", val)
            elif (op == 2):
                val = random.randint(200,800)
                print("Attempting to set CO2 to " + str(val))
                sensor_handler.arduino_handler.enqueue_parameter_update("CP", val)
            elif (op == 3):
                val = random.randint(100,2000)
                print("Attempting to set O2 to " + str(val))
                sensor_handler.arduino_handler.enqueue_parameter_update("OP", val)
                
            print("Main thread is sleeping. zZzZ")
            time.sleep(30)
            
            
        del sensor_handler
