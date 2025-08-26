"""
Debug Timer Module - A context manager for real-time elapsed time monitoring
"""
import time
import sys
import threading
from typing import Optional


class Timer:
    """
    A context manager that displays real-time elapsed time for a process.

    Usage:
        with Timer(message="Processing data") as t:
            # Your code here
            pass

    The timer will update every second showing elapsed time, and print
    the final time when the context exits.
    """

    def __init__(self, message: str = "Process", update_interval: float = 1.0):
        """
        Initialize the Timer.

        Args:
            message (str): Message to display with the timer
            update_interval (float): How often to update the display in seconds
        """
        self.message = message
        self.update_interval = update_interval
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self._stop_event = threading.Event()
        self._timer_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def __enter__(self):
        """Start the timer when entering the context."""
        self.start_time = time.time()
        self._stop_event.clear()

        # Start the timer thread
        self._timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self._timer_thread.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop the timer when exiting the context."""
        self.end_time = time.time()

        # Stop the timer thread
        self._stop_event.set()
        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=2.0)  # Wait max 2 seconds

        # Print final time and move to new line
        elapsed = self.end_time - self.start_time
        with self._lock:
            sys.stdout.write(f'\r{self.message}: {self._format_time(elapsed)}\n')
            sys.stdout.flush()

    def _timer_loop(self):
        """Main timer loop running in a separate thread."""
        while not self._stop_event.is_set():
            if self.start_time is not None:
                elapsed = time.time() - self.start_time
                with self._lock:
                    # Use \r to return to beginning of line
                    sys.stdout.write(f'\r|> {self.message}: {self._format_time(elapsed)} <|')
                    sys.stdout.flush()

            # Wait for the update interval or until stopped
            self._stop_event.wait(self.update_interval)

    def _format_time(self, seconds: float) -> str:
        """Format time in a human-readable way."""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = seconds % 60
            return f"{minutes}m {secs:.1f}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            secs = seconds % 60
            return f"{hours}h {minutes}m {secs:.1f}s"

    @property
    def elapsed(self) -> Optional[float]:
        """Get current elapsed time."""
        if self.start_time is None:
            return None
        end = self.end_time or time.time()
        return end - self.start_time


# Convenience function for quick usage
def time_it(message: str = "Process", update_interval: float = 1.0):
    """
    Convenience function that returns a Timer context manager.

    Args:
        message (str): Message to display with the timer
        update_interval (float): How often to update the display in seconds

    Returns:
        Timer: A Timer context manager
    """
    return Timer(message, update_interval)


# Example usage and test functions
if __name__ == "__main__":
    import random


    def simulate_work(duration: float, name: str):
        """Simulate some work by sleeping."""
        print(f"Starting {name}")
        time.sleep(duration)
        print(f"Finished {name}")


    # Example 1: Basic usage
    print("=== Example 1: Basic Usage ===")
    with Timer("Processing dataset") as timer:
        simulate_work(3.5, "data processing")

    print()

    # Example 2: Multiple processes
    print("=== Example 2: Multiple Processes ===")
    processes = [
        ("Loading data", 2.1),
        ("Data transformation", 4.3),
        ("Model training", 6.7),
        ("Evaluation", 1.8)
    ]

    for process_name, duration in processes:
        with Timer(f"Step: {process_name}"):
            simulate_work(duration, process_name)

    print()

    # Example 3: Custom update interval
    print("=== Example 3: Fast Updates (0.5s interval) ===")
    with Timer("Quick process", update_interval=0.5):
        simulate_work(2.0, "quick work")

    # Example 4: Accessing elapsed time
    print("\n=== Example 4: Accessing Elapsed Time ===")
    with Timer("Monitored process") as t:
        simulate_work(1.0, "first part")
        print(f"\nIntermediate time: {t.elapsed:.1f}s")
        simulate_work(1.5, "second part")