import time
import sys


def simple_progress_bar(total, update_interval=0.1):
    for i in range(total + 1):
        progress = i / total
        bar_length = 20
        filled_length = int(bar_length * progress)
        bar = '#' * filled_length + '-' * (bar_length - filled_length)

        # Construct the progress line
        line = f'\rProgress: [{bar}] {progress:.0%}'

        # Write the line and flush immediately
        sys.stdout.write(line)
        sys.stdout.flush()

        time.sleep(update_interval)

    # Print a newline at the end to move to the next line
    print()

