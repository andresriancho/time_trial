import pprint
import requests

from .http_utils import ParseException, parse_request


def run_x_runtime_job(trial):
    """
    Note that we can run this in pure python because the timing information is
    measured remotely by rack [0] and we don't need precise timing
    on our side.

    [0] https://github.com/rack/rack/blob/master/lib/rack/runtime.rb

    :param trial: The test to run, as configured by the user
    :return: The results in CSV format (seconds;nanoseconds)
    """
    print("Executing HTTP X-Runtime Trial...")
    pprint.pprint(trial.request)

    try:
        verb, path, version, body, headers = parse_request(bytes(trial.request,"iso-8859-1"))
    except ParseException as e:
        print("Unable to parse request: %s" % e)
        raise e

    session = requests.Session()
    url = trial.request_url + path

    raw_request = requests.Request(verb, url, data=body, headers=dict(headers))
    prepared_request = raw_request.prepare()

    output = []

    for i in range(trial.reps):
        try:
            response = session.send(prepared_request, verify=False)
        except Exception as e:
            print('Exception while sending request: "%s"' % e)
        else:
            # X-Runtime: 0.043636
            x_runtime = response.headers.get('X-Runtime', None)
            if x_runtime is None:
                print('The remote server did NOT send X-Runtime header')
                continue
            else:
                print('[%s/%s] X-Runtime: %s' % (i, trial.reps, x_runtime))

            # First part before the dot is seconds
            seconds = x_runtime.split('.')[0]

            # Not sure if I can call this nano-seconds, but it doesn't matter
            # much since we'll be comparing always the same type of results
            nanoseconds = x_runtime.split('.')[1]

            output.append((seconds, nanoseconds))

    output_str = ''
    for seconds, nanoseconds in output:
        output_str += '%s;%s\n' % (seconds, nanoseconds)

    return output_str
