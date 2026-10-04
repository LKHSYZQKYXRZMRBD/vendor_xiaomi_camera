#!/usr/bin/env -S PYTHONPATH=../../../tools/extract-utils python3
#
# SPDX-FileCopyrightText: 2024 The LineageOS Project
# SPDX-License-Identifier: Apache-2.0
#

from pathlib import Path
import subprocess

from extract_utils.fixups_blob import (
    BlobFixupCtx,
    blob_fixup,
    blob_fixups_user_type,
)
from extract_utils.file import File
from extract_utils.fixups_lib import (
    lib_fixup_vendorcompat,
    lib_fixups as default_lib_fixups,
    lib_fixups_user_type,
    libs_proto_3_9_1,
)
from extract_utils.main import (
    ExtractUtils,
    ExtractUtilsModule,
)
from extract_utils.makefiles import (
    MakefilesCtx,
    ProductPackagesCtx,
)


def split_miuicamera(
    ctx: BlobFixupCtx,
    file: File,
    file_path: str,
    *args,
    **kwargs,
):
    apk_path = Path(file_path)
    for part in apk_path.parent.glob(f'{apk_path.name}.part??'):
        part.unlink()

    subprocess.run(
        [
            'split',
            '--bytes=20M',
            '--suffix-length=2',
            '-d',
            file_path,
            f'{file_path}.part',
        ],
        check=True,
    )


def add_miuicamera_symlinks(
    ctx: MakefilesCtx,
    packages_ctx: ProductPackagesCtx,
):
    ctx.mk_out.write(
        '''
ifneq ($(filter fuxi nuwa ishtar,$(TARGET_DEVICE)),)

CAMERA_LIBRARIES := libcamera_algoup_jni.xiaomi.so libcamera_mianode_jni.xiaomi.so

CAMERA_SYMLINKS := $(addprefix $(TARGET_OUT_APPS_PRIVILEGED)/MiuiCamera/lib/arm64/,$(notdir $(CAMERA_LIBRARIES)))
$(CAMERA_SYMLINKS): $(LOCAL_INSTALLED_MODULE)
\t@echo "MiuiCamera lib link: $@"
\t@mkdir -p $(dir $@)
\t@rm -rf $@
\t$(hide) ln -sf /system/lib64/$(notdir $@) $@

ALL_DEFAULT_INSTALLED_MODULES += $(CAMERA_SYMLINKS)

endif
'''
    )


def add_system_camera_libraries(
    ctx: MakefilesCtx,
    packages_ctx: ProductPackagesCtx,
):
    ctx.product_mk_out.write(
        '\nPRODUCT_PACKAGES += ' + '\\' + '\n    libhidltransport\n'
    )


def lib_fixup_system_variant(lib: str, partition: str):
    if partition == 'system':
        return f'{lib}_system'

    return None


lib_fixups: lib_fixups_user_type = {
    **default_lib_fixups,
    libs_proto_3_9_1: lib_fixup_vendorcompat,
    (
        'libOpenCL',
        'libcdsprpc',
        'libvmmem',
        'vendor.qti.hardware.dsp@1.0',
        'vendor.xiaomi.hardware.campostproc@1.0',
    ): lib_fixup_system_variant,
}

blob_fixups: blob_fixups_user_type = {
    'system/lib64/libgui-xiaomi.so': blob_fixup().binary_regex_replace(
        b'android.hardware.graphics.common-V[4-5]-ndk\\.so',
        b'android.hardware.graphics.common-V7-ndk.so',
    ),
    (
        'system/lib64/libcamera_algoup_jni.xiaomi.so',
        'system/lib64/libcamera_mianode_jni.xiaomi.so',
    ): blob_fixup()
        .replace_needed('libgui.so', 'libgui-xiaomi.so')
        .sig_replace('08 AD 40 F9', '08 A9 40 F9'),
    'system/lib64/libmicampostproc_client.so': blob_fixup().remove_needed(
        'libhidltransport.so'
    ),
    'system/priv-app/MiuiCamera/MiuiCamera.apk': blob_fixup()
        .apktool_patch('patches/MiuiCamera')
        .call(split_miuicamera, need_tmp_dir=False),
}

module = ExtractUtilsModule(
    'camera',
    'xiaomi',
    device_rel_path='vendor/xiaomi/camera',
    blob_fixups=blob_fixups,
    lib_fixups=lib_fixups,
    namespace_imports=[],
)

module.proprietary_files[0].add_post_makefile_generation_fn(
    add_miuicamera_symlinks
)
module.proprietary_files[0].add_post_makefile_generation_fn(
    add_system_camera_libraries
)

if __name__ == '__main__':
    utils = ExtractUtils.device(module)
    utils.run()
