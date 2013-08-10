import sys
import shutil
from abstract_experiment import AbstractStep

def _create_projects(exp_settings_class, manager_class, all_projects):
    ''' Init project data and settings.
    '''    
    for pid, project_data in all_projects:
        experiment_settings = exp_settings_class()
        manager = manager_class(experiment_settings)
        try:
            project, settings = manager.get_project(pid)
            manager.recheck_folders_and_params(pid, project)       
            print "Project %s was added early" % pid
        except:
            manager.add_project(pid, project_data, init=True)
            print "Project %s added" % pid

def execute(args, usage, dataset_dict, exp_settings, exp_class, manager_class):
    ''' Execute experiment with givent args.
    '''
    if not len(args) == 5:
        print usage
        exit(0)
    command = args[0]
    tasks = args[1]
    start = int(args[2])
    end = int(args[3])
    dataset = args[4]
    if not dataset in dataset_dict:
        print "Available datasets:", ", ".join(dataset_dict.keys())
        exit(0)
    dataset = dataset_dict[dataset]
    commands = ["run","force","check"]
    if not command in commands:
        print "Available commands:", commands
        exit(0)
    if command == "run":
        execute_task(dataset, 
                    tasks, 
                    start=start, 
                    end=end, 
                    exp_name="default", 
                    force=False,
                    exp_settings_class=exp_settings,
                    exp_class = exp_class,
                    manager_class = manager_class
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
                    manager_class = manager_class
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
                    manager_class = manager_class
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
        exit(0)
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
                                    manager_class = None
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
        exp.execute()
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
                      )

    args = sys.argv[1:]
    if len(args) == 2:
        if args[0] == "create":
            if args[1] in dataset_dict:
                all_projects = dataset_dict[args[1]]()
                _create_projects(exp_settings_class, manager_class, all_projects)
            else:
                print "Available datasets:", ", ".join(dataset_dict.keys())
                exit(1)
        elif args[0] == "show":
            if args[1] in dataset_dict:
                all_projects = dataset_dict[args[1]]()
                for i, project in enumerate(all_projects):
                    print i, project
            else:
                print "Available datasets:", ", ".join(dataset_dict.keys())
                exit(1)
        else:
            print usage
            exit(1)
    else:
        execute(args,
                usage, 
                dataset_dict, 
                exp_settings_class, 
                exp_class, 
                manager_class
        )