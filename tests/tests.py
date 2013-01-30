import sys, os
sys.path.append("/Users/ad3002/Dropbox/workspace")
sys.path.append("c:/Users/Master/Dropbox/workspace")

import unittest
from PyExp.experiments.abstract_experiment import AbstractStep
from PyExp.experiments.abstract_experiment import AbstractExperimentSettings
from PyExp.experiments.abstract_experiment import AbstractExperiment
from PyExp.managers.abstract_manager import ProjectManager, ProjectManagerException

STEPS = [
            {
                'stage': "Test Stage A",
                'name': "step_a",
                'cf': sum,
                'check': sum,
                'data': None,
                'pre': None,
            },
            {
                'stage': "Test Stage A",
                'name': "step_b",
                'cf': lambda x: x**2,
                'check': lambda x: x**2,
                'data': None,
                'pre': "step_a"
            },
            {
                'stage': "Test Stage B",
                'name': "step_c",
                'cf': lambda x: x+1,
                'check': {"a":1, "b":2},
                'data': "manager",
                'pre': "step_b"
            },
            {
                'stage': "Test Stage B",
                'name': "step_d",
                'cf': lambda x: x,
                'data': [1,2,3],
                'check': lambda x: x,
                'pre': "step_c"
            },
        ]

class TestExperiment(AbstractExperiment):
    def init_steps(self):
        self.all_steps = STEPS

class TestExperimentSettings(AbstractExperimentSettings):
    def __init__(self ):
        self.folders = {
            "test_folder":"test/folder",
        }
        self.files = {
            "test_file":"test.txt",
        }
        self.other = {
            "test_other":"test",
        }

class ProjectManagerTest(unittest.TestCase):

    def setUp(self):
        pass

    def test_step_initiation(self):
        settings = TestExperimentSettings()
        manager = ProjectManager(settings)
        self.assertTrue(isinstance(manager.config, dict))
        self.assertEqual(manager.projects_folder, "projects")
        self.assertEqual(manager.work_folder, "data")

    def test_project_adding(self):
        pid = "test_project"
        data = {
            "data":"data",
            "foo":"bar",
            "path_to": "data/test_data",
            "pid": "test_project",
        }
        experiment_settings = TestExperimentSettings()
        manager = ProjectManager(experiment_settings)
        manager.add_project(pid, data, init=True, force=True)
        self.assertTrue(os.path.isfile("projects/test_project.yaml")) 
        self.assertTrue(os.path.isdir("data/data/test_data/test/folder")) 
        self.assertRaises(ProjectManagerException, manager.add_project, pid, data, init=True)
        data = {
            "data":"data",
            "foo":"bar",
        }
        self.assertRaises(ProjectManagerException, manager.add_project, pid, data, init=True)
        data = {
            "data":"data",
            "foo":"bar",
            "path_to": "data/test_data",
            "pid": "test_project",
        }
        manager.add_project(pid, data, init=True, force=True)
        self.assertEqual(manager.get_all_projects(), ['test_project.yaml'])

    def test_get_project(self):
        pid = "test_project"
        data = {
            "data":"data",
            "foo":"bar",
            "path_to": "data/test_data",
            "pid": "test_project",
        }
        experiment_settings = TestExperimentSettings()
        manager = ProjectManager(experiment_settings)
        project, settings = manager.get_project(pid)
        self.assertEqual(settings["full_path_to"].count("data"), 3)
        self.assertEqual(settings["files"]["test_file"].count("data"), 3)
        self.assertEqual(settings["files"]["test_file"].count("test.txt"), 1)

class AbstractStepTest(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_step_initiation(self):
        name = "name"
        data = [1,2,3]
        cf = sum
        step = AbstractStep(name, data, cf)
        self.assertEqual(step.name, name)
        self.assertEqual(step.sid, None)
        self.assertEqual(step.input, data)
        self.assertEqual(step.cf, cf)
        self.assertEqual(str(step.name), name)
        dict_repr = {
            'name':name,
            'cf':cf,
            'pre':None,
            'check':None,
            'save_output':False,
        }
        self.assertEqual(step.get_as_dict(), dict_repr)
        f = lambda x: True
        step = AbstractStep(name, data, cf, 
            save_output=True, 
            check_f=f, 
            check_p="step0")
        dict_repr = {
            'name':name,
            'cf':cf,
            'check':f,
            'pre':"step0",
            'save_output':True,
        }
        self.assertEqual(step.get_as_dict(), dict_repr)

class AbstractExperimentSettingsTest(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_initiation(self):
        settings1 = AbstractExperimentSettings()
        settings2 = AbstractExperimentSettings()
        self.assertEqual(settings1.folders, {})
        self.assertEqual(settings1.files, {})
        self.assertEqual(settings1.other, {})
        settings2.folders["test"] = "test"
        self.assertEqual(settings1.files, {})
        self.assertEqual(settings1.as_dict(), {
            "files":{},
            "folders":{},
            "other":{},
            "config":{},
            })
        self.assertEqual(settings2.as_dict(), {
            "files":{},
            "folders":{"test":"test"},
            "other":{},
            "config":{},
            })

class AbstractExperimentTest(unittest.TestCase):
    
    def setUp(self):
        pass

    def test_initiation(self):
        project = {"pid":"test_project"}
        pid = "test_project"
        manager = ProjectManager(TestExperimentSettings())
        project, settings = manager.get_project(pid)
        exp = TestExperiment(settings, project)
        self.assertEqual(exp.name, "default")
        exp = TestExperiment(settings, project, name="name")
        self.assertEqual(exp.name, "name")
        self.assertEqual(exp.logger, None)
        self.assertEqual(exp.force, False)
        self.assertEqual(exp.settings, settings)
        self.assertEqual(exp.project, project)
        self.assertEqual(exp.sp, 0)
        self.assertEqual(exp.pid, "test_project")
        self.assertEqual(exp.sid2step, {})
        self.assertEqual(exp.manager, None)
        self.assertEqual(exp.all_steps, STEPS)
        self.assertEqual(exp.get_settings(), settings)
        exp.clear_settings()
        self.assertEqual(exp.settings, None)

    def test_logger(self):
        pass

    def test_manager(self):
        pass

    def test_step_adding(self):
        project = {"pid":"test_project"}
        pid = "test_project"
        manager = ProjectManager(TestExperimentSettings())
        project, settings = manager.get_project(pid)
        exp = TestExperiment(settings, project, name="name")
        for i, step in enumerate(exp.get_avaliable_steps()):
            s = AbstractStep(step["name"], 
                        step["data"],
                        step["cf"],
                        )
            if i == 0:
                s0 = s
            if i == 1:
                s1 = s
            exp.add_step(s)
            self.assertEqual(exp.sp, i+1)
            self.assertEqual(exp.sid2step[i], s)
            self.assertEqual(exp.sid2step[i].sid, i)
        self.assertEqual(exp.get_step(0), s0)
        exp.remove_step(0)
        self.assertEqual(exp.get_step(0), None)
        exp.change_step(0, s1)
        self.assertEqual(exp.get_step(0), s1)
        self.assertEqual(exp.get_as_dict()["name"], 'name')


    def test_avalibale_steps(self):
        project = {"pid":"test_project"}
        pid = "test_project"
        manager = ProjectManager(TestExperimentSettings())
        project, settings = manager.get_project(pid)
        exp = TestExperiment(settings, project, name="name")
        step = exp.find_step("step_a")
        self.assertEqual(step, {
                'stage': "Test Stage A",
                'name': "step_a",
                'cf': sum,
                'data':None,
                'check': sum,
                'pre': None
            })
        stage = exp.find_steps_by_stage("Test Stage A")
        self.assertEqual(len(stage), 2)
        all_steps = exp.get_avaliable_steps()
        self.assertEqual(len(all_steps), 4)

    def test_execution(self):
        pass

      
if __name__ == '__main__':
    unittest.main()