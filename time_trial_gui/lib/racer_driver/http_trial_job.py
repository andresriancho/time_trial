import subprocess

from .http_utils import ParseException, parse_request

CPP_HTTP_TIMING_EXECUTABLE = '../racer/bin/run_http_timing_client'


def run_http_trial_job(trial):
    print("Executing HTTP Trial...")
    print(repr(trial.request))

    try:
        verb, path, version, body, headers = parse_request(bytes(trial.request,"iso-8859-1"))
    except ParseException as e:
        print("Unable to parse request: %s" % e)
        raise e

    cmd = [CPP_HTTP_TIMING_EXECUTABLE, trial.request_url + path, verb, version,
           body, str(trial.real_time), str(trial.core_affinity), " ",
           str(trial.reps)]
    cmd.extend(headers)

    print("Running %s, args %s" % (CPP_HTTP_TIMING_EXECUTABLE, cmd))
    return subprocess.check_output(cmd)
