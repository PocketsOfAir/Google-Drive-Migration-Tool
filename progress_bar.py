# The MIT License (MIT)
# Copyright (c) 2016 Vladimir Ignatev
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software
# is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
# PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
# FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
# OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
import sys
import time
import threading


class ProgressBar:

    def __init__(self, start_progress, max_progress, status_message=''):
        self.current_progress = start_progress
        self.max_progress = max_progress
        self.status_message = status_message

    def update_progress(self, increment_amount=1):
        self.current_progress = min(self.max_progress, self.current_progress + increment_amount)

    def show_progress(self):
        bar_len = 60
        filled_len = int(round(bar_len * float(self.current_progress) / float(self.max_progress)))

        percents = round(100.0 * float(self.current_progress) / float(self.max_progress), 1)
        bar = '█' * filled_len + ' ' * (bar_len - filled_len)

        sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', self.status_message))

    @property
    def is_finished(self):
        return self.current_progress >= self.max_progress


class ProgressWriter:

    def __init__(self):
        self.progress_bars = []
        self.writer = None

    def add_progress_bar(self, new_bar):
        if new_bar is not None:
            self.progress_bars.append(new_bar)

    def remove_bar(self, old_bar):
        if old_bar in self.progress_bars:
            self.progress_bars.remove(old_bar)

    def _print_all(self, interval=0.1, quit_on_finish=True):
        while len(self.progress_bars) and self.writer:
            for bar in self.progress_bars:
                bar.show_progress()
                sys.stdout.write('\r')
                if quit_on_finish and bar.is_finished:
                    self.progress_bars.remove(bar)

            sys.stdout.flush()
            time.sleep(interval)

    def start_writing(self, interval=0.1, quit_on_finish=True):
        if not self.writer:
            self.writer = threading.Thread(target=self._print_all, args=(interval, quit_on_finish))
            self.writer.start()

    def stop_writing(self):
        self.writer = None

if __name__ == '__main__':
    writer = ProgressWriter()

    fast_bar = ProgressBar(0, 100, 'Fast')
    mid_bar = ProgressBar(0, 200, 'Mid')
    slow_bar = ProgressBar(0, 500, 'Slow')
    writer.add_progress_bar(fast_bar)
    writer.add_progress_bar(mid_bar)
    writer.add_progress_bar(slow_bar)

    writer.start_writing()

    for i in range(0, 501):
        fast_bar.update_progress()
        mid_bar.update_progress()
        slow_bar.update_progress()
        time.sleep(0.1)



