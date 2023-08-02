import os

import bpy
import math, random

from openpype.pipeline import publish
from openpype.hosts.blender.api import plugin
from openpype.hosts.blender.api.pipeline import AVALON_PROPERTY


class ExtractBlockout(publish.Extractor):
    """Extract a blockout file."""

    label = "Extract Blockout"
    hosts = ["blender"]
    families = ["model", "rig"]
    optional = True

    def process(self, instance):
        print("------NEW------")
        col_array = []
        print("------COLLECTION CHECK------")
        for collection in bpy.data.collections:
            if collection.name.startswith("blockout"):
                print(collection.name)
                obj_array = []
                for obj in bpy.data.collections[collection.name].all_objects:
                    obj_array.append(obj.name)
                collection_data = {'COLLECTION': collection.name, 'OBJECT' : obj_array}
                col_array.append(collection_data)
            else:
                print("not a blockout collection")
        print("------DATA------")
        for collection_data in col_array:
            print("OBJ DATA = ", collection_data['COLLECTION'])
            print("OBJ DATA = ", collection_data['OBJECT'])
            print("OBJ DATA SET ", collection_data)
