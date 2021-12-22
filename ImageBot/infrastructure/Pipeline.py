"""Pipeline class implementing Pipes and Filters pattern.

A generic pipeline to process messages efficiently in a pipes-and-filter manner (multiprocessing possible).

Inspired, but not copied from 
https://deparkes.co.uk/2019/12/08/simple-python-pipes-and-filters/

Authors:
    - Lukas Block
    - Adrian Raiser

Todo:
    - Add license boilerplate
"""

import multiprocessing
from functools import partial
import traceback
from collections.abc import Iterable
from typing import Callable

from numpy import sin

class Pipeline(object):
    """Class representing Pipeline.

    Class which represents a pipeline within the pipes and filters pattern. 
    Every pipeline consists of filters added in series to each other.
    """


    def __init__(self, with_multiprocessing=False, max_no_processes=8):
        """Constructor.

        Args:
            with_multiprocessing (bool, optional): Enable multiprocessing. Defaults to False.
            max_no_processes (int, optional): If enabled, create the passed amount of subprocesses. Defaults to 8.
        """
        self._multiprocessing = with_multiprocessing
        if with_multiprocessing:
            self._pool = multiprocessing.Pool(max_no_processes)

        self._filters = []
        
    def add(self, filter : Callable, batch_processing=False):
        """Add filter to pipeline.

        Args:
            filter (Callable): A Callable object, taking a  message object or an Iterable of message objects as first input. Message objects are any python serializable objects which are passed between filters in the pipeline.
            batch_processing (bool, optional): Enable batch processing. The filter must support batch processing by taking an Iterable of message objects as argument. Defaults to False.
        """
        assert callable(filter)
        self._filters.append((filter, batch_processing))

    def insert(self, index, filter, batch_processing=False):
        """Insert filter at provided index to the pipeline.

        Args:
            index (Int): Index to insert filter on
            filter (Callable): Filter to be added
            batch_processing (bool, optional): Enable batch processing. The filter must support it. Defaults to False.
        """
        assert callable(filter)
        self._filters.insert(index, (filter, batch_processing))
        
    def execute(self, message, clbck=None, batch_processing=False):
        """Execute pipeline on passed message or list of messages.
        
        This function spans a new pipeline process and then returns as soon as the
        process was created (i.e. the pipeline is not finished!). The callback is
        called when the process finishes.
        If the number of max processes for this pipeline is reached, the process is
        put aside and will be started as soon as one of the currently running processes
        finished.

        Args:
            message (object|List[object]): Message object or list to be piped
            clbck (Callable|None, optional): The callback to be called, when the processing of the message
                finished. Be careful, the callback will be called from another process
                because pipelines are run in parallel. Thus, it might be necessary to use
                a multiprocessing.Queue in the clbck to get the result back into the main
                process. Furthermore the callback should not block for a time too long,
                because this stops further pipelines from being started. Defaults to None.
            batch_processing (bool, optional): Enable batch processing. Defaults to False.

        Returns:
            None
        """
        # Check the clbck type
        if clbck is not None:
            assert callable(clbck)
            
        # If the batch processing is true, the message must be iterable
        if batch_processing:
            assert isinstance(message, Iterable)
        
        if self._multiprocessing:
            # We are doing multiprocessing
            # First prepare the call function
            fnc = partial(Pipeline.call_fnc, filters=self._filters, message=message, batch_processing=batch_processing)
            # Hand it over
            if clbck is None:
                return self._pool.apply_async(Pipeline.call_fnc, (message, self._filters, batch_processing), error_callback=Pipeline.error_callback)
            else:
                return self._pool.apply_async(Pipeline.call_fnc, (message, self._filters ,batch_processing), callback=clbck, error_callback=Pipeline.error_callback)
        else:
            # We are not doing multiprocessing, call the function directly
            try:
                result = self(message, batch_processing=batch_processing)
            except Exception as ex:
                Pipeline.error_callback(ex)

            if clbck is not None:
                clbck(result)

    def __call__(self, message, batch_processing=False):
        """Overloads the call operator. See execute for more information.

        Args:
            message (object|List[object]): See execute
            batch_processing (bool, optional): See execute. Defaults to False.

        Returns:
            ImageMessage|List[ImageMessage]: See execute.
        """
        return Pipeline.call_fnc(message, self._filters, batch_processing=batch_processing)
        
    def join(self):
        """Joins all started subprocesses for the pipeline.
        
        Returns:
            None: Returns as soon as all subprocesses of the pipelined finished.
        """
        if self._multiprocessing:
            self._pool.close()
            self._pool.join()
    
    def error_callback(e):
        """Prints error and exceptions which might occure within the pipeline.
        
        Args:
            e (object): The error or exception which occured in the pipeline 

        Returns:
            None       
        """
        print("An exception occurred in the pipeline:")
        traceback.print_exception(type(e), e, e.__traceback__)
        
    def call_fnc(message, filters, batch_processing=False):
        """Handles the calling of provided filters.

        A filter is a function, which takes a certain message, processes it and
        return one or more other messages out of it. If the filter should return
        As such, the Pipeline itself
        is a filter, too.

        Args:
            message (object): See execute
            filters (List[Callable]): List of filters, which will be executed in order
            batch_processing (bool, optional): See execute. Defaults to False.

        Returns:
            object|List[object]: See execute
        """
        # Setup the start message(s)
        prev_results = None
        if batch_processing:
            prev_results = message
        else:
            prev_results = [message]
   
        # Now start processing
        for fb in filters:
            # The callable is stored as the first value in the tuple
            f = fb[0]
            new_results = []
            # Run each filter for each message from the previous filter
            if not fb[1]:
                # The filter is not capable of batch processing all previous results
                # at once
                for pr in prev_results:
                    single_new_result = f(pr)
                    # Collect the single or multiple results of this filter
                    if isinstance(single_new_result, list):
                        new_results.extend(single_new_result)
                    elif single_new_result is None:
                        # Do nothing, because we have an empty result
                        pass
                    else:
                        new_results.append(single_new_result)
            else:
                # The filter can do batch processing
                new_results = f(prev_results)
            # After processing all messages from the previous filter, the collected
            # results are now the results from the previous filter
            prev_results = new_results
        
        # Done with all filters, return
        return prev_results
        
        
        
        