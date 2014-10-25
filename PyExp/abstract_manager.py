#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#@created: 05.06.2011
#@author: Aleksey Komissarov
#@contact: ad3002@gmail.com 

import os
import yaml
import platform

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

    def __init__(self, settings_class):
        """ Init projects_folder. """
        self.load_config()
        self.projects_folder = self.config["projects_folder"]
        self.work_folder = self.config["path_work_folder"]
        self.settings_class = settings_class
        self.settings_class.config = self.config
        if self.projects_folder and not os.path.isdir(self.projects_folder):
            os.makedirs(self.projects_folder)
        if self.work_folder and not os.path.isdir(self.work_folder):
            os.makedirs(self.work_folder)

    def load_config(self):
        ''' Load OS-specific configs.'''
        self.os = platform.system()
        if self.os == "Windows":
            file_path = "../config.win.yaml"
        elif self.os == "Darwin":
            file_path = "../config.mac.yaml"
        else:
            file_path = os.path.join("/root/Dropbox/workspace/PySatDNA", "config.yaml")
            if not os.path.isfile(file_path):
                file_path = os.path.expanduser("~/Dropbox/PySatDNA/config.dobi.yaml")
        try:
            with open(file_path) as fh:
                self.config = yaml.load(fh)
        except Exception, e:
            print "ERROR: Check settings,", e
            print "Loading default settings"
            self.config = {
                'path_work_folder': 'data',
                'path_workspace_folder': '../..',
                'projects_folder': 'projects',
            }
            
    def add_project(self, pid, project_data, init=False, force=False):
        """ Add project to manager.
              
        Arguments:

        - *pid* project ID, usually with meta project prefix
        - *project_data* a dict with project initial settings
        - *init* true/false, default false.

        If the project exists then **ProjectManagerException** raised.
        """
        assert isinstance(project_data, dict)
        self.force_folder_creation = force_folder_creation
        if not "path_to" in project_data:
            print "Please add path_to parameter to project"
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

    def recheck_folders_and_params(self, pid, project, project_data=None):
        if not project_data:
            project_data = {}
        for key in project_data:
            if not key in project:
                print "\tadded", key
                project[key] = project_data[key]
        self._init_data(project)
        self.save(pid, project)

    def _init_project(self, project_data):
        """ Add initial data to project data dictionary."""
        return project_data

    def _init_data(self, project):
        """ Init project data."""
        project_folder = os.path.join(self.work_folder, project["path_to"])
        if not os.path.isdir(project_folder):
            manager_logger.info("Create folder %s" % project_folder)
            os.makedirs(project_folder)
        for folder_name, folder_path in self.settings_class.folders.items():
            folder = os.path.join(self.work_folder, project["path_to"], folder_path)
            if not os.path.isdir(folder):
                print "Create folder %s ..." % folder
                os.makedirs(folder)

    def _check_pid(self, pid):
        """ Check project existance."""
        file_path = os.path.join(self.projects_folder, "%s.yaml" % pid)
        if os.path.isfile(file_path):
            return True
        print "Can't find %s" % file_path
        return False

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

    def remove_project(self, pid):
        """ Remove project."""
        if not self._check_pid(pid):
            raise ProjectManagerException("PID (%s) doesn't exists." % pid)
        file_path = os.path.join(self.projects_folder, "%s.yaml" % pid)
        os.remove(file_path)

    def save(self, pid, project_data):
        """ Save project data to yaml project file. """
        file_name = os.path.join(self.projects_folder, "%s.yaml" % pid)
        with open(file_name, "w") as fh:
            yaml.dump(project_data, fh, default_flow_style=False)


