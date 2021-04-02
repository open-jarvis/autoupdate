"""
Copyright (c) 2021 Philipp Scheer
"""


import os
import stat
import shutil
import tarfile


# from https://stackoverflow.com/a/43527803/9360322
def install(downloaded_archive, local_installation_path):
    shutil.rmtree(local_installation_path, ignore_errors=True)
    shutil.unpack_archive(downloaded_archive, local_installation_path)
    os.unlink(downloaded_archive)


def copydirectory(root_src_dir, root_dst_dir):
    """
    Copy directory tree. Overwrites also read only files.
    :param root_src_dir: source directory
    :param root_dst_dir:  destination directory
    """

    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                try:
                    os.remove(dst_file)
                except PermissionError as exc:
                    os.chmod(dst_file, stat.S_IWUSR)
                    os.remove(dst_file)

            shutil.copy(src_file, dst_dir)