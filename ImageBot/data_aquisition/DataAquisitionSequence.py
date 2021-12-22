"""Data aquisition sequence class definition.

The data aquisition sequence uses the robotic arm 
to take images of the desired object from different angles.

Every sequence is split into runs.
In a run, the robotic arm travels to predefined positions and takes an image. 
After each run, the images are saved into the output folder.

Todo:
    - Add license boilerplate
    - Add linux support
    - Apply module pattern (?)
    - Add type hinting
    - Fix private method indication
"""

import time
import numpy as np
import threading
import cv2
import os

from collections.abc import Iterable
from ImageBot.data_aquisition.arduinoserialirqcom.SerialIrqCom import SerialIrqCom
from ImageBot.data_aquisition import Braccio
from math import degrees, radians, asin, sin, atan2
from ImageBot.Config import CAMERA_FRAME_WIDTH, CAMERA_FRAME_HEIGHT
from datetime import datetime

class DataAquistionSequence(object):
    """Data aquisition sequence class.
    
    This class is responsible for connecting to the Arduino controlling the robotic arm, coordinating its movements and processing the images.
    """

    def __init__(self, name):
        """Constructor.

        Args:
            name (str): Instance name. Will be used to create sequence folder
        """
        # The name of this sequence
        assert isinstance(name, str)
        self.__name = name
        
        # The timestamp when this sequence was created
        self.__timestamp = datetime.now()
        
        # The number of runs
        self.__run_number = 0
        
        # The variable indicating, whether we are currently running a data aquisition
        self.__run = False
        self.__thread = None
        
        # The variables for the setup
        self.__camera = None
        self.__scs = None
        
    def init(self, serial_port, camera_id):
        """Initialize robotic arm and camera.

        Args:
            serial_port (str): Serial port the Arduino is connected to.
            camera_id (int): ID of the connected camera/webcam.

        Raises:
            Exception: Destination folder already exists.

        Todo:
            - Choose more precise exception
        """
        # Make the directory for this data aquistion
        if os.path.isdir(self.name):
            # A directory with this name already exists
            print("Warning: A folder with the name of this DataAquisitionSequence already exists in " + os.path.abspath(self.name))
        else:
            os.makedirs(self.name)
        
        # Open the connection to the braccio robot arm
        self.__scs = SerialIrqCom(serial_port)
        
        # Get the camera
        # TODO: Only a windows alternative currently
        if os.name == 'nt':
            self.__camera = cv2.VideoCapture(camera_id, cv2.CAP_DSHOW)
        else:
            self.__camera = cv2.VideoCapture(camera_id)
        self.__camera.set(cv2.CAP_PROP_SETTINGS, 1)
        self.__camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_FRAME_WIDTH)
        self.__camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_FRAME_HEIGHT)
        print("Camera resolution is:", self.__camera.get(cv2.CAP_PROP_FRAME_WIDTH), "x", self.__camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    def start(self, object_position, min_height, max_height, number_of_stops, callback):
        """Start data aquisition sequence in own thread.

        Starts the data aquisition sequence.
        The function takes the relative position of the object to the base of the robotic arm, 
        a minimal and maximal height and a number of stops and calculates the movement trajectory for the robotic arm.

        Args:
            object_position (Tuple[float]): Position of object to scan in [x, y, z] coordinates. 
            min_height (float): Minimal height to take image from.
            max_height (float): Maximal height to take image from.
            number_of_stops (int): Number of intermediate holding positions to take image from. 
            callback (function): Function to execute when sequence is finished.

        Returns:
            bool: Returns true if successfully started sequence, false if the sequence is already running or fails.

        Todo:
            - Thread or process?
        """
        if self.__run:
            return False
        
        # Set the variable
        self.__run = True
        self.__thread = threading.Thread(target=DataAquistionSequence.__run_data_aquisition, args=(self, object_position, min_height, max_height, number_of_stops, callback))
        self.__thread.start()
        
        return True
    
    def stop(self):
        """Stop data aquisition sequence."""
        # If we are not running, stopping is not necessary
        if not self.__run:
            return
        
        # If we are running, stop it
        self.__run = False
        self.__thread.join()
        # TODO: Somehow get the results?
        self.__thread = None
    
    def aquire(self, object_position, min_height, max_height, number_of_stops, callback):
        """Run data aquisition sequence.

        Starts the data aquisition sequence.
        The function takes the relative position of the object to the base of the robotic arm, 
        a minimal and maximal height and a number of stops and calculates the movement trajectory for the robotic arm.

        Args:
            object_position (Tuple[float]): Position of object to scan in [x, y, z] coordinates. 
            min_height (float): Minimal height to take image from.
            max_height (float): Maximal height to take image from.
            number_of_stops (int): Number of intermediate holding positions to take image from. 
            callback (function): Function to execute when sequence is finished.

        Returns:
            bool: Returns true if successfully started sequence, false if the sequence is already running or fails.
        """
        if self.__run:
            return False
        
        # Set the variable
        self.__run = True
        return self.__run_data_aquisition(object_position, min_height, max_height, number_of_stops, callback)
            
    def close(self):
        """Close connections and clean up."""
        # Check if init was called before
        assert self.__scs is not None
        assert self.__camera is not None
        
        # Stop the braccio and move to the safe position
        self.__scs.send_receive_message(Braccio.STOP_COMMAND, 1)
        # Close the connection to the serial port
        self.__scs.close()
        # Release the camera
        self.__camera.release()
        
        # Set them none
        self.__scs = None
        self.__camera = None

    @property
    def name(self):
        """str: Name of object class."""
        return self.__name
    
    @property
    def timestamp(self):
        """datetime: Timestemp of object creation."""
        return self.__timestamp
        
    def is_running(self):
        """Status of aquisition sequence.

        Returns:
            bool: True if sequence is running, false otherwise.
        """
        return self.__run

    def __run_data_aquisition(self, object_position, min_height, max_height, number_of_stops, callback):
        """Data aquisition method.

        Args:
            object_position (Tuple[float]): Position of object to scan in [x, y, z] coordinates. 
            min_height (float): Minimal height to take image from.
            max_height (float): Maximal height to take image from.
            number_of_stops (int): Number of intermediate holding positions to take image from. 
            callback (function): Function to execute when sequence is finished.

        Raises:
            Exception: [description]
            Exception: [description]

        Todo:
            - Specify raised exceptions.
        """
        # Check if init has been called before
        assert self.__scs is not None
        assert self.__camera is not None
        
        # Object position must be an Iterable with length 3
        assert isinstance(object_position, Iterable)
        assert len(object_position) == 3
        object_position = np.array([x for x in object_position])
        
        # Get the run number and increase it by one
        run_number = self.__run_number
        self.__run_number += 1
        
        # Print
        print("Data Aquisition for run %i is running!" % run_number)
        
        # Calculate the heights from which to make take a picture 
        heights = np.linspace(min_height, max_height, number_of_stops)
        
        for height in heights:
            # Always check, whether we should stop the aquistion, due to some
            # external trigger
            if not self.__run:
                break
            
            print("Aquiring picture from %i mm" % height)
            
            '''
            First we move to the correct position
            '''
            
            # Calculate the angles to reach the associated height
            braccio_angles = self.__calculate_servo_values(height)
                        # Calculate the x position of the arm with the associated angles
            braccio_x_pos = self.__calculate_x_pos(braccio_angles)
            braccio_pos = [braccio_x_pos, 0, height]
            
            # Calculate the view angle and add it to the braccios angles
            view_angle = self.__calculate_view_angle(object_position, braccio_pos)
            braccio_angles[3] += view_angle
        
            # Now build the command
            braccio_angles_str = ",".join([("%.2f" % i) for i in braccio_angles])
            move_to_cmd = Braccio.SET_COMMAND + braccio_angles_str
           
            cmd_result = bool(int(self.__scs.send_receive_message(move_to_cmd, 1)[0]))
            if not cmd_result:
                # Close connections and throw an exception
                self.close()
                raise Exception("The target position sent with command " + move_to_cmd + " cannot be processed by the Braccio!")
            
            # Sleep for a second, to remove vibrations from the robot
            time.sleep(1)
            
            '''
            Take the picture and store it
            '''
            # Dummy read here, because otherwise a frame seems to be stuck in the camera
            success, image = self.__camera.read()
            success, image = self.__camera.read()
            if (success):
                # The file name itself should also contian the sequence name to be
                # assignable in case the folders get mixed upt
                filename = 'run%i-%.0fmm.png' % (run_number, height)
                # Save the image
                cv2.imwrite(os.path.join(self.name, filename), image)
                # Call the callback after saving the file and give it the image
                # data for further processing
                callback(image)
            else:
                self.close()
                raise Exception("Taking the picture for target position " + str(height) + " failed!")
        
        # Check whether we have finished on our own, or stopped because of some
        # external trigger
        if self.__run:
            print("Data Aquisition finished!")
            # We have successfully finished our task, stop it yourself
            self.__run = False
            self.__thread = None
        else:
            print("Data Aquisition was stopped!")
    
    def __calculate_view_angle(self, object_position, braccio_position, sign=1):
        # Check the sign, denoting, from which perspective to look at this part 
        assert (sign == 1) or (sign == -1)
        # Now calculate
        return degrees(atan2(object_position[2]-braccio_position[2], object_position[0]-braccio_position[0]))
    
    def __calculate_servo_values(self, height):
        assert (Braccio.FOREARM_LENGTH-Braccio.BASE_LENGTH-sin(radians(Braccio.MIN_DEGREE_UPPERARM)) * Braccio.UPPERARM_LENGTH) <= height <= (Braccio.BASE_LENGTH + Braccio.UPPERARM_LENGTH + Braccio.FOREARM_LENGTH)
        
        # The resulting angles
        result = [0 for _ in range(Braccio.SERVOS_TO_SET)]
        
        # First calculate the angle for the forearm
        if height < Braccio.BASE_LENGTH:
            result[1] = Braccio.MIN_DEGREE_UPPERARM
        elif height <= (Braccio.BASE_LENGTH + Braccio.UPPERARM_LENGTH):
            result[1] = degrees(asin((height-Braccio.BASE_LENGTH) / Braccio.UPPERARM_LENGTH))
        else:
            result[1] = 90
        
        
        if height < Braccio.BASE_LENGTH:
            upper_arm_height = sin(radians(Braccio.MIN_DEGREE_UPPERARM)) * Braccio.UPPERARM_LENGTH
            result[2] = 90 + degrees(asin((height-Braccio.BASE_LENGTH-upper_arm_height) / Braccio.FOREARM_LENGTH)) - Braccio.MIN_DEGREE_UPPERARM
        elif height <= (Braccio.BASE_LENGTH + Braccio.UPPERARM_LENGTH):
            result[2] = 90 - result[1]
        else:
            result[2] = degrees(asin((height-Braccio.BASE_LENGTH-Braccio.UPPERARM_LENGTH) / Braccio.FOREARM_LENGTH))
        
        # The angle for the hand
        result[3] = 180 - result[1] - result[2]
            
        return result
    
    def __calculate_x_pos(self, braccio_angles):
        x1 = sin(radians(90-braccio_angles[1])) * Braccio.UPPERARM_LENGTH
        x2 = sin(radians(180-braccio_angles[1]-braccio_angles[2])) * Braccio.FOREARM_LENGTH
        return x1 + x2
    
    
    