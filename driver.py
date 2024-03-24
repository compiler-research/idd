import abc
from abc import ABCMeta, abstractmethod

class Driver(metaclass=abc.ABCMeta):
    @abstractmethod
    def run_single_command(self, command, target): raise NotImplementedError

    @abstractmethod
    def run_parallel_command(self, command): raise NotImplementedError
