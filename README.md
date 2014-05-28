# PyExp: a microframework for small computational experiments

## Contents

- [Introduction](#_intro)
- [Timer class](#_timer)
- [Step class](#_step)
- [Experiment settings class](#_exp_settings)
- [Experiment class](#_exp)
    - [Attributes](#_exp_attr)
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
    - [Working with files](#_readers_files)
    - [Working with folders](#_readers_folders)
    - [Working with nested folders](#_readers_folder_folders)
    - [Useful shortcuts](#_readers_shortcuts)

<a name="_intro"/>
## Introduction

A data analysis workflow frequently consists of a sequence of steps applied to datasets. The purpose of TinyExp simplify fast creation and execution of such workflows. There are many complex tools like Taverna or Galaxy but lack of tolls for simple execution of series of data processing steps. TinyExp uses YAML files for keeping data and experiments settings. A preferable way to keep datasets is a tab delimited files. Each workflow steps can be extended with precondition, postcondition and checking functions. Execution status can be submitted to external webserver.

TinyExp includes four compoments:

- A class for fast model description.
- A class for experiment manager.
- A class for workflow description as a sequence of steps.
- And a class for simplified data IO.

The data for the experiment consists of two parts:

- Data common to all projects to be implemented in this experiment. For example, names of files or directories
- The project data.

<a name="_timer"/>
## Timer class

This class provides a wrapper for measure time of execution.

Usage:

```python
with Timer(name="Step name"):
    compute_something(data)

'''
>>> Started: [step_name]...
>>> Finished: [step_name] elapsed: [time]
'''
```

<a name="_step"/>
## Class for step descripion

Every step has following properties:

- **name**, step name
- **data**, additional data for a function.
- **cf**, a function
- **save_output** flag, default False
- **check_f**, function that check status of the step after execution, default is None
- **check_p**, name of step that cab be successfully executed (it has status OK) before this step, default is None

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
```

<a name="_exp_settings"/>
## Experiment settings

Settings initiation:

```python
settings = AbstractExperimentSettings()
settings.as_dict().keys()
>>> ['files', 'folders', 'other', 'config']
```

Each subclass of AbstractExperimentSettings must have three dictionaries (files, folders, other) that keepproject's filenames, foldernames, and other parameters needed for workflow execution.

<a name="_exp"/>
## Class for experiment description

<a name="_exp_attr"/>
### Experiments attributes:

- **settings**, settings object
- **project**, project object
- **name**, experiment name, default None
- **logger**, function for logging, default None
- **force**, skip prerequisite checking for steps, default False
- **manager**, project manager object, default None
- **sp**, number of added steps
- **pid**, current project pid
- **all_steps**, steps dictionary
- **sid2step**, sid to step dictionary

<a name="_exp_init"/>
### Experiment initiation:

```python
project, settings = manager.get_project(pid)
exp = AbstractExperiment(settings, project, name=None, force=False, logger=None, manager=None)
```

<a name="_exp_init_params"/>
### Parameters of initiation:

- **settings**, settings object
- **project**, project object
- **name**, experiment name, default is 'default'
- **logger**, function for logging, default None
- **force**, skip prerequisite checking for steps, default False
- **manager**, project manager object, default None

To initiate available step you must add to subclass init_steps() method with list of steps.

<a name="_exp_logger"/>
### Logger function example:

	logger_func(pid, exp_name, step_sid, step_name, status)

Upload step status to self.settings["config"]["url_status_update"]:

	exp.logger_update_status(pid, step_name, status)
	
Save project data and upload project to self.settings"config"]["url_project_update"]:

	exp.logger_update_project(pid, project)
	
Check all steps and upload project:

	exp.check_and_upload_project()

<a name="_exp_steps"/>
### Avaliable methods related to steps management:

- exp.add_step(step), add step with assigned sid (step_id)
- exp.get_all_steps(), returns list of step objects
- exp.get_avaliable_steps(), returns registered steps
- exp.print_steps(), prints "Step [sid]: [string representation of step]" for each step
- exp.get_step(sid), returns step or None
- exp.find_step(step_name), returns step dict or None
- exp.find_steps_by_stage(stege), returns steps dict or None
- exp.remove_step(sid)
- exp.change_step(sid, new_step)
- exp.get_as_dict(), returns {'name':..., 'steps': [s.as_dict(),...]}

<a name="_exp_exe"/>
### Experiment executin order:

```python
exp.execute(start_sid=0, end_sid=None)
```

An experiment class executes each added steps with following logic:

1. Refresh project settings from yaml file.
2. If project data lacks "status" dictionary then it will be added.
3. If status dictionary lacks step name then it will be added with None value
4. Check preconditions:
	- if force flag is true, then skip current step step status
	- if status dictionary lacks prerequiste step name then it will be added with None value
	- if previous step is not executed (status different from OK), then skip this step
	- check current step status, if this step was previously executed then skip it
5. If there is a logger function, then send a message about step start
6. Execute step wrapped in Timer class
7. If there is a logger function, then send a message about step finishing
8. If flag save_output is true, then save step return to self.settings[step.name], if step returned a dictionaly then save key, values pairs into self.settings dictionary.
9. Check current step status with self.check_step(step) method.
10. Save project to yaml file.

<a name="_exp_check"/>
### Methods related to step checking

Check step and returns None or result of checking:

```python
exp.check_step(step)
```

Check all  avaliable steps with exp.check_step(step) and update project:

```python
exp.check_avalibale_steps()
```

Set all step's statuses to None:

```python
exp.reset_avaliable_steps()
```

Check added steps:

```python
exp.check_steps()
```

<a name="_exp_settings"/>
### Methods related to settings

- exp.clear_settings()
- exp.get_settings()
- exp.remove_project_data

<a name="_manager"/>
## Experiment manager

An expeirment manager provide project settings persistence using yaml files:

```python
settings_class = AbstractExperimentSettings
manager = ProjectManager(settings_class) 
```

Upon initiation the manager is trying to read OS specific yaml configuration file in the parent directory:

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
manager.add_proejct(pid, project_data, init=False, force=False)
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

### Access to all project yaml files

```python
project_files = manager.get_all_projects()
```

### Project removing:

```python
manager.remove_project(pid)
```

### Project saving

```python
manager.save(pid, project_data)
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
```

In JSON format with optional preprosessing by preprocess_func:

```python
model_json = model.get_as_json(preprocess_func=None)
```

Model has preprocess_data method for any data preprocessing until returning. It can be implemented in nested classes.

<a name="_readers"/>
## IO simplification classes 

Includes three classes:

- AbstractFileIO()
- AbstractFolderIO()
- AbstractFoldersIO()

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