#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#@created: 07.06.2011
#@author: Aleksey Komissarov
#@contact: ad3002@gmail.com 
"""
Experiment abstraction.
"""
import time
import os
import urllib
try:
    import simplejson
    from logbook import Logger
except:
    class Logger(object):

        def __init__(self, t):
            self.type = t

        def info(self, m):
            print(self.type, m)

        
    print("No logbook installed")
import subprocess

STARTED = "Started"
FINISHED = "Finished"

timer_logger = Logger('timer logger')
exp_logger = Logger('exp logger')
core_logger = Logger('core logger')
runner_logger = Logger('run logger')
trseeker_logger = Logger('trseeker')


class ProcessRunner(object):
    """ Wrapper for running commands in shell.
    """
    def __init__(self):
        pass

    def run(self, command, log_file=None, verbose=True, mock=False):
        """
        Run command in shell.
        :param command: one command or list ot  commands for shell
        :param log_file: name of log file for appending executed command, default=None
        :param verbose: echo command with logger, default=True
        """
        if isinstance(command, list):
            return self.run_batch(command)
        if log_file:
            with open(log_file, "a") as fh:
                fh.write("%s\n" % command)
        if verbose:
            print(command)
            runner_logger.info(command)
        if not mock:
            os.system(command)

    def run_batch(self, commands):
        """
        Run commands one by one.
        :param commands: list of commands for shell
        """
        for command in commands:
            self.run(command)

    def run_parallel_no_output(self, commands, mock=False):
        """
        Run commands in parallel with subprocess.Popen
        :param commands: list of commands for shell
        :param mock: don't run command
        """
        ps = set()
        if not isinstance(commands, list):
            message = "Expected list get %s" % str(commands)
            runner_logger.error(message)
            raise Exception(message)
        for command in commands:
            runner_logger.info(command)
            if not mock:
                ps.add(subprocess.Popen(command, shell=True))
        n = len(ps)
        for p in ps:
            p.wait()
            n -= 1
            runner_logger.info('A process returned: %s (remains %s)' % (p.returncode, n))


    def run_asap(self, commands, cpu=10, mock=False):
        """
        Run large number of commands in parallel with subprocess.Popen
        :param commands: list of commands for shell
        :param cpu: number of cpu
        :param mock: don't run command
        """
        if not isinstance(commands, list):
            message = "Expected list get %s" % str(commands)
            runner_logger.error(message)
            raise Exception(message)
        running = []
        while commands:
            while len(running) > cpu:
                runner_logger.debug("Checking %s processes from (%s)" % (len(running), len(commands)))
                for i, p in enumerate(running):
                    returncode = p.poll()
                    if returncode is not None:
                        if returncode == 0:
                            runner_logger.info('A process returned: %s (remains %s)' % (p.returncode, len(commands)))
                        else:
                            runner_logger.error('A process returned error: %s (remains %s)' % (p.returncode, len(commands)))
                        running[i] = None
                        running = [x for x in running if x is not None]
                        break
                time.sleep(1)
            command = commands.pop()
            runner_logger.info(command)
            if not mock:
                running.append(subprocess.Popen(command, shell=True))
        

    def popen(self, command, silent=False):
        """
        Run command with Popen.
        :param silent: don't log output and errors
        :param command: command for shell
        """
        runner_logger.info("Running: %s" % command)
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        output, error = process.communicate()
        if not silent:
            runner_logger.debug("Output: %s" % output)
            runner_logger.debug("Error: %s" % error)
        if process.returncode != 0:
            message = "ERROR when launching '%s', code %s, output %s" % (command, process.returncode, output)
            runner_logger.error(message)
            raise Exception(message)
        return output, error

runner = ProcessRunner()


class Timer(object):
    """
    Timer wrapper for code blocks.
    Using:

    >>> from PyExp.experiments.abstract_experiment import Timer
    >>> with Timer("Do something"):
    ...     sum([1,2,3])
    Started: [Do something]...
    6
    Finished: [Do something]  elapsed: 2.88486480713e-05
    """
    
    def __init__(self, name=None):
        self.name = name
        self.timer_start = None
        if self.name:
            timer_logger.info('Started: [%s]...' % self.name)

    def __enter__(self):
        self.timer_start = time.time()

    def __exit__(self, *args):
        message = ''
        if self.name:
            message = 'Finished: [%s]' % self.name
        delta = time.time() - self.timer_start
        minutes = int(delta) / 60
        seconds = int(delta) % 60
        hours = 0
        if minutes > 60:
            hours = minutes / 60
            minutes = minutes % 60
        if hours:
            message += ' elapsed: %s h %s min %s sec ' % (hours, minutes, seconds)
        else:
            message += ' elapsed: %s min %s sec ' % (minutes, seconds)
        timer_logger.info(message)


class AbstractStep(object):
    """ Abstract step for experiment is described by step name, input value,
    and core function.

    >>> name = "step_summation"
    >>> cf = sum
    >>> some_input = [1,2,3]
    >>> step = AbstractStep(name, data, cf, use_env=False)
    """

    def __init__(self, name, data, cf, save_output=False, check_f=None, check_p=None, check_value=None):

        self.name = name
        self.sid = None
        self.input = data
        self.cf = cf
        self.check_f = check_f
        self.check_p = check_p
        self.check_value = check_value
        self.save_output = save_output
        assert hasattr(cf, "__call__")
        if self.check_f:
            assert hasattr(self.check_f, "__call__")
        if self.check_p:
            assert hasattr(self.check_p, "__call__")
        if self.check_value:
            assert isinstance(self.check_value, str)

    def __str__(self):
        return self.name

    def get_as_dict(self):
        """ Return step as python dictionary.
        :return: step dictionary
        """
        return {
            'name': self.name,
            'cf': self.cf,
            'check': self.check_f,
            'pre': self.check_p,
            'check_value': self.check_value,
            'save_output': self.save_output,
        }

    def as_dict(self):
        """ Return step as python dictionary.
        :return: step dictionary
        """
        return self.get_as_dict()


class AbstractExperimentSettings(object):
    """ Container for experiment settings.
    """
    config = {}

    def __init__(self):
        self.folders = {}
        self.files = {}
        self.other = {}

    def get_as_dict(self):
        """ Return step as python dictionary.
        :return: step dictionary
        """
        return {"files": self.files,
                "folders": self.folders,
                "other": self.other,
                "config": self.config,
        }

    def as_dict(self):
        """ Return step as python dictionary.
        :return: step dictionary
        """
        return self.get_as_dict()


class AbstractExperiment(object):
    """ Class for an abstract experiment.
    An experiment is a sequence of steps (AbstractStep).
    """

    all_steps = None

    ### Initialization section ###

    def __init__(self, settings, project, **kwargs):
        """ Init class 
        kwargs:
            - name
            - logger
            - force
            - manager
            - send_to_server
        """
        # init empty class
        if settings is None and project is None:
            self.init_steps()
            return
        self.name = 'default'
        if 'name' in kwargs:
            self.name = kwargs['name']
        self.logger = self.default_logger
        if 'logger' in kwargs:
            logger = kwargs['logger']
            if hasattr(logger, "__call__"):
                self.logger = logger
        self.force = False
        if 'force' in kwargs:
            self.force = kwargs['force']
        self.manager = None
        if 'manager' in kwargs:
            self.manager = kwargs['manager']
        self.send_to_server = None
        if 'send_to_server' in kwargs:
            self.send_to_server = kwargs['send_to_server']
        self.settings = settings
        self.project = project
        self.sp = 0
        self.pid = project["pid"]
        self.sid2step = {}
        self.all_steps = {}
        self.init_steps()
        self.settings["manager"] = self.manager
        self.settings["experiment"] = self
        self._skip_server_part = False

    def init_steps(self):
        """ Add available steps."""
        raise NotImplemented

    ### Steps management section ###

    def add_step(self, step):
        """ Add a step to workflow.
        :param step: instance of AbstractStep
        """
        assert step.__class__ == AbstractStep
        step.sid = self.sp
        self.sid2step[step.sid] = step
        self.sp += 1

    def get_all_steps(self):
        """ Get list of steps."""
        return [self.sid2step[i] for i in xrange(0, self.sp) if self.sid2step[i]]

    def get_step_names(self):
        """ Return list of all steps.
        """
        result = []
        for x in self.get_available_steps():
            result.append(x["name"])
        return result

    def get_available_steps(self):
        """ Return registered steps."""
        return self.all_steps

    def print_steps(self):
        """ Print sequence of added steps."""
        steps = self.get_all_steps()
        for i, step in enumerate(steps):
            exp_logger.info("Step %s: %s" % (i, str(step)))

    def get_step(self, sid):
        """ Get step by sid.
        :param sid: step sid
        """
        if sid < 0 or sid > self.sp:
            return None
        return self.sid2step[sid]

    def find_step(self, name):
        """ Return step dict by name from available steps.
        :param name: step name.
        """
        for step_dict in self.all_steps:
            if name == step_dict["name"]:
                return step_dict
        return None

    def find_steps_by_stage(self, stage):
        """ Return step dicts by stage name from available steps.
        :param stage: stage name.
        """
        result = []
        for step_dict in self.all_steps:
            if stage == step_dict["stage"]:
                result.append(step_dict)
        return result

    def remove_step(self, sid):
        """ Remove a step by id.
        :param sid: step sid.
        """
        self.sid2step[sid] = None

    def change_step(self, sid, new_step):
        """ Replace step.
        :param sid: step sid
        :param new_step: instance of AbstractStep
        """
        new_step.sid = sid
        self.sid2step[sid] = new_step

    def get_as_dict(self):
        """ Dictionary representation of experiment."""
        return {
            'name': self.name,
            'steps': [x.get_as_dict() for x in self.get_all_steps()],
        }

    ### Execution section ###

    def execute(self, start_sid=0, end_sid=None, project_context=None):
        """ Execute sequence of steps.
        :param start_sid: start step sid
        :param end_sid: end step sid
        :param project_context: project context dictionary
        """
        steps = self.get_all_steps()
        for step in steps[start_sid:end_sid]:
            # refresh project
            self.project, _settings = self.manager.get_project(self.project["pid"], project_context=project_context)
            if not "status" in self.project:
                self.project["status"] = {}
            if not step.name in self.project["status"]:
                self.project["status"][step.name] = None
            # check prerequisites
            if not self.force:
                # skip finished
                if step.check_value:
                    status_p = self.project["status"][step.name]
                    if status_p == step.check_value:
                        exp_logger.warning("Step skipped. Step %s was previously computed with %s" % (step.name, status_p))
                        continue
            if self.logger:
                exp_logger.info("Logger, start event", self.logger(self.pid, self.name, step.sid, step.name, STARTED))
            with Timer(step.name):
                # save step output
                if step.check_p is not None and hasattr(step.check_p, "__call__"):
                    exp_logger.info("Compute prerequisites for step %s" % step.name)
                    result = step.check_p(self.settings, self.project)
                    if result is not None:
                        exp_logger.error("Compute prerequisites for step %s is failed with %s" % (step.name, result))
                        self.project["status"][step.name] = result
                        continue
                if step.input is None:
                    result = step.cf(self.settings, self.project)
                elif isinstance(step.input, dict):
                    result = step.cf(self.settings, self.project, **step.input)
                elif isinstance(step.input, list) or isinstance(step.input, tuple):
                    result = step.cf(self.settings, self.project, *step.input)
                else:
                    result = step.cf(self.settings, self.project, step.input)
                if self.logger:
                    exp_logger.info("Logger, finish event", self.logger(self.pid, self.name, step.sid, step.name, FINISHED))
                # save step output
                if step.save_output:
                    if result is None:
                        pass
                    if isinstance(result, dict):
                        for key, value in result.items():
                            self.settings[key] = value
                    else:
                        self.settings[step.name] = result
            # post verification
            self.check_step(step, result)
            # update project
            self.logger_update_project(self.project["pid"], self.project)

    def execute_parallel(self, start_sid=0, end_sid=None, project_context=None, threads=1):
        """
        Run experiments on different datasets in parallel.
        :param start_sid:
        :param end_sid:
        :param project_context:
        :param threads:
        """
        raise NotImplemented
    
    ### Steps checking section ### 

    def check_step(self, step, exe_result):
        """ Check step result.
        """
        if not "status" in self.project:
            self.project["status"] = {}
        if not step.name in self.project["status"]:
            self.project["status"][step.name] = None
        if step.check_f is None:
            exp_logger.warning("Verification for step %s is absent" % step.name)
        if step.check_f:
            if not hasattr(step.check_f, "__call__"):
                exp_logger.warning("Uncallable function for step %s" % step.name)
            result = step.check_f(self.settings, self.project)
            if result is None:
                exp_logger.info("Result for step %s is None" % step.name)
        self.project["status"][step.name] = exe_result
        self.logger_update_status(self.project["pid"],  step.name, exe_result)
        return exe_result

    def check_avalibale_steps(self):
        """ Check all avaliable steps.
        """
        steps = self.get_available_steps()
        for step in steps:
            real_step = AbstractStep(step["name"], 
                                     None, 
                                     step["cf"], 
                                     check_f=step["check"], 
                                     check_p=step["pre"])
            result = self.check_step(real_step, None)
            exp_logger.info("%s\t%s" % (real_step.name, result))
        # send to server
        self.logger_update_project(self.project["pid"],
                        self.project)

    def reset_avalibale_steps(self):
        steps = self.get_available_steps()
        for step in steps:
            self.project["status"][step["name"]] = None
        # send to server
        self.logger_update_project(self.project["pid"], self.project)

    def check_steps(self):
        """
        Check steps.
        """
        steps = self.get_all_steps()
        for step in steps:
            result = self.check_step(step, None)
            exp_logger.info("%s\t%s" % (step.name, result))
        # send to server
        self.logger_update_project(self.project["pid"], self.project)

    ### Methods related to settings ###
    def clear_settings(self):
        """ Clear settings."""
        self.settings = None

    def get_settings(self):
        """ Get settings."""
        return self.settings

    def remove_project_data(self):
        """ Remove all project data.
        """
        for file_name in self.settings["files"]:
            print("Removing file %s ..." % file_name)
            try:
                os.unlink(file_name)
            except:
                print("Can't remove %s" % file_name)
        for folder_name in self.settings['folders']:
            print("Removing folder %s ..." % folder_name)
            for root, dirs, files in os.walk(folder_name, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

    ### Methods related to project status update ###

    def default_logger(self, pid, name, step_sid, step_name, status):
        """ Send data to url_exe_update url.
        """
        data  = {
            "pid": pid,
            "name": name,
            "step_sid": step_sid,
            "step_name": step_name,
            "status": status,
            "step": self.get_step(step_sid).as_dict(),
        }
        if not "config" in self.settings or not "url_exe_update" in self.settings["config"]:
            print("To submit data to server set url_exe_update in config file.")
            return
        url = self.settings["config"]["url_exe_update"]
        self._send_to_server(url, data)

    def logger_update_status(self, pid, step_name, status):
        """
        """
        if not "config" in self.settings or not "url_status_update" in self.settings["config"]:
            print("To submit data to server set url_status_update in config file.")
            return
        url = self.settings["config"]["url_status_update"]
        data = {
            'pid': pid,
            'step_name': step_name,
            'status':status,
        }
        self._send_to_server(url, data)
        
    def logger_update_project(self, pid, project):
        """
        """
        if self.manager:
            self.manager.save(pid, project)
        if not "config" in self.settings or not "url_project_update" in self.settings["config"]:
            print("To submit data to server set url_project_update in config file.")
            return
        url = self.settings["config"]["url_project_update"]
        project = simplejson.dumps(project)
        data = {
            'project': project,
        }
        self._send_to_server(url, data)

    def logger_send_project(self, pid, project):
        """ Send project to server.
        :param pid:
        :param project:
        :return: None
        """
        if not "config" in self.settings or not "url_project_update" in self.settings["config"]:
            print("To submit data to server set url_project_update in config file.")
            return
        url = self.settings["config"]["url_project_update"]
        project = simplejson.dumps(project)
        data = {
            'project': project,
        }
        self._send_to_server(url, data)

    def check_and_upload_project(self):
        """
        Check and save/upload project.
        """
        if not "status" in self.project:
            self.project["status"] = {}
        steps = self.get_available_steps()
        for step in steps:
            if not step["name"] in self.project["status"]:
                self.project["status"][step["name"]] = None
                self.check_step(step, None)
        self.logger_update_project(self.project["pid"], self.project)

    def upload_to_server(self, url, data):
        """
        :param url: server url
        :param data: data to send
        """
        self._send_to_server(url, data, force=True)

    def _send_to_server(self, url, data, force=False):
        """
        """
        if not force and self.send_to_server is None:
            return
        if not force and self._skip_server_part:
            exp_logger.info("Server part is skipped!")
            return
        attempts = 0
        data = urllib.urlencode(data)
        while attempts < 3:
            try:
                exp_logger.info("Sending data to url %s..." % (url))
                response = urllib.urlopen(url, data).read()
                exp_logger.info("Failed sent to url %s with response: %s" % (url, response))
                break
            except Exception as e:
                print(e)
                time.sleep(3)
                attempts += 1
        if attempts == 3:
            self._skip_server_part = True