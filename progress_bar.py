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

    def __init__(self,
                 start_progress=0,
                 max_progress=100,
                 quit_on_finish=True,
                 status_message='',
                 start_message=None,
                 end_message=None,
                 interval=0.1):
        self.current_progress = start_progress
        self.max_progress = max_progress
        self.status_message = status_message
        self.kill = False
        self.writer = threading.Thread(target=self._show_progress,
                                       daemon=True,
                                       args=(interval,
                                             quit_on_finish,
                                             start_message,
                                             end_message))
        self.writer.start()

    def update_progress(self, increment_amount=1):
        self.current_progress = min(self.max_progress, self.current_progress + increment_amount)

    def kill_bar(self):
        self.kill = True

    def _show_progress(self, interval, quit_on_finish, start_message, end_message):
        bar_len = 60
        if start_message:
            sys.stdout.write(start_message + '\n')
            sys.stdout.flush()
        while True:
            current_percent = min(float(self.current_progress) / float(self.max_progress), 1)
            filled_len = int(round(bar_len * current_percent))

            percents = round(100.0 * current_percent, 1)
            bar = '█' * filled_len + ' ' * (bar_len - filled_len)

            sys.stdout.write('[%s] %s%s ...%s\r' % (bar, percents, '%', self.status_message))
            sys.stdout.flush()
            if self.kill or (quit_on_finish and current_percent >= 1):
                sys.stdout.write('\n')
                sys.stdout.flush()
                break

            time.sleep(interval)

        if end_message:
            sys.stdout.write(end_message + '\n')
            sys.stdout.flush()

if __name__ == '__main__':
    progress_bar = ProgressBar(start_message='Starting a progress bar.',
                               end_message='Progress complete.')
    for i in range(0, 100):
        progress_bar.update_progress()
        time.sleep(0.05)

    time.sleep(2)



