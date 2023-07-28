import os

import bpy

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



        for collection in bpy.data.collections:
            for col in col_arr:
                #context = plugin.create_blender_context(active=asset_group, selected=plugin.get_selection())
                name = collection.name
                if col in name:
                    for obj in bpy.data.collections[collection.name].all_objects:
                        self.select_objects(obj)
                        for obj in bpy.context.selected_objects:
                            org_loc = obj.location.copy()
                            print(obj)

                            # Sends object to zero vectors.
                            obj.location = (0,0,0)


                            print("C BON")
                else:
                    print("C PAS BON")

                # override = plugin.create_blender_context(
                # active=asset, bpy.data.collections[collection.name].all_objects)
               # bpy.ops.export_scene.fbx(filepath=f"C:/Users/DMS7/Desktop/{collection.name}.fbx", use_selection=True)
                # bpy.ops.export_scene.fbx(
                # bpy.context,
                # filepath=f"C:/Users/DMS7/Desktop/{collection.name}.fbx",
                # use_active_collection=False,
                # use_selection=True,
                # mesh_smooth_type='FACE',
                # add_leaf_bones=False
                # )
                # obj.location = org_loc

            bpy.ops.object.select_all(action='DESELECT')
