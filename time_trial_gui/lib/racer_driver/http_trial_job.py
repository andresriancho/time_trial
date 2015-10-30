import pprint
import subprocess

from .http_utils import ParseException, parse_request

CPP_HTTP_TIMING_EXECUTABLE = '../racer/bin/run_http_timing_client'


def run_http_trial_job(trial):
    print("Executing HTTP Trial...")
    pprint.pprint(trial.request)

    try:
        verb, path, version, body, headers = parse_request(bytes(trial.request,"iso-8859-1"))
    except ParseException as e:
        print("Unable to parse request: %s" % e)
        raise e

    cmd = [CPP_HTTP_TIMING_EXECUTABLE, trial.request_url + path, verb, version,
           body, str(trial.real_time), str(trial.core_affinity), " ",
           str(trial.reps)]
    cmd.extend(headers)

    print("Running %s with arguments:" % CPP_HTTP_TIMING_EXECUTABLE)
    for arg in cmd[1:]:
        print('%s' % arg)
    output = subprocess.check_output(cmd)

    print('Trial output:')
    print(output)
    
    return output
