#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#@created: 07.06.2011
#@author: Aleksey Komissarov
#@contact: ad3002@gmail.com 
'''
Experiment abstraction.
'''
import time
import random
import urllib
import simplejson
from multiprocessing import Pool 

STARTED = "Started"
FINISHED = "Finished"

timer_logger = Logger('timer logger')
exp_logger = Logger('exp logger')
core_logger = Logger('core logger')
runner_logger = Logger('run logger')
trseeker_logger = Logger('trseeker')

class ProcessRunner(object):
    '''
    '''
    def __init__(self):
        pass

    def run(self, command):
        '''
        '''
        runner_logger.info(command)
        os.system(command)
        # returncode = subprocess.call()
        # if returncode == "ERROR":
        #     # log error
        #     # set error status for step
        #     # abort batch
        #     pass
        # elif returncode == "OK":
        #     # log error
        #     # set error status for step
        #     # abort batch
        #     pass

    def run_batch(self, commands):
        '''
        '''
        for command in commands:
            self.run(command)

runner = ProcessRunner()


class Timer(object):
    '''
    Timer wrapper for code blocks.
    Using:

    >>> from PyExp.experiments.abstract_experiment import Timer
    >>> with Timer("Do something"):
    ...     sum([1,2,3])
    Started: [Do something]...
    6
    Finished: [Do something]  elapsed: 2.88486480713e-05
    '''
    
    def __init__(self, name=None):
        self.name = name
        if self.name:
            timer_logger.info('Started: [%s]...' % self.name)

    def __enter__(self):
        self.timer_start = time.time()

    def __exit__(self, type, value, traceback):
        message = ''
        if self.name:
            message = 'Finished: [%s]' % self.name
        delta = time.time() - self.timer_start
        minutes = int(delta) / 60
        seconds =int(delta) % 60
        message += ' elapsed: %s min %s sec ' % (minutes, seconds)
        timer_logger.info(message)

class AbstractStep(object):
    ''' Abstract step for exepriment is described by step name, input value,
    and core function.

    >>> name = "step_summation"
    >>> cf = sum
    >>> input = [1,2,3]
    >>> step = AbstractStep(name, data, cf, use_env=False)
    '''

    def __init__(self, name, data, cf, save_output=False, check_f=None, check_p=None):

        self.name = name
        self.sid = None
        self.input = data
        self.cf = cf
        self.check_f = check_f
        self.check_p = check_p
        self.save_output = save_output
        assert hasattr(cf, "__call__")
        if self.check_f:
            assert hasattr(self.check_f, "__call__")
        if self.check_p:
            assert isinstance(self.check_p, str)

    def __str__(self):
        return self.name

    def get_as_dict(self):
        return {
            'name': self.name,
            'cf': self.cf,
            'check': self.check_f,
            'pre': self.check_p,
            'save_output': self.save_output,
        }

class AbstractExperimentSettings(object):
    ''' Container for experimant settings.
    '''
    config = {}

    def __init__(self):
        self.folders = {}
        self.files = {}
        self.other = {}

    def as_dict(self):
        return {"files": self.files,
              "folders": self.folders,
              "other": self.other,
              "config": self.config,
        }

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
        self.logger = None
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
        ''' Add avaliable steps.'''
        raise NotImplemented

    ### Steps management section ###

    def add_step(self, step):
        """ Add a step to workflow."""
        assert step.__class__ == AbstractStep
        step.sid = self.sp
        self.sid2step[step.sid] = step
        self.sp += 1

    def get_all_steps(self):
        """ Get list of steps."""
        return [self.sid2step[i] for i in xrange(0, self.sp) if self.sid2step[i]]

    def get_step_names(self):
        '''
        '''
        result = []
        for x in self.get_avaliable_steps():
            result.append(x["name"])
        return result

    def get_avaliable_steps(self):
        ''' Return registered steps.'''
        return self.all_steps

    def print_steps(self):
        ''' Print sequence of added steps.'''
        steps = self.get_all_steps()
        for i, step in enumerate(steps):
            print "Step %s: %s" % (i, str(step))

    def get_step(self, sid):
        """ Get step by sid."""
        if sid < 0 or sid > self.sp:
            return  None
        return self.sid2step[sid]

    def find_step(self, name):
        """ Return step dict by name from avaliable steps."""
        for step_dict in self.all_steps:
            if name == step_dict["name"]:
                return step_dict
        return None

    def find_steps_by_stage(self, stage):
        """ Return step dicts by stage name from avaliable steps."""
        result = []
        for step_dict in self.all_steps:
            if stage == step_dict["stage"]:
                result.append(step_dict)
        return result

    def remove_step(self, sid):
        """ Remove a step by id."""
        self.sid2step[sid] = None

    def change_step(self, sid, new_step):
        """ Replace step."""
        new_step.sid = sid
        self.sid2step[sid] = new_step

    def get_as_dict(self):
        """ Dictionary representation of experiment."""
        return {
            'name': self.name,
            'steps': [ x.get_as_dict() for x in self.get_all_steps()], 
        }

    ### Execution section ###

    def execute(self, start_sid=0, end_sid=None, project_context=None):
        """ Execute sequence of steps."""
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
                # check prerequsites
                if step.check_p:
                    if not step.check_p in self.project["status"]:
                        self.project["status"] = None
                    status_p = self.project["status"][step.check_p]
                    if status_p != "OK":
                        print "Previous step %s's status is %s" % (step.check_p, status_p)
                        continue
                # skip finished
                if self.project["status"][step.name] == "OK":
                        print "Skipped completed step: %s" % step.name
                        continue
            if self.logger:
                print "Logget, start event", self.logger(self.pid, self.name, step.sid, step.name, STARTED)
            with Timer(step.name):
                # save step output
                result = None
                if step.input is None:
                    result = step.cf(self.settings, self.project)
                elif isinstance(step.input, dict):
                    result = step.cf(self.settings, self.project, **step.input)
                elif isinstance(step.input, list) or isinstance(step.input, tuple):
                    result = step.cf(self.settings, self.project, *step.input)
                else:
                    result = step.cf(self.settings, self.project, step.input)
                if self.logger:
                    print "Logget, finish event", self.logger(self.pid, self.name, step.sid, step.name, FINISHED)
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
            # send to server
            self.logger_update_project(self.project["pid"],
                            self.project)

    def execute_parallel(self, start_sid=0, end_sid=None, project_context=None, threads=1):
        '''
        '''
        pass
    
    ### Steps checking section ### 

    def check_step(self, step, exe_result):
        if step.check_f is None:
            print "Verification for step %s is absent" % step.name
            self.project["status"][step.name] = exe_result
            self.logger_update_status(self.project["pid"],  step.name, exe_result)
            return exe_result
        if not "status" in self.project:
            self.project["status"] = {}
        if not step.name in self.project["status"]:
            self.project["status"][step.name] = None
        if step.check_f:
            if not hasattr(step.check_f, "__call__"):
                print "Uncallable function for step %s" % step.name
                self.project["status"][step.name] = exe_result
                self.logger_update_status(self.project["pid"],  step.name, exe_result)
                return exe_result
            result = step.check_f(self.settings, self.project)
            if result is None:
                print "Result for step %s is None" % step.name
            # send to server
            self.project["status"][step.name] = result
            self.logger_update_status(self.project["pid"],  step.name, result)
            return result
        self.project["status"][step.name] = exe_result
        self.logger_update_status(self.project["pid"],  step.name, exe_result)
        return exe_result

    def check_avalibale_steps(self):
        ''' Check all avaliable steps.
        '''
        steps = self.get_avaliable_steps()
        for step in steps:
            real_step = AbstractStep(step["name"], 
                                     None, 
                                     step["cf"], 
                                     check_f=step["check"], 
                                     check_p=step["pre"])
            result = self.check_step(real_step, None)
            print real_step.name, result
        # send to server
        self.logger_update_project(self.project["pid"],
                        self.project)

    def reset_avalibale_steps(self):
        steps = self.get_avaliable_steps()
        for step in steps:
            self.project["status"][step["name"]] = None
        # send to server
        self.logger_update_project(self.project["pid"],
                        self.project)

    def check_steps(self):
        steps = self.get_all_steps()
        for step in steps:
            result = self.check_step(step, None)
            print step.name, result
        # send to server
        self.logger_update_project(self.project["pid"],
                        self.project)


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
            print "Removing file %s ..." % file_name
            try:
                os.unlink(file_name)
            except:
                print "Can't remove %s" % file_name
        for folder_name in self.settings['folders']:
            print "Removing folder %s ..." % folder_name
            for root, dirs, files in os.walk(folder_name, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))

    ### Methods related to project status update ###

    def logger_update_status(self, pid, step_name, status):
        if not "config" in self.settings or not "url_status_update" in self.settings["config"]:
            print "To submit data to server set url_status_update in config file."
            return
        url = self.settings["config"]["url_status_update"]
        data = {
            'pid': pid,
            'step_name': step_name,
            'status':status,
        }
        self._send_to_server(url, data)
        
    def logger_update_project(self, pid, project):
        if self.manager:
            self.manager.save(pid, project)
        if not "config" in self.settings or not "url_project_update" in self.settings["config"]:
            print "To submit data to server set url_project_update in config file."
            return
        url = self.settings["config"]["url_project_update"]
        project = simplejson.dumps(project)
        data = {
            'project': project,
        }
        self._send_to_server(url, data)

    def logger_send_project(self, pid, project):
        if not "config" in self.settings or not "url_project_update" in self.settings["config"]:
            print "To submit data to server set url_project_update in config file."
            return
        url = self.settings["config"]["url_project_update"]
        project = simplejson.dumps(project)
        data = {
            'project': project,
        }
        self._send_to_server(url, data)

    def check_and_upload_project(self):
        if not "status" in self.project:
            self.project["status"] = {}
        steps = self.get_avaliable_steps()
        for step in steps:
            if not step["name"] in self.project["status"]:
                self.project["status"][step["name"]] = None
                self.check_step(step, None)
        self.logger_update_project(self.project["pid"],
                        self.project)

    def upload_to_server(self, url, data):
        '''
        ''' 
        self._send_to_server(url, data)

    def _send_to_server(self, url, data):
        '''
        '''
        if not self.send_to_server:
            return
        if self._skip_server_part:
            print "Server part is skipped!"
            return
        attempts = 0
        data = urllib.urlencode(data)
        while attempts < 3:
            try:
                resp = urllib.urlopen(url, data).read()
                print resp
                break
            except Exception, e:
                print e
                time.sleep(3)
                attempts += 1
        if attempts == 3:
            self._skip_server_part = True