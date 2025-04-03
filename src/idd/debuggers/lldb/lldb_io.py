from threading import Lock
from idd.diff_driver import DiffDriver


lock = Lock()


class ParallelFlag:  # used as a flag to sync between two instances
    def __init__(self, is_parallel=True):
        self._is_parallel = is_parallel
        self.count = 0

    @property
    def is_parallel(self):
        return self._is_parallel

    @is_parallel.setter
    def is_parallel(self, value):
        self.count += 1
        self._is_parallel = value


class IOManager:
    class SyncFile:
        def __init__(self, io_manager: "IOManager"):
            self.contents = []
            self.io_manager = io_manager

        def write(self, text: str):
            self.contents.append([text])
            self.io_write()

        def append(self, contents: list[str]):
            self.contents.append(contents)
            self.io_write()

        def io_write(self):
            # determine if we need to write to widget
            if self.io_manager.is_parallel and len(
                self.io_manager.base_contents.contents
            ) == len(self.io_manager.regression_contents.contents):
                self.io_manager._write()

            if not self.io_manager.is_parallel:
                if self is self.io_manager.base_contents:
                    self.io_manager.base_io_widget.append(self.contents)
                else:
                    self.io_manager.regression_io_widget.append(self.contents)
                self.contents.clear()

    def __init__(
        self, base_io_widget, regression_io_widget, is_parallel_wrapper: ParallelFlag
    ):
        self.base_io_widget = base_io_widget
        self.regression_io_widget = regression_io_widget
        self.base_contents = IOManager.SyncFile(self)
        self.regression_contents = IOManager.SyncFile(self)
        self.is_parallel = is_parallel_wrapper
        self.diff_driver = DiffDriver()

    def get_base_file(self):
        return self.base_contents

    def get_regression_file(self):
        return self.regression_contents

    def _write(self):
        with lock:
            for base, regressed in zip(
                self.base_contents.contents, self.regression_contents.contents
            ):
                diff1 = self.diff_driver.get_diff(base, regressed, "base")
                self.base_io_widget.append(diff1)

                diff2 = self.diff_driver.get_diff(regressed, base, "regressed")
                self.regression_io_widget.append(diff2)

            self.base_contents.contents.clear()
            self.regression_contents.contents.clear()
