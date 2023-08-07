import os

import bpy

from openpype.pipeline import publish
from openpype.hosts.blender.api import plugin, lib
from openpype.modules.kitsu.utils import credentials as kitsu_cred
from openpype.hosts.blender.api.pipeline import AVALON_PROPERTY


class ExtractBlockout(publish.Extractor):
    """Extract a blockout file."""

    label = "Extract Blockout"
    hosts = ["blender"]
    families = ["model", "rig"]
    optional = True

    def process(self, instance):
        print("------BLOCKOUT EXTRACTION------")
        col_array = []
        for collection in bpy.data.collections:
            if lib.get_collection_parent(collection) == "EXPORT":
                obj_array = []
                print(f"Collection {collection.name} is child of EXPORT exporting {collection.name}")
                for obj in bpy.data.collections[collection.name].all_objects:
                    obj_array.append(obj.name)
                collection_data = {'COLLECTION': collection.name, 'OBJECT' : obj_array}
                col_array.append(collection_data)

            print("------BLOCKOUT EXTRACTEDDATA------")
            for collection_data in col_array:
                print("OBJ DATA = ", collection_data['COLLECTION'])
                print("OBJ DATA = ", collection_data['OBJECT'])
                print("OBJ DATA SET ", collection_data)

                projects = kitsu_cred.gazu.project.get_project_by_name(os.environ['AVALON_PROJECT'])
                type = kitsu_cred.gazu.asset.get_asset_type_by_name('Animation')
                asset = kitsu_cred.gazu.asset.new_asset(
                    projects,
                    type,
                    collection_data['COLLECTION'],
                    "My asset description"
                )
                print("project = ", os.environ['AVALON_PROJECT'])
                print('-----------------')
