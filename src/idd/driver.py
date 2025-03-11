import abc
from abc import abstractmethod

class Driver(metaclass=abc.ABCMeta):
    @abstractmethod
    def get_state(self, target): raise NotImplementedError

    @abstractmethod
    def run_single_command(self, command, target): raise NotImplementedError

    @abstractmethod
    def run_parallel_command(self, command): raise NotImplementedError
    
    @abstractmethod
    def terminate(self): raise NotImplementedError


class IDDParallelTerminate:
    pass
