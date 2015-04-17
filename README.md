# PyExp: a microframework for small computational experiments

## Contents

- [Introduction](#_intro)
- [Timer class](#_timer)
- [Runner class](#_runner)
- [Step class](#_step)
- [Log wrapper](#_logger)
- [System command wrapper](#_runner)
- [Experiment settings class](#_exp_settings)
- [Experiment class](#_exp)
    - [Attributes](#_exp_attr)
    - [Creation](#_exp_create)
    - [Initiation](#_exp_init)
    - [Initiation parameters](#_exp_init_params)
    - [Logging](#_exp_logger)
    - [Steps managment](#_exp_steps)
    - [Execution](#_exp_exe)
    - [Steps checking](#_exp_check)
    - [Settings management](#_exp_settings)
- [Manager class](#_manager)
    - [Add project](#_manager_add_project)
    - [Get project](#_manager_get_project)
- [Data models](#_models)
- [IO helpers](#_readers)
    - [Working with gziped files](#_readers_archives)
    - [Working with files](#_readers_files)
    - [Working with folders](#_readers_folders)
    - [Working with nested folders](#_readers_folder_folders)
    - [Useful shortcuts](#_readers_shortcuts)
- [App functions](#_app)

<a name="_intro"/>
## Introduction

A data analysis workflow frequently consists of a sequence of steps applied to datasets. The purpose of PyExp is to simplify fast creation and execution of such workflows. There are many complex tools like Taverna or Galaxy but lack of tools for simple execution of series of data processing steps. PyExp uses YAML files for keeping data and experiments settings. A preferable way to keep datasets is a tab delimited files. Each workflow steps can be extended with precondition, postcondition and checking functions. Computation results can be submitted to external webserver or MongoDB database.

PyExp includes four compoments:

- A class for fast model description.
- A class for experiment managing.
- A class for workflow description as a sequence of steps.
- And a class for simplified data IO.
- A class for running command line tools.

The data for the experiment consists of two parts:

- Data common to all projects to be running in the given experiment. For example, names of files or directories
- The project-specific data.

<a name="_timer"/>
## Timer class

Timer class provides a wrapper for measuring execution time for a code fragment.

Usage:

```python
with Timer(name="Step name"):
    compute_something(data)

'''
>>> Started: [step_name]...
>>> Finished: [step_name] elapsed: [time]
'''
```

<a name="_runner"/>
## Process runner class

Runner class provides a wrapper for runnig command line tools one by one or in parallel.

Usage:

```python

from PyExp import runner

command = "ls"
commands = [
    "ls",
    "pwd",
]

runner.run(command, log_file=None, verbose=True)
# or with list of commands then it runs run_batch(...)
runner.run(commands)

runner.run_batch(commands)
```

Or you can run all commands in parallel:

```python

runner.run_parallel_no_output(commands, mock=False)
```

Or you can run all commands with queue in parallel:

```python

runner.run_asap(commands, cpu=10, mock=False)
```

If you need output from command then use popen:

```python

output, error = runner.popen(command, silent=False)
```

<a name="_step"/>
## Class for step descripion

Every step has following properties:

- **name**, step name
- **data**, additional data for a function.
- **cf**, a function
- **save_output** flag, default False
- **check_f**, function that check status of the step after execution, default is None
- **check_p**, name of step that should be successfully executed (**it should returns None or error text**) before this step, default is None
- **check_value**, output value from the step that will be checked with check_p

Step initiation:

```python

def cf(*arguments, **keywords):
	pass

def chech_f(*arguments, **keywords):
	return "OK"

step = AbstractStep("step_name", None, cf, save_output=False, check_f=check_f, check_p="previous_step")

print step
>>> step_name

print step.get_as_dict().keys()
>>> ['name', 'cf', 'check', 'pre', 'save_output']
# or 
print step.as_dict()
```

<a name="_logger"/>
## Log wrapper

There are several loggers for various parts of experiment running:

```python
timer_logger = Logger('timer logger')
exp_logger = Logger('exp logger')
core_logger = Logger('core logger')
runner_logger = Logger('run logger')
trseeker_logger = Logger('trseeker')
```

<a name="_exp_settings"/>
## Experiment settings

Settings initiation:

```python
settings = AbstractExperimentSettings()
settings.as_dict().keys()
>>> ['files', 'folders', 'other', 'config']
# or
print settings.get_as_dict()
```

Each subclass of AbstractExperimentSettings must have three dictionaries (files, folders, other) that keep project's filenames, foldernames, and other parameters needed for workflow execution.

<a name="_exp"/>
## Class for experiment description

<a name="_exp_attr"/>
### Experiments attributes:

- **settings**, settings dictionary
- **project**, project dictionary
- **name**, experiment name, default 'default', can be changed with kwargs['name']
- **logger**, function for logging, default self.default_logger, can be changed with kwargs['logger']
- **force**, skip prerequisite checking for steps, default False, can be changed with kwargs['force']
- **manager**, project manager object, default None, can be changed with kwargs['manager']
- **send_to_server**, communicate with server during execution, default None, can be changed with kwargs['send_to_server']
- **sp**, number of added steps
- **pid**, current project pid
- **sid2step**, sid to step dictionary
- **all_steps**, steps dictionary
- **settings["manager"]**, a link to manager instance
- **settings["experiment"]**, a link to experiment instance

<a name="_exp_create"/>
### How to create a new experiment 

To create an experiment you should add self.all_steps list with step dictionaries in self.init_steps() method.

```python
class AnnotationExperiment(AbstractExperiment):
    ''' Assembly annotation.
    '''
    def init_steps(self):
        ''' Add avaliable steps.'''

        self.all_steps = [
            ## Reports
            {
                'pre': None,
                'stage': "Reports",
                'name': "report_raw",
                'cf': report_raw_data_statistics,
                'check': None,
                'desc': 'report',
            },
            ## Data preparation
            {
                'pre': None,
                'stage': "Preprocessing",
                'name': "fastqc_raw",
                'cf': cf_create_fastqc_reports_for_raw_reads,
                'check': None,
                'desc': 'Fastqc for raw files.',
            },
        ]
```

Also you should create ExperimantSettings class and ProjectManager classes:

```python
class ExperimentSettings(AbstractExperimentSettings):
    ''' ExperimentSettings class.
    '''
    def __init__(self):
      super(ExperimentSettings, self).__init__()

      self.folders = {...}
      self.files = {...}
      self.other = {...}

class SomeProjectManager(ProjectManager):
    """ Class for projects about something.
    """
    
    def _init_project(self, project_data):
        """Add initial data to project data dictionary."""

        mandatory_params = ["path_to",
                            "pid",
                            ]

        project = {}
        for param in mandatory_params:
            if not param in project_data:
                raise ProjectManagerException("Add '%s' parameter to project data" % param)
            setattr(self, param, project_data[param])
            project[param] = project_data[param]
        for key in project_data:
            project[key] = project_data[key]
        return project
```


<a name="_exp_init"/>
### Experiment initiation:

```python

pid = "some_pid"

manager = SomeProjectManager()

project, settings = manager.get_project(pid)

exp = AbstractExperiment(settings, project, name=None, force=False, logger=None, manager=manager, send_to_server=None)
```

Or you can use run_app function (see below):

```python
exp_settings_class = ExperimentSettings
exp_class = AnnotationExperiment
manager_class = SomeProjectManager 

dataset_dicts = {...}

run_app(exp_class, exp_settings_class, manager_class, dataset_dicts)
```

<a name="_exp_init_params"/>
### Parameters of initiation:

- **settings**, settings object
- **project**, project object
- **name**, experiment name, default is 'default'
- **logger**, function for logging, default None
- **force**, skip prerequisite checking for steps, default False
- **manager**, project manager object, default None
- **send_to_server**, communicate with server during execution, default None

To initiate available step you must add to subclass init_steps() method with list of steps.

<a name="_exp_steps"/>
### Avaliable methods related to steps management:

- exp.add_step(step), add step with assigned sid (step_id)
- exp.get_all_steps(), returns list of step objects
- exp.get_available_steps(), returns registered steps
- exp.print_steps(), prints "Step [sid]: [string representation of step]" for each step
- exp.get_step(sid), returns step or None
- exp.find_step(step_name), returns step dict or None
- exp.find_steps_by_stage(stege), returns steps dict or None
- exp.remove_step(sid)
- exp.change_step(sid, new_step)
- exp.get_as_dict(), returns {'name':..., 'steps': [s.as_dict(),...]}

<a name="_exp_exe"/>
### Experiment execution order:

```python
exp.execute(start_sid=0, end_sid=None, project_context=None)
```

An experiment class executes each added steps with following logic:

1. Refresh project and settings from yaml file with manager instance using given project_context.
2. If project data lacks "status" dictionary then it will be added.
3. If status dictionary lacks step name then it will be added with None value
4. Check preconditions:
    - if force flag is true, then skip precondition check (go to 5)
    - if step contains step.check_value and it is equal to self.project["status"][step.name] then the current step will be skipped (go to 1)
5. If there is a logger function, then send a message about step start
6. Execute step wrapped in Timer class
    - if step.check_p is defined and it's a function then run it. If step.check_p returns something then stop step execution, save result in self.project["status"][step.name] (go to 1)
    - if step.input is None them simply run step.cf(self.settings, self.project)
    - else there are some value in step.input then add it to step.cf as the last argument
7. If there is a logger function, then send a message about step finishing
8. If flag save_output is true, then save step return to self.settings[step.name], if step returned a dictionaly then save key, values pairs into self.settings dictionary.
9. Check current step status with self.check_step(step, cf_results) method.
10. Update project including saving project data to yaml file.


<a name="_exp_check"/>
### Methods related to step checking

There is an additional verification with step.check_f function if it is provided for the step, otherwise step returns value will be saved in project["status"][step.name] variable, step.check_f should be usual core function that takes settings, project arguments and returns some value that be saved in project["status"][step.name] variable. After each step check logger_update_project is called, so you can update server value with it if send_to_server is True.

Check step and returns None or result of checking:

```python
exe_result = None
exp.check_step(step, exe_result)
```

Check **ALL** available steps with exp.check_step(step) and update project:

```python
exp.check_avalibale_steps()
```

Set all step's statuses to None:

```python
exp.reset_avaliable_steps()
```

Check **only** added steps:

```python
exp.check_steps()
```

<a name="_exp_settings"/>
### Methods related to settings

- exp.clear_settings(), set settings to None
- exp.get_settings()
- exp.remove_project_data, remove all project's files and folders listed in settings

<a name="_exp_logger"/>
### About logging

A Custom logger function interface, default logger funciton send data to self.settings["config"]["url_exe_update"] url.

```python
logger_func(pid, exp_name, step_sid, step_name, status)
```

Upload step status to self.settings["config"]["url_status_update"]:

```python
exp.logger_update_status(pid, step_name, status)
```

Save project data and upload project to self.settings"config"]["url_project_update"]:

```python
exp.logger_update_project(pid, project)
# or
exe.logger_send_project(pid, project)
```

Check all steps and upload project:

```python
exp.check_and_upload_project()
```

Simple function for uploading anything with POST request:
```python
exp.upload_to_server(url, data)
```

Inner logic for uploading:
- if self.send_to_server is None then skip uploading
- if self._skip_server_part then skip uploading
- try three times upload to server with forth fail set elf._skip_server_part to True.

<a name="_manager"/>
## Experiment manager

An expeirment manager provides project settings persistence using yaml files:

```python
settings_class = AbstractExperimentSettings
manager = ProjectManager(settings_class, config_path=None) 
```

Config file contains:

```python
path_work_folder: /home/username/data
path_workspace_folder: /home/username/Dropbox
projects_folder: /home/username/managers/wgs
url_status_update: http://localhost:3015/api/update/project/status
url_ext_update: http://localhost:3015/api/update/project/exe
url_project_update: http://localhost:3015/api/add/project
url_experiment_update: http://localhost:3015/api/add/experiment
```

If not config_path is not provided then upon initiation the manager is trying to read OS specific yaml configuration file in the parent directory:

- config.win.yaml
- config.mac.yaml
- config.yaml (default and *nix)

Then it save settings from this file in self.config property. If the manager fails find settings file then it creates deffult self.config:

```python
self.config = {
                'path_work_folder': 'data',
                'path_workspace_folder': '../..',
                'projects_folder': 'projects',
            }
```

Using settings from self.config it sets self.projects_folder (folder with project yaml files), self.work_folder (folder with project data), and self.settings_class.config = self.config.

<a name="_manager_add_project"/>
### Project adding

```python
pid = "name"
projecy_data = {'path_to': 'path'}
manager.add_project(pid, project_data, init=False, force=False)
```

With force flag project yaml file will be deleted, otherwise if a yaml file exists then the manager raise exception. After project adding the manager calls  self._init_project(...) which can be changed in subclasses for data initiation with project_data settings. 
With init flag it additinally calls sekf._init_data(...) which create all folders according to work_folder, path_to, and folder_path settings from settings_class.folders.

Also you can recheck parameters and create folders with:

```
manager.recheck_folders_and_params(pid, project_data)
```

<a name="_manager_get_project"/>
### Access to project data

```python
project, settings = manager.get_project(pid)
```

A project dictionary contains data from project's yaml file. A settings dictionary contains data from settings class with correct paths according to work_folder path and path_to path.

Or reverse:

```python
id = get_id_by_pid(pid, dataset_dict):
```

### Access to all project yaml files

```python
project_files = manager.get_all_projects()
```

### Project removing:

```python
manager.remove_project(pid)
```

<a name="_models"/>
## Data model

```python
from PyExp.models.abstract_model import AbstractModel
```

Class attributes:

- dumpable_attributes, a list of all attributes
- int_attributes, a list of int type attributes
- float_attributes, a list of float type attributes
- list_attributes, a list of list type attributes
- list_attributes_types, a dictionay of list attributes types
- other_attributes, a list of other types attributes

While initialisation each attribute is set to default values (0, 0.0, or None for list attributes).

A string representation of object is a tab-delimited string of dumpable attributes (preprocessed with self.preprocess_data() method) with \n end-symbol.

### Creation:

```python
model = AbstractModel()
model.set_with_dict(data_dict)
model.set_with_list(data_list)
```

You can get model data as dictionary:

```python
model_dict = model.get_as_dict()
# or
model_dict = model.as_dict()
```

Or as human friendly:

```python
model.print_human_friendly()
```

In JSON format with optional preprosessing by preprocess_func:

```python
model_json = model.get_as_json(preprocess_func=None)
```

Model has preprocess_data method for any data preprocessing until returning. It can be implemented in nested classes.

In model defined __setitem__ and __getitem__ so you can access them both as dictinary and as object attributes.

<a name="_readers"/>
## IO simplification classes 

Includes three classes:

- AbstractFileIO()
- AbstractFolderIO()
- AbstractFoldersIO()

<a name="_readers_archives"/>

<a name="_readers_files"/>
### Working with files

Avaliable attributes:

- data
- N

Avalibale methods:

- read_from_file(input_file), data is saved in self.data.
- read_online(input_file), yield line
- read_from_db(db_cursor), yield item
- read_from_mongodb(table, query), yield item
- updata_mongodb(table, what, wherewith)
- write_to_file(output_file)
- write_to_db(db_cursor)
- write_to_mongodb(db_cursor)
- read_as_iter(source)
- iterate(skip_empty=True), iterate over data
- iterate_with_func(pre_func, iter_func)
- do(cf, **args), get result after cf(data, **args)
- process(cf, **args)
- clear(self)
- do_with_iter(self, cf, **args) -> [result,]
- process_with_iter(cf, **args)
- clear()
- do_with_iter(cf, **args), ger list of results after cf(data[i], **args)
- process_with_iter(cf, **args)
- sort(sort_func, reverse=True)

<a name="_readers_folders"/>
### Working with folders

	reader = AbstractFolderIO(folder, mask=".")

- iter_files(), yield file name
- get_files(), return list of file names
- iter_filenames(), yield file path
- get_filenames(), return list of file paths
- iter_path_names(), yield (name, full path)
- iter_file_content(), yield file content
- iter_file_content_and_names(), yield (data, name, full_path)
- move_files_by_mask(dist_folder)
- copy_files_by_mask(dist_folder)

<a name="_readers_folder_folders"/>
### Working with nested folders

<a name="_readers_shortcuts"/>
### Useful shortcuts

```python
from PyExp.readers.abstract_reader import *
```

- sc_iter_filepath_folder(folder, mask="."), yield full path
- sc_iter_filename_folder(folder, mask="."), yield file name
- sc_iter_path_name_folder(folder, mask="."), yield (file name, full path)
- sc_iter_filedata_folder(folder, mask="."), yield data
- sc_move_files(folder, dist_folder, mask=".")
- sc_process_file(file_name, cf, args_dict)
- sc_process_folder(folder, cf, args_dict, mask=".")
- sc_process_folder_to_other(folder, output_folder, cf, args_dict, mask=".", verbose=False)
- read_pickle_file(pickle_file), get data

<a name="_app"/>
## App functions

To run experiment execution you can use:
```python
from PyExp import run_app

run_app(exp_class, exp_settings_class, manager_class, dataset_dict)
```

### Available scenaries:

Create and init all projects from dataset:

```bash
python experiment.py create dataset_name
```

Show available projects in dataset:

```bash
python experiment.py show dataset_name
```

Run with custom yaml script:

```bash
python experiment.py yaml yaml_path
```

Yaml content:

```yaml
command: force
steps:
  - step1
  - step2
  - step3
start: 0
end: 2
dataset: dataset_name
settings_context: <dict>
project_context: <dict>
```

Your can generate yaml:

```bash
python experiment.py yaml generate yaml_file
```

Usual usage
```bash
python experiment.py run step dataset_name
# or
python experiment.py check step dataset_name
# or
python experiment.py force step dataset_name
```

Or you can execute for project slice from dataset:

```bash
# check ids
python experiment.py show dataset_name
# and then
python experiment.py force step1 2 6 dataset_name
```

