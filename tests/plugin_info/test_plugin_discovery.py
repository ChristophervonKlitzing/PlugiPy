import unittest
import os
from plugipy.plugin_info.common_pipeline_steps import create_has_directory_filter, create_has_file_filter, directory_filter, file_filter
from plugipy.plugin_info.plugin_finder import PluginFinder

class TestPluginDiscovery(unittest.TestCase):
    def setUp(self) -> None:
        self.search_path = os.path.join(os.path.dirname(__file__), "./test_plugins")
        return super().setUp()
    
    def test_default(self):
        finder = PluginFinder(self.search_path)

        plugin_names = {pinfo.name for pinfo in finder.find_all()}  # no guaranteed order required
        self.assertSetEqual(plugin_names, {"plugin_a", "plugin_b", "plugin_c"})

    def test_directory_filter(self):
        finder = PluginFinder(self.search_path)
        finder.add_to_pipeline(directory_filter)

        plugin_names = {pinfo.name for pinfo in finder.find_all()}  # no guaranteed order required
        self.assertSetEqual(plugin_names, {"plugin_a", "plugin_c"})
    
    def test_file_filter(self):
        finder = PluginFinder(self.search_path)
        finder.add_to_pipeline(file_filter)

        plugin_names = {pinfo.name for pinfo in finder.find_all()}  # no guaranteed order required
        self.assertSetEqual(plugin_names, {"plugin_b"})
    
    def test_has_file_filter(self):
        finder = PluginFinder(self.search_path)
        finder.add_to_pipeline(create_has_file_filter("README.md"))

        plugin_names = {pinfo.name for pinfo in finder.find_all()}  # no guaranteed order required
        self.assertSetEqual(plugin_names, {"plugin_c"})

    def test_has_dir_filter(self):
        finder = PluginFinder(self.search_path)
        finder.add_to_pipeline(create_has_directory_filter("subdirA"))
        finder.add_to_pipeline(create_has_directory_filter("subdirB"))

        plugin_names = {pinfo.name for pinfo in finder.find_all()}  # no guaranteed order required
        self.assertSetEqual(plugin_names, {"plugin_a"})
    
    def test_find_by_name(self):
        finder = PluginFinder(self.search_path)

        pinfo = finder.find_by_name("not-existing-plugin")
        self.assertIsNone(pinfo, "A not existing plugin should not result in a valid PluginInfo instance")

        pinfo = finder.find_by_name("plugin_a")
        self.assertIsNotNone(pinfo, "An existing plugin should result in a valid PluginInfo instance")

        self.assertEqual(finder.error_string, "", "A not failing PluginFinder should have an empty error-string")
        pinfo = finder.find_by_name("plugin_a", extra_steps=[create_has_file_filter("some-not-existing-file.txt")])
        self.assertIsNone(pinfo, "A plugin which does not fulfil all pipeline steps should not result in a valid PluginInfo instance")
        self.assertNotEqual(finder.error_string, "", "The error-string should not be empty when failing to find a plugin by name")