import pyblish.api
from openpype.hosts.blender.api.workio import save_file


class IncrementWorkfileVersion(pyblish.api.ContextPlugin):
    """Increment current workfile version."""

    order = pyblish.api.IntegratorOrder + 0.9
    label = "Increment Workfile Version"
    optional = True
    hosts = ["blender"]
    families = ["animation", "model", "rig", "action", "layout"]

    def process(self, context):

        assert all(result["success"] for result in context.data["results"]), (
            "Publishing not successful so version is not increased.")

        from openpype.lib import version_up
        path = context.data["currentFile"]
        filepath = version_up(path)

        save_file(filepath, copy=False)

        self.log.info('Incrementing script version')



////////////

print("------------------------")

col_array = []

for collection in bpy.data.collections:
    if collection.name.startswith("blockout"):
        print(collection.name)
        for obj in bpy.data.collections[collection.name].all_objects:
            collection_data = {'COLLECTION': collection.name, 'OBJECT' : obj.name}
            col_array.append(collection_data)
    else:
        print("not a blockout collection")

for collection_data in col_array:
    print("OBJ DATA = ", collection_data['COLLECTION'])
    print("OBJ DATA = ", collection_data['OBJECT'])
