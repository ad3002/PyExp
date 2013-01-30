# PyExp: a tiny Python framework for experiment execution

Фреймоворк состоит из четырех частей:

- класс для описания моделей
- менеджер экспериментов
- собственно класс для описания экспериментов состоящих их последовательных шагов
- и класс облегчающий чтение данных

Данные для эксперимента состоят из двух частей:

- данные общие для всех проектов, которые будут выполнены в этом эксперименте. Это названия файлов и директорий. 
- данные собственно проекта

## Timer

При старте таймера, он печатате "Started: [step_name]...".
При окончание шага, он печатает "Finished: [step_name] elepase: [time]".

Usage:

	with Timer(name="Step name"):
		compute_smth(data)

## Класс описывающий шаг

Каждый шаг имеет следующие параметры:

- **name**, step name
- **data**, дополнительные данные для передаче в исполняющую функцию.
- **cf**, исполняющая функция
- **save_output** flag, default False
- **check_f**, функция, проверяющая статус этого шага после его выполнения, default None
- **check_p**, имя шага, который должен быть выполнен (иметь статус OK), на момент выполнения этого шага, default None

Инициация шага:

	step = AbstractStep("step_name", None, cf, save_output=False, check_f=check_f, check_p="previous_step")

	print step
	>>> step_name

	print step.get_as_dict().keys()
	>>> ['name', 'cf', 'check', 'pre', 'save_output']

## Настройки эксперимента

Инициация настроек эксперимента:

	settings = AbstractExperimentSettings()
	settings.as_dict().keys()
	>>> ['files', 'folders', 'other', 'config']

Для создания субкласса настроек нужно добавить словари files, folders, other.

## Класс эксперимента

### Аттрибуты эксеримента:

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

### Инициация эксперимента:

	project, settings = manager.get_project(pid)
	exp = AbstractExperiment(settings, project, name=None, force=False, logger=None, manager=None)

### Параметры инициации:

- **settings**, settings object
- **project**, project object
- **name**, experiment name, default is 'default'
- **logger**, function for logging, default None
- **force**, skip prerequisite checking for steps, default False
- **manager**, project manager object, default None

В процессе создания вызывается метод init_steps(self). Для инициации доступных шагов в субклассе должен быть создан метод init_steps(self). 

### Logger function example:

	logger_func(pid, exp_name, step_sid, step_name, status)

### Avaliable methods related to steps management:

- exp.add_step(step), добавленному шагу присваивается sid (step_id)
- exp.get_all_steps(), returns list of step objects
- exp.get_avaliable_steps(), returns registered steps
- exp.print_steps(), prints "Step [sid]: [string representation of step]" for each step
- exp.get_step(sid), returns step or None
- exp.find_step(step_name), returns step dict or None
- exp.find_steps_by_stage(stege), returns steps dict or None
- exp.remove_step(sid)
- exp.change_step(sid, new_step)
- exp.get_as_dict(), returns {'name':..., 'steps': [s.as_dict(),...]}

### Avalibale methods related to experiment exectution:

- exp.execute(start_sid=0, end_sid=None), see next section

## Порядок исполнение эксперимента:

Выполяются последовательно все добавленные шаги.Порядок выполнения шага следующий: 

1) обновление данных проекта из yaml file
2) if project data lacks "status" dictionary then it will be added
3) if status dictionary lacks step name then it will be added with None value
3) проверка пререквезитов
- если стоит флаг force, то нет проверки на выполненность текущего шага
- if status dictionary lacks prerequiste step name then it will be added with None value
- если предыдущий шаг не выполнен (status отличный от OK), то это шаг пропускается
- проверяется статус текущего шага и если он равен OK то шаг пропускается
4) если передан logger то отправляется сообщение о начале выполнения шага
5) выполнение шага внутри Timer class
6) если передан logger то отправляется сообщение о заверщение выполнения шага
7) если стоит флаг save_output, то результат шага сохраняется в словарь self.settings[step.name], или если результат словарь то в self.settings сохраняются пары ключ-значение.
8) происходит проверка статуса текущего шага с self.check_step(step)
9) После этого обновляются данные проекта.

### Methods related to step checking

 - exp.check_step(step), returns None or result of checking.
- exp.check_avalibale_steps(), check all  avaliable steps with exp.check_step(step) and update project
- exp.reset_avaliable_steps(), set all step's statuses to None

### Methods related to settings

- exp.clear_settings()
- exp.get_settings()
- exp.remove_project_data

### Methods related to experiment logging and server data:

- exp.logger_update_status(pid, step_name, status), upload step status to self.settings["config"]["url_status_update"]
- exp.logger_update_project(pid, project), save project data and upload project to self.settings"config"]["url_project_update"]
- exp.check_and_upload_project(), check all steps and upload project

## Описание менеджера экспериментов


Суть менеджера в управление настройками проектов, которые хранятся как yaml файлы.

::

	settings_class = AbstractExperimentSettings
	manager = ProjectManager(settings_class) 

Для инициации менеджер берет аргументом класс настроек эксперимента. При инициации менеджер пытается прочитать в родительской директории os specific yaml файл с настройками:

- config.win.yaml
- config.mac.yaml
- config.yaml (default and *nix)

Содержимое этого фала сохраняется в self.config. Если не удается прочитать файл, то создаются значения по умполчанию для self.congig:

::

	self.config = {
	                'path_work_folder': 'data',
	                'path_workspace_folder': '../..',
	                'projects_folder': 'projects',
	            }

После этого используя значения self.config, выставляются self.projects_folder (директория с yaml файлами проектов), self.work_folder (директория с данными проектов) и self.settings_class.config = self.config. Если директории отсутствуют, то они создаются.

Добавление проекта:

::

	pid = "name"
	projecy_data = {'path_to': 'path'}
	manager.add_proejct(pid, project_data, init=True, force=False)

Если force, то yaml файл проекта будет удален. Если не force и yaml файл был создан ранее, то вылетит исключение.
После этого происходит вызов self._init_project(...), который может быть переписан в субклассах для инитиации данных переданных с project_data.
Если init, то дополнительно происходит вызов _init_data(...), в котором происходит создание всех директорий согласно данным work_folder, path_to и folder_path из settings_class.folders.

Получение проекта.

::

	project, settings = manager.get_project(pid)

Project dictionary contains data from project's yaml file. Settings dictionary содержит данные из settings class с поправленными путями according to work_folder path and path_to path.

Получение списка путей к yaml файлам всех проктов:

::

	project_files = manager.get_all_projects()

Project removing:

::

	manager.remove_project(pid)

Projecy saving

::

	manager.save(pid, project_data)

Модель для хранение данных
--------------------------

::
	
	from PyExp.models.abstract_model import AbstractModel

Класс содержит следующие аттрибуты:

- dumpable_attributes, список всех аттрибутов
- int_attributes, список тех из них, которые типа int
- float_attributes, список тех из них, которые типа float
- list_attributes, список тех из них, которые типа list
- list_attributes_types, словарь типов для аттрибутов из list_attributes
- other_attributes, словарь других аттрибутов

При инициализации аттрибуты выставляются на None, 0 или 0.0.
Строковая репрезентация объекта - это tab-delimited string of dumpable attributes with \n end-symbol. При этом дополнительно вызывается model.preprocess_data() для преобразование данных.

Создание объекта:

::

	model = AbstractModel()
	model.set_with_dict(data_dict)
	model.set_with_list(data_list)

Модель можно получить как словарь:

::

	model_dict = model.get_as_dict()

Облегчение чтения данных
------------------------

Состоит из трех классов:

- AbstractFileIO()
- AbstractFolderIO()
- AbstractFoldersIO()

Работа с отдельным файлом
~~~~~~~~~~~~~~~~~~~~~~~~~

Avaliable attributes:

- data
- N

Avalibale methods:

- read_from_file(input_file), прочитанные данные хранятся в self.data.
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


Работа с директорией
~~~~~~~~~~~~~~~~~~~~

::

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

Работа со вложенными директориями
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Полезные shortcuts
~~~~~~~~~~~~~~~~~~

- sc_iter_filepath_folder(folder, mask="."), yield full path
- sc_iter_filename_folder(folder, mask="."), yield file name
- sc_iter_path_name_folder(folder, mask="."), yield (file name, full path)
- sc_iter_filedata_folder(folder, mask="."), yield data
- sc_move_files(folder, dist_folder, mask=".")
- sc_process_file(file_name, cf, args_dict)
- sc_process_folder(folder, cf, args_dict, mask=".")
- sc_process_folder_to_other(folder, output_folder, cf, args_dict, mask=".", verbose=False)
- read_pickle_file(pickle_file), get data

