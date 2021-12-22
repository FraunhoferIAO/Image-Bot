import time
import serial

SERIAL_COM_START_SIGN = "<"
SERIAL_COM_WAIT_TIME = 1.0/100
SERIAL_COM_READY_STATEMENT = "ready"
SERIAL_COM_SETUP_COMPLETE_STATEMENT = "setup complete"
SERIAL_COM_END_SIGN = ">"

class SerialIrqCom(object):
	'''
	A cass which helps to send objects to an Arduino with the SerialCom interface
	'''
	
	def __init__(self, com_interface, baudrate=9600, timeout_time=10.0):
		'''
		Initializes the Serial Com Sender and open the com port directly
		@param com_interface: The name of the com interface to open (e.g. Com4 under windows or /dev/ttyS... under Linux
		@param baudrate: The baudrate with which to open the SerialIrqCom, default ist 9600 (same as default of the Arduino implmentation
		@param timeout_time: The timeout time in seconds  after which communication with the Arduino is aborted if no answer is received
		'''
		self.__timeout_time = timeout_time
		self.__interface = serial.Serial(com_interface, baudrate)
		# Now wait for the counterpart to complete its setup
		self.__wait_for(SERIAL_COM_SETUP_COMPLETE_STATEMENT)
	
	@property
	def timeout_time(self):
		return self.__timeout_time
		
	@timeout_time.setter
	def timeout_time(self, timeout_time):
		self.__timeout_time = timeout_time
		
	def close(self):
		'''
		Closes the serial connections
		'''
		self.__interface.close()
		
	def open(self):
		'''
		Opens the serial connection again after it has been closed. No necessity to be called after initialization of this object, because the port is directly open, after the call of the constructor
		'''
		self.__interface.open()
		# Now wait for the counterpart to complete its setup
		self.__wait_for(SERIAL_COM_SETUP_COMPLETE_STATEMENT)

	def __wait_for(self, statement):
		'''
		Internal function which waits for a certain answer (statement) of the arduino. All other answers received in between will be ignored. Function can time out after self.__timeout_time seconds.
		@param statement: A statement string which mus be contained in the answer of the Arduino.
		@return: True if the statemen has been found in answer, otherwise false
		'''
		start_time = time.time()
		while ((time.time() - start_time) < self.__timeout_time):
			# Wait a little bit to not use too much CPU power
			time.sleep(SERIAL_COM_WAIT_TIME)
			response = "Wait"
			# Check if we received a response
			if self.__interface.inWaiting():
				response = str(self.__interface.readline())
			# Check if the response contains the statement                    
			if statement in str(response):
				return True
		return False

	def send_message(self, msg):
		'''
		Sends a msg to the Arduino
		@param msg: A python string representing the message to be sent
		'''
		# Write the start sign
		self.__interface.write(str.encode(SERIAL_COM_START_SIGN))
		# Wait for the reply
		if self.__wait_for(SERIAL_COM_READY_STATEMENT):
			# Received the ready signal, send the msg
			self.__interface.write(str.encode(msg))
			# Write the stop sign
			self.__interface.write(str.encode(SERIAL_COM_END_SIGN))
		else:
			print("Command send_message for message \"%s\" timed out after %f seconds" % (msg, self.__timeout_time))
		
	def send_receive_message(self, msg, number_of_lines=1, encoding="utf-8"):
		# First send a message
		self.send_message(msg)
		# Now wait for a reply
		return self.receive_message(number_of_lines, encoding)
		
	def receive_message(self, number_of_lines=1, encoding="utf-8"):
		'''
		Receives one or multiple messages from the Arduino. This function can timeout and return less than the required number of lines, if the connection times out before the next message could be received
		@param number_of_lines: The number of messages (i.e. lines) to be received
		@param encoding: The encoding to be used for the binary array received
		@return: An array of messages (i.e. lines) received from the Arduino.
		'''
		result = []
		start_time = time.time()
		while ((time.time() - start_time) < self.__timeout_time):
			# Wait a little bit to not use too much CPU power
			time.sleep(SERIAL_COM_WAIT_TIME)
			# Check if we received a response
			if self.__interface.inWaiting():
				# Add the new message
				result.append(self.__interface.readline().decode(encoding).rstrip())
				# Reset the timeout
				start_time = time.time()
			if len(result) == number_of_lines:
				return result
		return result
		

