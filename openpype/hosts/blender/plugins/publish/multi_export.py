import os

import bpy
import math, random

from openpype.pipeline import publish
from openpype.hosts.blender.api import plugin
from openpype.hosts.blender.api.pipeline import AVALON_PROPERTY


class MultiExporter(publish.Extractor):
    """Extract as multiple FBX."""

    label = "Multi Exporter"
    hosts = ["blender"]
    families = ["model", "rig"]
    optional = True


    def select_objects(self, obj):
            bpy.context.view_layer.objects.active = obj
            obj.select_set(True)

    def process(self, instance):
        print("------------------------")
        bpy.ops.object.select_all(action='DESELECT')

        col_arr = ["_hehe", "_hihi", "hoho"]

        selected = []
        asset_group = None
        obj_loc_array = []

        for collection in bpy.data.collections:
            if collection.name in col_arr:
                selected.clear()

                for obj in bpy.data.collections[collection.name].all_objects:
                      selected.append(obj)
                      #Saving Object Original Position
                      obj_data = {'OBJ' : obj, 'LOC' : (obj.location.x, obj.location.y, obj.location.z)}
                      obj_loc_array.append(obj_data)
                      obj.location = (0,0,0)
                context = plugin.create_blender_context(active=asset_group, selected=selected)

                filename = f"{collection.name}.fbx"
                if not os.path.exists(instance.data['publishDir']):
                     os.mkdir(instance.data['publishDir'])
                filepath = os.path.join(instance.data['publishDir'], filename)
                bpy.ops.export_scene.fbx(
                context,
                filepath=filepath,
                use_active_collection=False,
                use_selection=True,
                mesh_smooth_type='FACE',
                add_leaf_bones=False
                )

        #Restore Original Object Location
        for obj_data in obj_loc_array:
             x = bpy.data.objects[obj_data['OBJ'].name]
             x.location = obj_data['LOC']
