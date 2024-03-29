#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#@created: 05.06.2011
#@author: Aleksey Komissarov
#@contact: ad3002@gmail.com 
''' Code related to ProjectManager.
'''
import os
try:
    import yaml
except:
    print("Install pyyaml module")
import platform
try:
    from logbook import Logger
except:
    print("Install logbook module")


class ProjectManagerException(Exception):
    """ Simple exceptions class for project manager."""

    def __init__(self, value):
        self.value = value
    
    def __str__(self):
        return repr(self.value)


class ProjectManager(object):
    """ Class for controlling project's settings.
    A project is a collection of setting 
    for some data transformation.
    Each project is yaml file with settings. 
    Project PID is a yaml file name.
    """

    config_path = None

    def __init__(self, settings_class, config_path=None):
        """ Init projects_folder. 
        Manager loads settings from default location in PySatDNA root or from given config_path.
        Then create work and projects folders if they were not found.
        And set config values for settings class.
        """
        self.manager_logger = Logger('Manager logger')
        if config_path:
            self.load_config(config_path)
        else:
            self.load_config(self.config_path)
        self.projects_folder = self.config["projects_folder"]
        self.work_folder = self.config["path_work_folder"]
        self.settings_class = settings_class
        self.settings_class.config = self.config
        self.force_folder_creation = False
        if self.projects_folder and not os.path.isdir(self.projects_folder):
            os.makedirs(self.projects_folder)
        if self.work_folder and not os.path.isdir(self.work_folder):
            os.makedirs(self.work_folder)

    def load_config(self, config_path):
        ''' Load OS-specific configs.'''
        if config_path:
            file_path = config_path
            if not os.path.isfile(file_path):
                message = "ERROR with open config file: %s" % file_path
                self.manager_logger.error(message)
                raise ProjectManagerException(message)
        else:      
            self.os = platform.system()
            if self.os == "Windows":
                file_path = "../config.win.yaml"
            elif self.os == "Darwin":
                file_path = "../config.mac.yaml"
            else:
                file_path = os.path.expanduser("~/Dropbox/workspace/PySatDNA/config.yaml")
                if not os.path.isfile(file_path):
                    file_path = os.path.expanduser("~/Dropbox/PySatDNA/config.dobi.yaml")
        try:
            with open(file_path) as fh:
                self.config = yaml.load(fh)
        except Exception as e:
            self.manager_logger.error("ERROR with open config file: %s" % file_path)
            self.manager_logger.warning("Loading default settings")
            self.config = {
                'path_work_folder': 'data',
                'path_workspace_folder': '../..',
                'projects_folder': 'projects',
            }
            
    def add_project(self, pid, project_data, init=False, force=False, force_folder_creation=False):
        """ Add project to manager.
        Arguments:

        - *pid* project ID, usually with meta project prefix
        - *project_data* a dict with project initial settings
        - *init* true/false, default false.
        - *force* true/false, default false. remove existing yaml file.
        - *force_folder_creation* create or not all possible folders

        If the project exists then **ProjectManagerException** raised.
        """
        assert isinstance(project_data, dict)
        self.force_folder_creation = force_folder_creation
        if not "path_to" in project_data:
            self.manager_logger.error("Please add path_to parameter to project")
            raise ProjectManagerException("Please add path_to parameter to project")
        # check pid existence
        if force:
            try:
                self.remove_project(pid)
            except:
                    pass
        if self._check_pid(pid):
            raise ProjectManagerException("PID (%s) exists." % pid)
        project_data = self._init_project(project_data)
        project_data["status"] = {}
        if init:
            self._init_data(project_data)
        self.save(pid, project_data)

    def _check_pid(self, pid):
        """ Check project existance."""
        file_path = os.path.join(self.projects_folder, "%s.yaml" % pid)
        if os.path.isfile(file_path):
            return True
        self.manager_logger.error("Can't find %s" % file_path)
        return False

    def _init_project(self, project_data):
        """ Add initial data to project data dictionary."""
        return project_data

    def _init_data(self, project):
        """ Init project data."""
        project_folder = os.path.join(self.work_folder, project["path_to"])
        if not os.path.isdir(project_folder):
            self.manager_logger.info("Create folder %s" % project_folder)
            os.makedirs(project_folder)
        for folder_name, folder_path in self.settings_class.folders.items():
            folder = os.path.join(self.work_folder, project["path_to"], folder_path)
            if not os.path.isdir(folder) and self.force_folder_creation:
                self.manager_logger.info("Create folder %s" % folder)
                os.makedirs(folder)

    def _deepupdate(self, original, update):
        """
        Recursively update a dict.
        Subdict's won't be overwritten but also updated.
        From http://stackoverflow.com/a/8310229/385489
        """
        for key, value in original.iteritems(): 
            if not key in update:
                update[key] = value
            elif isinstance(value, dict):
                self._deepupdate(value, update[key]) 
        return update

    def save(self, pid, project_data):
        """ Save project data to yaml project file. 
        - load project
        - add absent fields from loaded project
        - save project

        """
        file_name = os.path.join(self.projects_folder, "%s.yaml" % pid)
        if os.path.isfile(file_name):
            with open(file_name, "r") as fh:
                old_project_data = yaml.load(fh)
            project_data = self._deepupdate(old_project_data, project_data)
        with open(file_name, "w") as fh:
            yaml.dump(project_data, fh, default_flow_style=False)

    def recheck_folders_and_params(self, pid, project, project_data=None):
        if not project_data:
            project_data = {}
        for key in project_data:
            if not key in project:
                print("\tadded", key)
                project[key] = project_data[key]
        self._init_data(project)
        self.save(pid, project)

    def get_project(self, pid, settings_context=None, project_context=None, path_replacing=None):
        """ Get project data by pid. You can change settings and project fields according to given contexts.
        """
        if not self._check_pid(pid):
            raise ProjectManagerException("PID (%s) doesn't exists." % pid)
        file_path = os.path.join(self.projects_folder, "%s.yaml" % pid)
        with open(file_path, "r") as fh:
            project_data = yaml.load(fh)
        if path_replacing:
            path_from = path_replacing[1]
            path_to = path_replacing[2]
            if "path_to" in project_data:
                project_data["path_to"] = project_data["path_to"].replace(path_from, path_to)
        settings = self._fix_paths(project_data)
        if settings_context:
            for k, v in settings_context.items():
                if type(v) is dict:
                    for k2 in v:
                        settings[k][k2] = v[k2]
                else:
                    settings[k] = v
        if project_context:
            for k, v in project_context.items():
                if type(v) is dict:
                    project_data.setdefault(k, {})
                    for k2 in v:
                        project_data[k][k2] = v[k2]
                else:
                    project_data[k] = v
        return project_data, settings

    def _fix_paths(self, project):
        """ Replace all project's paths with right one."""
        data = self.settings_class.as_dict()
        for folder_key, path_to in data["folders"].items():
            data["folders"][folder_key] = os.path.join(self.work_folder, project["path_to"], path_to)
        for file_key, path_to in data["files"].items():
            data["files"][file_key] = os.path.join(self.work_folder, project["path_to"], path_to)
        data["full_path_to"] = os.path.join(self.work_folder, project["path_to"])
        return data

    def get_all_projects(self):
        """ Get a list of avaliable projects."""
        result = []
        for root, dirs, files in os.walk(self.projects_folder, topdown=False):
            result.extend(files)
        return list(set(result))

    @staticmethod
    def get_id_by_pid(pid, dataset_dict):
        """ Get project id by pid."""
        for dataset in dataset_dict:
            for i, (_pid, project) in enumerate(dataset_dict[dataset]()):
                if _pid == pid:
                    return i, dataset 
        return None, None

    def remove_project(self, pid):
        """ Remove project."""
        if not self._check_pid(pid):
            raise ProjectManagerException("PID (%s) doesn't exists." % pid)
        file_path = os.path.join(self.projects_folder, "%s.yaml" % pid)
        os.remove(file_path)
