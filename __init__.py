import os
import bpy
from .Updater_OP import *
from .Updater import engine
from bpy_extras.io_utils import ImportHelper
from bpy.types import AddonPreferences, Operator, Panel
from bpy.props import StringProperty, EnumProperty, CollectionProperty

bl_info = {
    "name": "StickR",
    "author": "Kent Edoloverio",
    "description": "Import images as stickeR",
    "blender": (4, 0, 2),
    "version": (1, 0, 0),
    "location": "3D View > KLicense",
    "warning": "",
    "category": "3D View",
}

preview_collections = {}
icon_collection = {}
preview_list = {}
addon_keymaps = []


def preferences():
    return bpy.context.preferences.addons[__name__].preferences


def add_to_image_menu(self, context):
    layout = self.layout
    layout.operator("stickr.importenum", icon='OUTLINER_OB_IMAGE')


class StickRAddonPreference(AddonPreferences):
    bl_idname = __name__

    directory_path: StringProperty(
        default="Choose Path",
        name="Directory",
        subtype='DIR_PATH')

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'directory_path')
        box = layout.box()
        row = box.row()
        row.scale_y = 2
        row.operator("addonupdater.release_notes", icon="HELP")
        row = box.row()
        row.scale_y = 2
        row.operator(Check_for_update.bl_idname, icon="TRIA_DOWN_BAR")
        row.scale_y = 2
        row.alert = True
        row.operator(Update.bl_idname, icon="FILE_REFRESH")

        json_file_path = os.path.join(
            os.path.dirname(__file__), "version_info.json")

        try:
            with open(json_file_path, 'r') as json_file:
                version_info = json.load(json_file)

                if engine._latest_version is not None:
                    row = box.row()
                    row.label(
                        text=f"Version: {version_info['current_version']}")
                elif engine._current_version != engine._latest_version:
                    row = box.row()
                    row.label(
                        text=f"New version: {version_info['latest_version']}")
                elif engine._current_version == engine._latest_version:
                    row = box.row()
                    row.label(
                        text=f"You are using the latest version: {version_info['current_version']}")
                if engine._update_date is not None:
                    row = box.row()
                    row.label(text=f"Last update: {engine._update_date}")
        except json.decoder.JSONDecodeError as e:
            print(f"Error loading JSON file: {e}")
            row = box.row()
            row.label(text="Last update: Never")
        except FileNotFoundError:
            row = box.row()
            row.label(text="Error loading version information.")


def get_preview_items(self, context):
    enum_items = []
    name = self.name
    if name in preview_list.keys():
        list = preview_list[name]
        if context is None:
            return enum_items
        pcoll = preview_collections[name]
        if len(pcoll.my_previews) > 0:
            return pcoll.my_previews

        for i, name in enumerate(list):
            if name.endswith((".png", ".jpg")):
                thumb = pcoll.load(name, name, 'IMAGE')
                enum_items.append(
                    (name, os.path.basename(name.replace(".png", "").replace(".jpg", "")), "", thumb.icon_id, i))
        pcoll.my_previews = enum_items
        return pcoll.my_previews
    return []


class StickRLoadPreviews(Operator):
    bl_idname = 'stickr.refresh'
    bl_label = 'Refresh'
    bl_description = "Refresh"
    bl_options = {'PRESET', 'UNDO'}

    def execute(self, context):
        context.scene.stickr.clear()
        for pcoll in preview_collections.values():
            bpy.utils.previews.remove(pcoll)
        preview_collections.clear()
        preview_list.clear()
        allfiles = []
        alldirs = []

        if os.path.isdir(preferences().directory_path):
            for path, dirs, files in os.walk(preferences().directory_path):
                alldirs += [os.path.join(path, dir) for dir in dirs]

            for a in alldirs+[os.path.dirname(preferences().directory_path),]:
                allfiles = [os.path.join(a, f) for f in os.listdir(a)]
                og_name = a
                i = 1
                while os.path.basename(a) in bpy.context.scene.stickr.keys():
                    a = og_name+f"-{i}"
                    i += 1
                temp = bpy.context.scene.stickr.add()
                temp.name = os.path.basename(a)
                preview_list[os.path.basename(a)] = allfiles
                pcoll = bpy.utils.previews.new()
                pcoll.my_previews = ()
                preview_collections[os.path.basename(a)] = pcoll
        return {'FINISHED'}


class StickRInfo(bpy.types.PropertyGroup):
    name: StringProperty(name="name", default="StickR")
    preview: EnumProperty(items=get_preview_items)


def stickr_directories(self, context):
    return [(a.name, a.name, a.name) for a in context.scene.stickr] if context.scene.stickr else [("None", "None", "None")]


class StickRPanel(Panel):
    bl_label = "StickR"
    bl_idname = "OBJECT_PT_STICKR"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "StickR"

    def draw(self, context):
        layout = self.layout
        box = layout.box()
        row = box.row()
        row.scale_y = 2
        row.scale_x = 2
        row.operator("stickr.refresh", icon="FILE_REFRESH")
        row = box.row()
        row.scale_y = 1.5
        row.scale_x = 1.5
        row.prop(context.scene, 'stickr_directories')
        if context.scene.stickr_directories in context.scene.stickr.keys():
            layout.template_icon_view(
                context.scene.stickr[context.scene.stickr_directories],
                "preview",
                show_labels=True,
                scale=8,
                scale_popup=6,)
            layout.label(
                text=context.scene.stickr[context.scene.stickr_directories].preview)

            row = box.row()
            row.scale_y = 2
            row.scale_x = 2
            row.operator("stickr.importenum")

        active_object = context.active_object
        if active_object and active_object.type in {'MESH', 'CURVE', 'FONT', 'SURFACE'} and active_object.data.materials:
            mat = active_object.data.materials[0]
            if mat and "StickR Shader" in [a.name for a in mat.node_tree.nodes]:
                self.draw_material_settings(
                    layout, mat.node_tree.nodes['StickR Shader'].inputs)

    def draw_material_settings(self, layout, inputs):
        layout.prop(inputs[2], 'default_value', text="Scale")
        layout.prop(inputs[3], 'default_value', text="Worn Strength")
        layout.prop(inputs[11], 'default_value', text="Scratches")
        layout.prop(inputs[16], 'default_value',
                    text="Scratches Strength")

        row = layout.column(align=True)
        row.label(text="Offset:")
        layout.prop(inputs[17], 'default_value', text="")

        layout.prop(inputs[4], 'default_value', text="Contrast")
        layout.prop(inputs[5], 'default_value', text="Roughness")
        layout.prop(inputs[6], 'default_value', text="Edge")
        layout.prop(inputs[7], 'default_value', text="Damage Hue")
        layout.prop(inputs[8], 'default_value',
                    text="Damage Saturation")
        layout.prop(inputs[9], 'default_value',
                    text="Damage Brightness")
        layout.prop(inputs[10], 'default_value', text="Bump Strength")
        layout.prop(inputs[12], 'default_value', text="Rotation")
        layout.prop(inputs[13], 'default_value', text="Distortion")
        layout.prop(inputs[14], 'default_value', text="Scale")
        layout.prop(inputs[15], 'default_value', text="Thickness")


class StickRImportEnum(bpy.types.Operator):
    bl_idname = 'stickr.importenum'
    bl_label = 'Import Image'
    bl_description = "Import image as StickR"
    bl_options = {'PRESET', 'UNDO'}

    def execute(self, context):
        path = context.scene.stickr[context.scene.stickr_directories].preview
        active_object = context.active_object if context.selected_objects else None

        plane = None
        if os.path.isfile(path):
            img = bpy.data.images.load(path)
            res_x = img.size[0] / 1000
            res_y = img.size[1] / 1000
            bpy.ops.mesh.primitive_plane_add()
            plane = context.active_object
            plane.scale.x = res_x
            plane.scale.y = res_y
            plane.rotation_euler = [1.5707, 0, 1.5707]
            plane.location = [0, 0, 0.01]
            bpy.ops.object.transform_apply(
                location=True, rotation=False, scale=True)
            mat = bpy.data.materials.new(img.name)
            mat.use_nodes = True
            mat.blend_method = 'CLIP'
            plane.data.materials.append(mat)
            nodes = mat.node_tree.nodes
            output_socket = None
            if "Principled BSDF" in [n.name for n in nodes]:
                output_socket = nodes['Principled BSDF'].outputs[0].links[0].to_socket
                nodes.remove(nodes['Principled BSDF'])
            if bpy.data.node_groups.get('StickR Shader') is None:
                path = os.path.join(os.path.join(os.path.dirname(
                    os.path.abspath(__file__)), "Assets"), "asset.blend", "NodeTree")
                bpy.ops.wm.append(
                    directory=path, filename='StickR Shader', autoselect=False)

            StickRShaderGroup = nodes.new('ShaderNodeGroup')
            StickRShaderGroup.location = 0, 300
            StickRShaderGroup.name = "StickR Shader"
            StickRShaderGroup.node_tree = bpy.data.node_groups.get(
                'StickR Shader')
            if output_socket:
                mat.node_tree.links.new(
                    StickRShaderGroup.outputs[0], output_socket)
            img_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            img_node.location = -300, 300
            img_node.image = img
            mat.node_tree.links.new(
                img_node.outputs[0], StickRShaderGroup.inputs[0])
            mat.node_tree.links.new(
                img_node.outputs[1], StickRShaderGroup.inputs[1])
            subsurf_mod = plane.modifiers.new(type="SUBSURF", name="Subdivide")
            subsurf_mod.levels = 3
            subsurf_mod.render_levels = 3
            subsurf_mod.subdivision_type = 'SIMPLE'

        if active_object and plane:
            bpy.ops.object.shade_smooth()
            plane.data.use_auto_smooth = True
            shrink_mod = plane.modifiers.new(
                type="SHRINKWRAP", name="Shrinkwrap")
            shrink_mod.target = active_object
            shrink_mod.offset = 0.003
            shrink_mod.wrap_method = 'PROJECT'
            shrink_mod.use_project_z = True
            shrink_mod.use_negative_direction = True
            bpy.context.scene.tool_settings.snap_elements = {'FACE'}
            bpy.context.scene.tool_settings.use_snap_align_rotation = True
            bpy.context.scene.tool_settings.snap_target = 'CENTER'

        return {'FINISHED'}


class StickRImportImage(bpy.types.Operator, ImportHelper):
    bl_idname = 'stickr.importimage'
    bl_label = 'Import Image'
    bl_description = "Import image as StickR"
    bl_options = {'PRESET', 'UNDO'}

    filter_glob: StringProperty(
        default='*.jpg;*.jpeg;*.png;*.tif;*.tiff;*.bmp',
        options={'HIDDEN'}
    )

    def execute(self, context):
        path = self.filepath
        active_object = context.active_object if context.selected_objects else None

        plane = None
        if os.path.isfile(path):
            img = bpy.data.images.load(path)
            res_x = img.size[0] / 1000
            res_y = img.size[1] / 1000
            bpy.ops.mesh.primitive_plane_add()
            plane = context.active_object
            plane.scale.x = res_x
            plane.scale.y = res_y
            plane.rotation_euler = [1.5707, 0, 1.5707]
            plane.location = [0, 0, 0.01]
            bpy.ops.object.transform_apply(
                location=True, rotation=False, scale=True)
            mat = bpy.data.materials.new(img.name)
            mat.use_nodes = True
            mat.blend_method = 'CLIP'
            plane.data.materials.append(mat)
            nodes = mat.node_tree.nodes
            output_socket = None
            if "Principled BSDF" in [n.name for n in nodes]:
                output_socket = nodes['Principled BSDF'].outputs[0].links[0].to_socket
                nodes.remove(nodes['Principled BSDF'])
            if bpy.data.node_groups.get('StickR Shader') is None:
                path = os.path.join(os.path.join(os.path.dirname(
                    os.path.abspath(__file__)), "Assets"), "Assets.blend", "NodeTree")
                bpy.ops.wm.append(
                    directory=path, filename='StickR Shader', autoselect=False)

            StickRShaderGroup = nodes.new('ShaderNodeGroup')
            StickRShaderGroup.location = 0, 300
            StickRShaderGroup.name = "StickR Shader"
            StickRShaderGroup.node_tree = bpy.data.node_groups.get(
                'StickR Shader')
            if output_socket:
                mat.node_tree.links.new(
                    StickRShaderGroup.outputs[0], output_socket)
            img_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            img_node.location = -300, 300
            img_node.image = img
            mat.node_tree.links.new(
                img_node.outputs[0], StickRShaderGroup.inputs[0])
            mat.node_tree.links.new(
                img_node.outputs[1], StickRShaderGroup.inputs[1])
            subsurf_mod = plane.modifiers.new(type="SUBSURF", name="Subdivide")
            subsurf_mod.levels = 6
            subsurf_mod.render_levels = 6
            subsurf_mod.subdivision_type = 'SIMPLE'

        if active_object and plane:
            bpy.ops.object.shade_smooth()
            plane.data.use_auto_smooth = True
            shrink_mod = plane.modifiers.new(
                type="SHRINKWRAP", name="Shrinkwrap")
            shrink_mod.target = active_object
            shrink_mod.offset = 0.003
            shrink_mod.wrap_method = 'PROJECT'
            shrink_mod.use_project_z = True
            shrink_mod.use_negative_direction = True
            bpy.context.scene.tool_settings.snap_elements = {'FACE'}
            bpy.context.scene.tool_settings.use_snap_align_rotation = True
            bpy.context.scene.tool_settings.snap_target = 'CENTER'

        return {'FINISHED'}


classes = (
    StickRAddonPreference,
    StickRLoadPreviews,
    StickRInfo,
    StickRPanel,
    StickRImportEnum,
    StickRImportImage,
    Release_Notes,
    Update,
    Check_for_update,
)


def register():

    engine.user = "kents00"  # Replace this with your username
    engine.repo = "StickR"  # Replace this with your repository name
    engine.token = None  # Set your GitHub token here if necessary

    for cls in classes:
        bpy.utils.register_class(cls)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    kmaps = [
        # Add your keymaps here if needed
    ]

    km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
    if kc:
        for (op, k, sp) in kmaps:
            kmi = km.keymap_items.new(
                op,
                type=k,
                value="PRESS",
                alt="alt" in sp,
                shift="shift" in sp,
                ctrl="ctrl" in sp,
            )
            addon_keymaps.append((km, kmi))

    bpy.types.VIEW3D_MT_image_add.append(add_to_image_menu)
    bpy.types.Scene.stickr = CollectionProperty(type=StickRInfo)
    bpy.types.Scene.stickr_directories = EnumProperty(
        items=stickr_directories, name="")


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)

    for (km, kmi) in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()
    bpy.types.VIEW3D_MT_image_add.remove(add_to_image_menu)
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    preview_list.clear()


if __name__ == "__main__":
    register()
