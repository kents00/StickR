import os
import bpy
from bpy_extras.io_utils import ImportHelper

bl_info = {
    "name": "StickR",
    "author": "KentEdoloverio",
    "description": "Import images as stickeR",
    "blender": (2, 83, 0),
    "version": (2, 1, 0),
    "location": "SHIFT+A > Image > Image as Decal",
    "warning": "",
    "category": "3D View > StickR",
}


class StickRPreference(bpy.types.AddonPreferences):
    bl_idname_ = __package__

    stickr_path: bpy.props.StringProperty(
        default="Choose Path", name="Directory", subtype='DIR_PATH')

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'stickr_path')


class StickRLoadPreviews(bpy.types.Operator):
    bl_idname = 'stickr.loadpreviews'
    bl_label = 'Refresh'
    bl_description = "Refresh"
    bl_options = {'PRESET', 'UNDO'}

    def execute(self, context):
        return {'FINISHED'}


class StickRPanel(bpy.types.Panel):
    bl_idname = "StickR_Panel"
    bl_label = "StickR"
    bl_category = "StickR"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        scene = context.scene
        layout = self.layout

        box = layout.box()
        row = box.row()

        row = box.row()
        row.scale_y = 2.0
        row.scale_x = 2.0
        row.operator("stickr.loadpreviews",
                     text="Refresh", icon="FILE_REFRESH")

        return {'FINISHED'}


classes = (
    StickRPreference,
    StickRLoadPreviews,
    StickRPanel,

)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in classes:
        bpy.utils.register_class(cls)


if __name__ == "__main__":
    register()
