#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#@created: 04.06.2011
#@author: Aleksey Komissarov
#@contact: ad3002@gmail.com 
import sys
import shutil
import yaml
from abstract_experiment import AbstractStep
from abstract_manager import ProjectManagerException
from logbook import Logger

app_logger = Logger('App logger')

def _create_projects(exp_settings_class, manager_class, all_projects):
    ''' Init project data and settings.
    '''    
    for pid, project_data in all_projects:
        experiment_settings = exp_settings_class()
        manager = manager_class(experiment_settings)
        try:    
            project, settings = manager.get_project(pid)
            manager.recheck_folders_and_params(pid, project, project_data=project_data)       
            app_logger.warning("Project %s was added early" % pid)
        except AttributeError, e:
            app_logger.error("ERROR: please, check that all settings given as dictionaries, not sets. (%s)" % e)
            raise Exception(e)
        except ProjectManagerException, e:
            manager.add_project(pid, project_data, init=True)
            app_logger.info("Project %s added" % pid)


def execute(args, usage, dataset_dict, exp_settings, exp_class, manager_class):
    ''' Execute experiment with givent args.
    '''
    if not len(args) in [5,7]:
        print usage
        sys.exit(0)
    command = args[0]
    tasks = args[1]
    start = int(args[2])
    end = int(args[3])
    dataset = args[4]
    settings_context = None
    project_context = None
    if len(args) > 5:
        settings_context = args[5]
        project_context = args[6]
    if not dataset in dataset_dict:
        print "Available datasets:", ", ".join(dataset_dict.keys())
        sys.exit(0)
    dataset = dataset_dict[dataset]
    commands = ["run","force","check"]
    if not  command.startswith("rw_"):
        if not command in commands:
            print "Available commands:", commands
            sys.exit(0)
    if command == "run":
        execute_task(dataset, 
                    tasks, 
                    start=start, 
                    end=end, 
                    exp_name="default", 
                    force=False,
                    exp_settings_class=exp_settings,
                    exp_class = exp_class,
                    manager_class = manager_class,
                    settings_context = settings_context,
                    project_context = project_context
                    )
    if command == "force":
        execute_task(dataset,
                    tasks, 
                    start=start, 
                    end=end, 
                    exp_name="default", 
                    force=True,
                    exp_settings_class=exp_settings,
                    exp_class = exp_class,
                    manager_class = manager_class,
                    settings_context = settings_context,
                    project_context = project_context                    
                    )
    if command == "check":
        check_task(dataset, 
                    tasks, 
                    start=start, 
                    end=end, 
                    exp_name="default", 
                    force=False,
                    exp_settings_class=exp_settings,
                    exp_class = exp_class,
                    manager_class = manager_class,
                    settings_context = settings_context,
                    project_context = project_context
                    )
    if command.startswith("rw"):
        commands = command.split("_")
        execute_task(dataset,
                    tasks, 
                    start=start, 
                    end=end, 
                    exp_name="default", 
                    force=True,
                    exp_settings_class=exp_settings,
                    exp_class = exp_class,
                    manager_class = manager_class,
                    settings_context = settings_context,
                    project_context = project_context,
                    path_replacing = commands,
                    )

def add_step(exp, task, manager, pid):
    ''' Add step to experiment.
    '''
    s = exp.find_step(task)
    input = None
    if not s:
        print "Unknown step name:", task
        print "Avaliable steps: " 
        for x in exp.get_avaliable_steps():
            print x["name"]
        sys.exit(0)
    if "manager" in s and s["manager"]:
            input = {"manager":manager, 
                     "pid":pid,
                     }
    check =None
    if "check" in  s:
        check = s["check"]
    pre =None
    if "pre" in  s:
        pre = s["pre"]
    if input:
        step = AbstractStep(s["name"], input, s["cf"], save_output=False, check_f=check, check_p=pre)
    else:
        step = AbstractStep(s["name"], None, s["cf"], save_output=False, check_f=check, check_p=pre)
    exp.add_step(step)
    
def execute_task(dataset_gen, 
                                    task, 
                                    start=None, 
                                    end=None, 
                                    exp_name="default", 
                                    force=None,
                                    exp_settings_class=None,
                                    exp_class = None,
                                    manager_class = None,
                                    settings_context = None,
                                    project_context = None,
                                    path_replacing= None,
                                    ):
    ''' Execute task.
    '''
    if not start is None and not end is None:
        dataset = dataset_gen()[start:end]
    else:
        dataset = dataset_gen()
    n = len(dataset)
    for i, (pid, project_init) in enumerate(dataset):
        print i, n, pid, task
        experiment_settings = exp_settings_class()
        manager = manager_class(experiment_settings)
        project, settings = manager.get_project(pid, settings_context=settings_context, project_context=project_context, path_replacing=path_replacing)
        exp = exp_class(settings, project, name=exp_name, manager=manager, force=force)
        if "," in task:
            print "Complex task"
            tasks = task.strip().split(",")
            for t in tasks:
                add_step(exp, t, manager, pid)
        else:
            print "Simple task"
            add_step(exp, task, manager, pid)
        exp.execute(project_context=project_context)
        print "\a"
    print "\a\a\a\a"

def check_task(dataset_gen, 
                                task, 
                                start=None, 
                                end=None, 
                                exp_name="default", 
                                force=None,
                                exp_settings_class=None,
                                exp_class = None,
                                manager_class = None
                                ):
    ''' Check given task.
    '''
    if not start is None and not end is None:
        dataset = dataset_gen()[start:end]
    else:
        dataset = dataset_gen()
    n = len(dataset)
    for i, (pid, project_init) in enumerate(dataset):
        print i, n, pid, task
        experiment_settings = exp_settings_class()
        manager = manager_class(experiment_settings)
        project, settings = manager.get_project(pid)
        exp = exp_class(settings, project, name=exp_name, manager=manager, force=force)
        if "," in task:
            print "Complex task"
            tasks = task.strip().split(",")
            for t in tasks:
                add_step(exp, t, manager, pid)
        else:
            print "Simple task"
            add_step(exp, task, manager, pid)
        exp.check_steps()
        print "\a"
    print "\a\a\a\a"

def run_app(exp_class, exp_settings_class, manager_class, dataset_dict):
    #TODO: add check command
    #TODO: add submit command
    usage = ("command task1,task2 from to dataset"
                      "\nOR\ncreate dataset"
                      "\nOR\nshow dataset"
                      "\nOR\ncheck dataset"
                      "\nOR\nyaml file_name"
                      "\nOR\nyaml generate file_name"
                      )

    args = sys.argv[1:]
    if len(args) == 2:
        if args[0] == "create":
            if args[1] in dataset_dict:
                all_projects = dataset_dict[args[1]]()
                _create_projects(exp_settings_class, manager_class, all_projects)
            else:
                print "Available datasets:", ", ".join(dataset_dict.keys())
                sys.exit(1)
        elif args[0] == "show":
            if args[1] in dataset_dict:
                all_projects = dataset_dict[args[1]]()
                for i, project in enumerate(all_projects):
                    print i, project
            else:
                print "Available datasets:", ", ".join(dataset_dict.keys())
                sys.exit(1)
        elif args[0] == "yaml":
            file_name = args[1]
            try:
                with open(file_name) as fh:
                    data = yaml.load(fh.read())
            except Exception, e:
                print e
                print "Can't read yaml file %s" % file_name
                sys.exit(1)
            try:
                if type(data["steps"]) is list:
                    data["steps"] = ",".join(data["steps"])
                if "data" in data:
                    dataset_items = [x[0] for x in dataset_dict[data["dataset"]]()]
                    if not data["data"] in dataset_items:
                        print "Wrong data parameter in yaml file."
                        print "Available values:", ",".join(dataset_items)
                        sys.exit(1)
                    data["start"] =  dataset_items.index(data["data"])
                    data["end"] = data["start"] + 1
                if not "settings_context" in data:
                    data["settings_context"] = None
                if not "project_context" in data:
                    data["project_context"] = None
                args = [
                    data["command"],
                    data["steps"],
                    data["start"],
                    data["end"],
                    data["dataset"],
                    data["settings_context"],
                    data["project_context"],
                ]
            except Exception, e:
                print e
                print "Necessary yaml fields: command (str), steps (list), start (int), end (int), dataset (str)"
                print "Optional fields: data (str), settings_context (dict), project_context (dict)"
                print "OR you may generate a yaml file with: 'yaml generate file_name' command"
                sys.exit(1)

            execute(args,
                usage, 
                dataset_dict, 
                exp_settings_class, 
                exp_class, 
                manager_class
            )
        else:
            print usage
            sys.exit(1)
    elif len(args) == 3:
     
        if args[0] == "yaml" and args[1]=="generate":
            file_name = args[2]
            data = {
                'command': 'force',
                'steps': ["a", "b"],
                'start': 0,
                'end': 1,
                'dataset': 'dataset',
                'data': None,
                'settings_context': None,
                'project_context': None,
                'avaliable_steps': exp_class(None, None).get_step_names(),
            }
            with open(file_name, "w") as fh:
                fh.write(yaml.dump(data))
    else:
        execute(args,
                usage, 
                dataset_dict, 
                exp_settings_class, 
                exp_class, 
                manager_class
        )