__author__ = 'daniel'


class TrialJob:
    def __init__(self):
        self.real_time = 1
        self.core_affinity = 1
        self.reps = 1

    @classmethod
    def from_model(cls, model):
        raise NotImplementedError


class EchoTrialJob(TrialJob):
    def __init__(self):
        TrialJob.__init__(self)
        # in nanoseconds (for now :-/)
        self.delay = 100
        self.target_host = ""
        self.target_port = ""

    @classmethod
    def from_model(cls, model):
        job = cls()
        job.target_host = model.host
        job.target_port = model.port
        job.delay = model.delay        
        return job


class HTTPTrialJob(TrialJob):
    def __init__(self):
        TrialJob.__init__(self)
        self.request_url = ""
        self.request = ""

    @classmethod
    def from_model(cls, model):
        job = cls()
        job.request = model.request
        job.request_url = model.request_url
        return job


class XRuntimeTrialJob(TrialJob):
    def __init__(self):
        TrialJob.__init__(self)
        self.request_url = ""
        self.request = ""

    @classmethod
    def from_model(cls, model):
        job = cls()
        job.request = model.request
        job.request_url = model.request_url
        return job


def job_factory(trial_model):
    trial_model_klass = trial_model.__class__.__name__
    trial_jobs = {'HTTPTrial': HTTPTrialJob,
                  'XRuntimeTrial': XRuntimeTrialJob,
                  'EchoTrial': EchoTrialJob}
    return trial_jobs.get(trial_model_klass).from_model(trial_model)