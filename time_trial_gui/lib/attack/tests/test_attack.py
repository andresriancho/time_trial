import unittest
import uuid

from itertools import repeat
from mock import Mock, call

from models.trial import XRuntimeTrial
from lib.attack.attack import TimeAttack

URL = 'http://time.trial.com/'
ACCEPTED_CHARSET = '01234abcd'
VALID_TOKEN = 'abc444'
UNKNOWN_TOKEN = 'abc234'
HTTP_REQUEST = '''GET /password_reset/$TIME_TRIAL$ HTTP/1.1
Host: time.trial.com
'''

RACER_SHORTER = '''\
0;1234
0;1235
0;1236
0;1237
0;1238
'''

RACER_NEAR_SHORTER = '''\
0;1244
0;1245
0;1246
0;1247
0;1248
'''

RACER_LONGER = '''\
0;1634
0;1635
0;1636
0;1637
0;1638
'''


class JobResult(object):
    def __init__(self):
        self.uuid = None

    def get_id(self):
        if self.uuid is None:
            self.uuid = uuid.uuid4()

        return self.uuid


class ShorterJobResult(JobResult):
    result = RACER_SHORTER


class LongerJobResult(JobResult):
    result = RACER_LONGER


class TestTimeAttack(unittest.TestCase):
    def generate_racer_results(self, valid_token, accepted_charset, start_after,
                               unknown_token):
        """
        This method mirrors the algorithm implemented in attack.py, needs to be
        updated for unittests to PASS.

        :return: A list of ShorterJobResult/LongerJobResult instances
        """
        known_chars = valid_token[:start_after]
        missing_chars = len(unknown_token) - len(known_chars)

        for i in range(missing_chars):
            for guess_char in accepted_charset:
                if guess_char == unknown_token[len(known_chars)]:
                    known_chars += guess_char
                    yield LongerJobResult()
                    break
                else:
                    yield ShorterJobResult()

    def test_simplest_time_attack(self):

        #log_mock = mock.Mock()
        log_mock = print
        new_char_mock = Mock()

        trial = XRuntimeTrial()
        trial.request_url = URL
        trial.request = HTTP_REQUEST

        time_attack = TimeAttack(trial=trial,
                                 accepted_charset=ACCEPTED_CHARSET,
                                 valid_token=VALID_TOKEN,
                                 start_after=2,
                                 on_log_message=log_mock,
                                 on_new_char_found=new_char_mock,
                                 bruteforce_last_chars=False)

        mocked_results = self.generate_racer_results(VALID_TOKEN,
                                                     ACCEPTED_CHARSET,
                                                     2, UNKNOWN_TOKEN)

        time_attack.enqueue_job = Mock(side_effect=mocked_results)
        time_attack.sleep = lambda x: None
        timed_token = time_attack.run()

        self.assertEqual(new_char_mock.call_args_list,
                         [call('c'), call('2'), call('3'), call('4')])
        self.assertEquals(timed_token, UNKNOWN_TOKEN)

    def test_all_responses_equal(self):

        #log_mock = mock.Mock()
        log_mock = print
        new_char_mock = Mock()

        trial = XRuntimeTrial()
        trial.request_url = URL
        trial.request = HTTP_REQUEST

        time_attack = TimeAttack(trial=trial,
                                 accepted_charset=ACCEPTED_CHARSET,
                                 valid_token=VALID_TOKEN,
                                 start_after=2,
                                 on_log_message=log_mock,
                                 on_new_char_found=new_char_mock,
                                 bruteforce_last_chars=False)

        time_attack.enqueue_job = Mock(side_effect=repeat(ShorterJobResult()))
        time_attack.sleep = lambda x: None
        timed_token = time_attack.run()

        self.assertEqual(new_char_mock.call_args_list, [])
        self.assertEquals(timed_token, VALID_TOKEN[:2])