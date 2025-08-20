"""
Executor module providing progress-aware thread pool execution capabilities.

This module implements a thread pool executor with built-in progress tracking
functionality. It includes progress controllers, future wrappers, and utility
functions for managing asynchronous tasks with progress reporting.
"""

from concurrent.futures import Future, ThreadPoolExecutor, CancelledError
from .util import _tt


ProgressListener = _tt.Callable[[int, int, "ProgressController"], None]


class ProgressController:
    """
    A controller for tracking and reporting progress of operations.

    This class manages progress state and notifies listeners when progress changes.
    It maintains a current progress value and total, and can synchronize with other
    progress controllers.

    Attributes:
        __progress (int): Current progress value.
        __total (int): Total value for the operation.
        _listener (List[ProgressListener]): List of registered progress listeners.
    """

    _progress: int = 0
    _total: int = 100

    _listener: _tt.List[ProgressListener]

    def __init__(self):
        """
        Initialize a new ProgressController.

        Sets initial progress to 0, total to 100, and creates an empty listener list.
        """
        self._listener = []

    def updateProgress(
        self,
        progress: _tt.Optional[int] = None,
        add: _tt.Optional[int] = None,
        total: _tt.Optional[int] = None,
    ):
        """
        Update the progress value and optionally the total.

        Notifies all registered listeners after updating the values.

        Args:
            progress (int): The new progress value.
            total (Optional[int]): The new total value. If None, keeps current total.
        """
        if add is not None:
            progress = self._progress + add
        if progress is not None:
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
            self.updateProgress(progress, total)

        return target.addProgressListener(_sync)


class FutureWithProgress(Future, ProgressController):
    """
    A Future that can report progress.

    Combines the functionality of a Future with progress tracking capabilities.
    This allows asynchronous operations to report their progress while maintaining
    the standard Future interface.
    """

    def __init__(self):
        super().__init__()
        ProgressController.__init__(self)


_T = _tt.TypeVar("_T")
_P = _tt.TypeVar("_P", bound=Future)


def futureMap(target: Future[_T], creater: _tt.Callable[[], _P] = Future[_T]):
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
    res = creater()

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

    def submit(self, fn, /, *args, **kwargs):
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
