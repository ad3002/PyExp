#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#@created: 07.06.2011
#@author: Aleksey Komissarov
#@contact: ad3002@gmail.com 

import time

class Timer(object):
    '''
    Timer wrapper for code blocks. 
    Using:
        with Timer("Do something"):
            your_function()
    '''
    def __init__(self, name=None):
        self.name = name
        if self.name:
            print 'Started: [%s]...' % self.name

    def __enter__(self):
        self.timer_start = time.time()

    def __exit__(self, type, value, traceback):
        if self.name:
            print 'Finished: [%s]' % self.name,
        print ' elapsed: %s' % (time.time() - self.timer_start)

class AbstractStep(object):
    '''
        Abstract step for exepriment is described by step name, input value,
        and core function.
    '''

    def __init__(self, name, input, cf, use_env=False):

        self.name = name
        self.sid = None
        self.input = input
        self.cf = cf
        self.use_env = use_env
        assert hasattr(cf, "__call__")

    def __str__(self):
        return self.name


class AbstractExperiment(object):
    """
        Class for an abstract experiment.
        
        An experimenr is a number of steps (AbstractStep).
        
        Public properties:
        enviroment is a dictionary of values used by steps.
        
        Public methods:
        add_step(self, step)
        get_all_steps(self) -> list of step objects
        get_step(self, sid) -> step object
        remove_step(self, sid)
        change_step(self, sid, new_step)
        execute(self, start_sid=0, end_sid=None)
        clear_env(self)
    """

    def __init__(self):
        """ Init class """
        self.sp = 0
        self.sid2step = {}
        self.enviroment = {}

    def add_step(self, step):
        """ Add a step to workflow."""
        step.sid = self.sp
        self.sid2step[step.sid] = step
        self.sp += 1

    def get_all_steps(self):
        """ Get list of steps."""
        return [self.sid2step[i] for i in xrange(0, self.sp) if self.sid2step[i]]

    def print_steps(self):
        steps = self.get_all_steps()
        for i, step in enumerate(steps):
            print "Step %s: %s" % (i, str(step))

    def get_step(self, sid):
        """ Get step by sid."""
        return self.sid2step[sid]

    def remove_step(self, sid):
        """ Remove a step by id."""
        self.sid2step[sid] = None

    def change_step(self, sid, new_step):
        """ Replace step."""
        new_step.sid = sid
        self.sid2step[sid] = new_step

    def execute(self, start_sid=0, end_sid=None):
        """ Execute sequence of steps."""
        steps = self.get_all_steps()
        for step in steps[start_sid:end_sid]:
            with Timer(step.name):
                if not step.use_env:
                    if type(step.input) is tuple:
                        result = step.cf(*step.input)
                    else:
                        result = step.cf(step.input)
                else:
                    result = step.cf(step.input, self.enviroment)
                if result is None:
                    continue
                if result.__class__ is dict:
                    for key, value in result.items():
                        self.enviroment[key] = value
                else:
                    self.enviroment[step.name] = result

    def clear_env(self):
        """ Clear enviroment."""
        self.enviroment = None
