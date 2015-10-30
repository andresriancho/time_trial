__author__ = 'daniel'

from .http_trial_job import run_http_trial_job
from .echo_trial_job import run_echo_trial_job
from .x_runtime_job import run_x_runtime_job


TRIALS = {'HTTPTrialJob': run_http_trial_job,
          'EchoTrialJob': run_echo_trial_job,
          'XRunTimeTrialJob': run_x_runtime_job}


def execute_trial(trial):
    trial_klass = trial.__class__.__name__
    trial_runner = TRIALS.get(trial_klass)
    return trial_runner(trial)


