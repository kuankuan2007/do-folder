"""
Executor module providing progress-aware thread pool execution capabilities.

This module implements a thread pool executor with built-in progress tracking
functionality. It includes progress controllers, future wrappers, and utility
functions for managing asynchronous tasks with progress reporting.
"""

import time
from concurrent.futures import Future, ThreadPoolExecutor, CancelledError
from .util import _tt, TaskStatus


ProgressListener = _tt.Callable[[int, int, "ProgressController"], None]


class ProgressController:
    """
    A controller for tracking and reporting progress of operations.

    This class manages progress state and notifies listeners when progress changes.
    It maintains a current progress value and total, and can synchronize with other
    progress controllers.

    Attributes:
        _progress (int): Current progress value.
        _total (int): Total value for the operation.
        _listener (List[ProgressListener]): List of registered progress listeners.
    """

    _progress: int = 0
    _total: int = 100

    _listener: list[ProgressListener]
    _history: list[tuple[float, int]]

    historyTime: float = 3.0

    def __init__(self):
        """
        Initialize a new ProgressController.

        Sets initial progress to 0, total to 100, and creates an empty listener list.
        """
        self._listener = []
        self._history = []

    def updateProgress(
        self,
        progress: _tt.Optional[int] = None,
        *,
        total: _tt.Optional[int] = None,
        add: _tt.Optional[int] = None,
    ):
        """
        Update the progress value and optionally the total.

        Notifies all registered listeners after updating the values.

        Args:
            progress (int, optional): The new progress value.
            total (int, optional): The new total value. If None, keeps current total.
            add (int, optional): The amount to add to the current progress. If None, keeps current progress.
        """
        if add is not None:
            progress = self._progress + add
        if progress is not None:
            self._history.append((time.time(), progress - self._progress))
            self._progress = progress
        if total is not None:
            self._total = total
        for listener in self._listener:
            self._callListener(listener)

    def _callListener(self, listener: ProgressListener):
        """
        Call a progress listener with current progress information.

        Args:
            listener (ProgressListener): The listener function to call.
        """
        listener(self._progress, self._total, self)

    def addProgressListener(self, listener: ProgressListener) -> _tt.Callable[[], None]:
        """
        Add a listener that will be called with the current progress.

        The listener is immediately called with the current progress state.

        Args:
            listener (ProgressListener): Function to call when progress updates.
                                       Takes (progress, total, controller) as parameters.

        Returns:
            Callable[[], None]: Function to remove the listener when called.
        """

        self._callListener(listener)
        self._listener.append(listener)
        return lambda: self._listener.remove(listener)

    def syncFrom(self, target: "ProgressController"):
        """
        Synchronize this controller's progress with another controller.

        Sets up a listener on the target controller that will update this
        controller's progress whenever the target's progress changes.

        Args:
            target (ProgressController): The controller to synchronize from.

        Returns:
            Callable[[], None]: Function to stop the synchronization.
        """

        def _sync(progress: int, total: int, _future: "ProgressController"):
            self.updateProgress(progress, total=total)

        return target.addProgressListener(_sync)

    @property
    def progress(self) -> int:
        """Get current progress value.

        Returns:
            Current progress as integer.
        """
        return self._progress

    @property
    def total(self) -> int:
        """Get total progress target value.

        Returns:
            Total progress target as integer.
        """
        return self._total

    @property
    def speed(self):
        """Calculate current processing speed based on history.

        Returns:
            Current speed in units per second, or None if insufficient data.
        """
        now = time.time()
        while self._history and now - self._history[0][0] > self.historyTime:
            self._history.pop(0)
        if len(self._history) < 2:
            return None
        return sum(x[1] for x in self._history) / self.historyTime

    @property
    def remain(self):
        """Calculate estimated remaining time based on current speed.

        Returns:
            Estimated remaining time in seconds, or None if speed unavailable.
        """
        speed = self.speed
        if not speed:
            return None
        return (self.total - self.progress) / speed

    @property
    def percent(self) -> float:
        """Calculate completion percentage.

        Returns:
            Completion percentage as float (0.0 to 100.0).
        """
        if not self.total:
            return 0.0
        return self._progress / self._total * 100.0


_T = _tt.TypeVar("_T")


class FutureCanSync(Future[_T]):
    """Future that supports custom running state checking.

    Extends the standard Future to allow custom logic for determining
    if the future is currently running.
    """

    runningFrom: _tt.Optional[_tt.Callable[[], bool]] = None

    def __init__(self, runningFrom: _tt.Optional[_tt.Callable[[], bool]] = None):
        """Initialize FutureCanSync with optional custom running check.

        Args:
            runningFrom: Optional callable that returns True if the future is running.
        """
        super().__init__()
        self.runningFrom = runningFrom

    def running(self) -> bool:
        """Check if the future is currently running.

        Returns:
            True if the future is running, False otherwise.
        """
        if self.runningFrom:
            return self.runningFrom()
        return super().running()


class FutureWithProgress(FutureCanSync[_T], ProgressController):
    """
    A Future that can report progress.

    Combines the functionality of a Future with progress tracking capabilities.
    This allows asynchronous operations to report their progress while maintaining
    the standard Future interface.
    """

    statue: TaskStatus = TaskStatus.WAITING

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ProgressController.__init__(self)
        self.add_done_callback(self._futureStateSync)

    def _futureStateSync(self, target: Future):
        if target.done():
            self.updateProgress(progress=self._total)
            if target.cancelled():
                self.statue = TaskStatus.CANCELED
            elif target.exception():
                self.statue = TaskStatus.FAILED
            else:
                self.statue = TaskStatus.COMPLETED

    def updateProgress(self, *args, **kwargs):
        if self.running():
            self.statue = TaskStatus.RUNNING
        return super().updateProgress(*args, **kwargs)


_P = _tt.TypeVar("_P", bound=FutureCanSync)


def futureMap(target: "Future[_T]", creater: _tt.Callable[..., _P] = FutureCanSync):
    """
    Map a Future to a new Future using a creator function.

    Creates a new Future that will be resolved with the same result or exception
    as the target Future. This is useful for wrapping Futures with additional
    functionality.

    Args:
        target (Future[_T]): The source Future to map from.
        creater (Callable[[], _P]): Function that creates the new Future.
                                   Defaults to Future[_T].

    Returns:
        _P: The new Future created by the creater function.
    """
    res = creater(runningFrom=target.running)

    def _doneCallback(future: Future):
        try:
            result = future.result()
            res.set_result(result)
        except BaseException as e:  # pylint: disable=broad-except
            if isinstance(e, CancelledError):
                res.cancel()
            else:
                res.set_exception(e)

    target.add_done_callback(_doneCallback)

    return res


class ThreadPoolExecutorWithProgress(ThreadPoolExecutor):
    """
    A thread pool executor that reports progress.

    Extends the standard ThreadPoolExecutor to automatically provide progress
    tracking for submitted tasks. Each submitted task receives a ProgressController
    and returns a FutureWithProgress that can report progress updates.
    """

    def submit(self, fn, /, *args, **kwargs) -> FutureWithProgress:
        """
        Submit a callable to be executed with the given arguments.

        The callable will receive a 'progressControler' keyword argument
        that can be used to report progress during execution.

        Args:
            fn: The callable to be executed.
            *args: Positional arguments to pass to the callable.
            **kwargs: Keyword arguments to pass to the callable.

        Returns:
            FutureWithProgress: A Future that can report progress and will
                              resolve with the result of the callable.
        """
        controller = ProgressController()
        _res = super().submit(fn, *args, progress=controller, **kwargs)
        res = futureMap(_res, FutureWithProgress)
        res.syncFrom(controller)
        return res
