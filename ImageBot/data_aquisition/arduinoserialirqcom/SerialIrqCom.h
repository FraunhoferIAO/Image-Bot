/**
   Header that includes all functionality necessary to communicate with an Arduino running the FastLED library, because this alters interrupts in a way, that serial communication might be lost

   @author: Lukas Block
   @version: 2021-02-16
*/

#ifndef SERIALIRQCOM_H
#define SERIALIRQCOM_H

// General define stuff
#define SERIAL_COM_MAX_CHARS 64
#define SERIAL_COM_START_MARKER '<'
#define SERIAL_COM_END_MARKER '>'
#define SERIAL_COM_BAUDRATE 9600
#define SERIAL_COM_READY_STATEMENT "ready"

namespace SerialIrqCom {
	
	/*
	 * Enum for return type of receive function
	 */
	enum ReturnType {
		Idle,
		Receiving,
		NewCommandAvailable
	};

	/*
	 * Variables relevant for reading
	 */
	byte pointer = 0;
	char msg[SERIAL_COM_MAX_CHARS];
	bool receiveInProgress = false;

	/**
	 Function that is responsible for setting up the serial connection
	*/
	void setup() {
	  // Setup serial connection
	  Serial.begin(SERIAL_COM_BAUDRATE);
    Serial.println("setup complete");
	}

	/**
	   Function to read the message from the serial port. Must be called in the loop()-section
	*/
	ReturnType receive() {
		// Now start reading, if something is available
		if (Serial.available() > 0) {
			// Read a char
			char readChar = Serial.read();
		
			#if DEBUG >= 2
			Serial.print("Received char: ");
			Serial.println(readChar);
			#endif
		
			if (receiveInProgress) {
				// We are in the middle of reading something

				if (readChar != SERIAL_COM_END_MARKER) {
					// Read the values
					msg[pointer] = readChar;
					pointer++;
					// Some safety net to avoid index out of bounds
					if (pointer >= SERIAL_COM_MAX_CHARS) {
						Serial.println("ERROR: Send message is longer than the maximum length of XXX!");
						pointer = SERIAL_COM_MAX_CHARS - 1;
					}
					return Receiving;
				} else {
					// End of command has been detected, terminate string
					msg[pointer] = '\0';
					// Reset reading
					receiveInProgress = false;
					pointer = 0;

					#if DEBUG >= 1
					Serial.print("Input fully arrived: ");
					Serial.println(msg);
					#endif

					return NewCommandAvailable;
				}
			} else if (readChar == SERIAL_COM_START_MARKER) {
				// We detected a start marker - start receiving
				receiveInProgress = true;
				// Let the sender know, that we are ready to receive
				// TODO: Here
				Serial.println(SERIAL_COM_READY_STATEMENT);
				return Receiving;
			} else if (isSpace(readChar)) {
				// We received a whitspace character outside the normal message statement, just do nothing
			} else {
				// We received a charcater outside any start message
				Serial.println("WARNING: Received char but without any start message statement! Cannot process message...");
			}  
		}
		// Nothing available to be read
		return Idle;
	}
	
	
	
}



#endif
