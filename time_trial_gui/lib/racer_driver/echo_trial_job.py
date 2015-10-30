import subprocess

CPP_ECHO_TIMING_EXECUTABLE = "../racer/bin/run_timing_client"


def run_echo_trial_job(trial):
    print("Executing Echo Trial...")
    #TODO: get this from a config file
    cmd = []
    cmd.append(CPP_ECHO_TIMING_EXECUTABLE)
    cmd.append(trial.target_host)
    cmd.append(str(trial.target_port))
    cmd.append(str(int(trial.real_time)))
    cmd.append(str(trial.core_affinity))
    cmd.append(str(trial.delay))
    cmd.append(str(trial.reps))
    print(cmd)

    return subprocess.check_output(cmd)

