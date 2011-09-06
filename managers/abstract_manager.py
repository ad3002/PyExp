#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#@created: 05.06.2011
#@author: Aleksey Komissarov
#@contact: ad3002@gmail.com 

import os
import yaml

class ProjectManagerException(Exception):
    """ Simple exceptions class for project manager."""
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return repr(self.value)

class ProjectManager(object):
    """
        Class for controlling project's settings.
        A project is a collection of setting 
        for some data transformation.
        Each project is yaml file with settings. 
        Project PID is a yaml file name.
        
        Public properties:
        self.projects_folder = "data"
        
        Public methods:
        __init__(self, projects_folder="data")
        add_project(self, pid, project_data, init=False)
        get_project(self, pid) -> project data
        get_all_projects(self) -> projects list
        remove_project(self, pid)
        save(self, pid, project_data)
        
        Private methods:
        _check_pid(self, pid) -> bool
        _init_project(self, project_data) -> project data
        _init_data(self, project)
        
        Exceptions:
        ProjectManagerException("PID (%s) doesn't exists." % pid)
        ProjectManagerException("PID (%s) exists." % pid)
        
    """

    def __init__(self, projects_folder="data"):
        """ Init projects_folder. """
        self.projects_folder = projects_folder
        if not os.path.isdir(self.projects_folder):
            os.makedirs(self.projects_folder)

    def add_project(self, pid, project_data, init=False):
        """ Add project to manager.
              
            Arguments:
            pid          -- project pid, 
                            usually with meta project prefix
            project_data -- a dict with project initial settings
            init         -- init data
        """
        # check pid existence
        if self._check_pid(pid):
            raise ProjectManagerException("PID (%s) exists." % pid)
        project_data = self._init_project(project_data)
        self.save(pid, project_data)

        if init:
            self._init_data(project_data)

    def _init_data(self, project):
        """ Init project data."""
        raise NotImplementedError

    def get_project(self, pid):
        """ Get project data by pid."""
        if not self._check_pid(pid):
            raise ProjectManagerException("PID (%s) doesn't exists." % pid)
        file_path = os.path.join(self.projects_folder, "%s.yaml" % pid)
        with open(file_path, "r") as fh:
            project_data = yaml.load(fh)
        return project_data

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

    def _check_pid(self, pid):
        """ Check project existance."""
        file_path = os.path.join(self.projects_folder, "%s.yaml" % pid)
        if os.path.isfile(file_path):
            return True
        return False

    def _init_project(self, project_data):
        """ Add initial data to project data dictionary."""
        return project_data

    def save(self, pid, project_data):
        """ Save project data to yaml project file. """
        file_name = os.path.join(self.projects_folder, "%s.yaml" % pid)
        with open(file_name, "w") as fh:
            yaml.dump(project_data, fh, default_flow_style=False)

