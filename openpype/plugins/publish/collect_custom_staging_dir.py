"""
Requires:
    anatomy


Provides:
    instance.data     -> stagingDir (folder path)
                      -> stagingDir_persistent (bool)
"""
import copy
import os.path

import pyblish.api

from openpype.pipeline import get_transient_data_profile


class CollectTransientDataDir(pyblish.api.InstancePlugin):
    """Looks through profiles if Transient data (stagingDir) should be
    persistent and in special location.

    Transient dir could be useful in specific use cases where is
    desirable to have temporary renders in specific, persistent folders, could
    be on disks optimized for speed for example.

    It is studio responsibility to clean up obsolete folders with data.

    Location of the folder is configured in `project_anatomy/templates/others`.
    ('transient' key is expected, with 'folder' key)

    Which family/task type/subset is applicable is configured in:
    `project_settings/global/tools/publish/custom_staging_dir_profiles`

    """
    label = "Collect Transient Data Directory"
    order = pyblish.api.CollectorOrder + 0.4990

    template_key = "transient"

    def process(self, instance):
        family = instance.data["family"]
        subset_name = instance.data["subset"]
        host_name = instance.context.data["hostName"]
        project_name = instance.context.data["projectName"]
        project_settings = instance.context.data["project_settings"]
        anatomy = instance.context.data["anatomy"]
        task = instance.data["anatomyData"].get("task", {})

        transient_data_profile = get_transient_data_profile(
            project_name, host_name, family, task.get("name"),
            task.get("type"), subset_name, project_settings=project_settings,
            anatomy=anatomy, log=self.log)

        if transient_data_profile:
            anatomy_data = copy.deepcopy(instance.data["anatomyData"])
            anatomy_data["root"] = anatomy.roots
            scene_name = instance.context.data.get("currentFile")
            if scene_name:
                anatomy_data["scene_name"] = os.path.basename(scene_name)
            transient_dir = transient_data_profile[
                "transient_template"].format(**anatomy_data)
            instance.data["stagingDir"] = transient_dir

            # TODO: remove traces of `stagingDir_persistent` in the future
            # maintain backward compatibility
            instance.data["stagingDir_persistent"] = transient_data_profile[
                "transient_persistence"]

            instance.data["stagingDirPersistence"] = transient_data_profile[
                "transient_persistence"]

            result_str = "Adding '{}' as".format(transient_dir)
        else:
            result_str = "Not adding"

        self.log.debug("{} custom staging dir for instance with '{}'".format(
            result_str, family
        ))
