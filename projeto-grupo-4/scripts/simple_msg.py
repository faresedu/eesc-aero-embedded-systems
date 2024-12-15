import struct

class LabelString:
    def __init__(self, label='', string_msg=''):
        self.__label = label
        self.__string = string_msg
        self.__pattern = f'20s80s'

    def pack_msg(self):
        self.__label = self.__label.encode('utf-8')
        self.__label = self.__label.ljust(20, b"\x00")

        self.__string = self.__string.encode('utf-8')
        self.__string = self.__string.ljust(80, b"\x00")

        return struct.pack(self.__pattern, self.__label, self.__string)
    
    def unpack_msg(self, data):
        self.__label, self.__string = struct.unpack(self.__pattern, data)
        self.__label = self.__label.decode('utf-8').strip('\x00')
        self.__string = self.__string.decode('utf-8').strip('\x00')

        return self.__label, self.__string

class ControlMsg:
    def __init__(self, command='', arg1 ='', arg2=''):
        self.__command = command
        self.__arg1 = arg1
        self.__arg2 = arg2
        self.__pattern = '20s20s20s'
    
    def setup_msg(self):
        self.__command = self.__command.encode('utf-8')
        self.__command = self.__command.ljust(20, b"\x00")

        self.__arg1 = self.__arg1.encode('utf-8')
        self.__arg1 = self.__arg1.ljust(20, b"\x00")

        self.__arg2 = self.__arg2.encode('utf-8')
        self.__arg2 = self.__arg2.ljust(20, b"\x00")

    def pack_msg(self):
        self.setup_msg()
        return struct.pack(self.__pattern, 
                           self.__command, 
                           self.__arg1, 
                           self.__arg2)

    def unpack_msg(self, data):
        self.__command, self.__arg1, self.__arg2 = struct.unpack(self.__pattern, data)
        self.__command = self.__command.decode('utf-8').strip('\x00')
        self.__arg1 = self.__arg1.decode('utf-8').strip('\x00')
        self.__arg2 = self.__arg2.decode('utf-8').strip('\x00')

        return self.__command, self.__arg1, self.__arg2

    def __str__(self):
        return f'Control: {self.control}, String: {self.string}'

    def __repr__(self):
        return str(self)