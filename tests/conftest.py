"""Configure tests for test_merge.py """

import os
import pathlib
import platform
import time

import photoscript
import pytest
from applescript import AppleScript

from osxphotos.fileutil import FileUtil


def get_os_version():

    # returns tuple containing OS version
    # e.g. 10.13.6 = (10, 13, 6)
    version = platform.mac_ver()[0].split(".")
    if len(version) == 2:
        (ver, major) = version
        minor = "0"
    elif len(version) == 3:
        (ver, major, minor) = version
    else:
        raise (
            ValueError(
                f"Could not parse version string: {platform.mac_ver()} {version}"
            )
        )
    return (ver, major, minor)


OS_VER = f"{get_os_version()[0]}.{get_os_version()[1]}"
if OS_VER == "10.15":
    TEST_LIBRARY_SOURCE = "TestSource-10.15.7.photoslibrary"
    TEST_LIBRARY_TARGET = "TestTarget-10.15.7.photoslibrary"
    TEST_DATA = "test_data_10_15_7.json"
else:
    TEST_LIBRARY_SOURCE = None
    TEST_LIBRARY_TARGET = None
    TEST_DATA = None
    pytest.exit("This test suite currently only runs on MacOS Catalina ")


def copy_photos_library(photos_library, destination=None):
    """ copy the test library, returns path to copied library """
    photoslib = photoscript.PhotosLibrary()
    photoslib.quit()
    picture_folder = (
        pathlib.Path(str(destination)) or pathlib.Path("~/Pictures").expanduser()
    )
    if not picture_folder.is_dir():
        pytest.exit(f"Invalid picture folder: '{picture_folder}'")
    src = pathlib.Path(os.getcwd()) / f"tests/test_libraries/{photos_library}"
    dest = picture_folder / photos_library
    FileUtil.copy(src, picture_folder)
    return dest


def open_photos_library(photoslibrary, delay=10):
    """ open a Photos library """
    photoslibrary = str(photoslibrary)
    script = AppleScript(
        f"""
            set tries to 0
            repeat while tries < 5
                try
                    tell application "Photos"
                        activate
                        delay 3 
                        open POSIX file "{photoslibrary}"
                        delay {delay}
                    end tell
                    set tries to 5
                on error
                    set tries to tries + 1
                end try
            end repeat
        """
    )
    script.run()


# @pytest.fixture(scope="session", autouse=True)
# def setup_photos():
#     copy_photos_library()


# @pytest.fixture(scope="session")
# @pytest.fixture
# def photoslib():
#     copy_photos_library()
#     return photoscript.PhotosLibrary()


@pytest.fixture
def suspend_capture(pytestconfig):
    class suspend_guard:
        def __init__(self):
            self.capmanager = pytestconfig.pluginmanager.getplugin("capturemanager")

        def __enter__(self):
            self.capmanager.suspend_global_capture(in_=True)

        def __exit__(self, _1, _2, _3):
            self.capmanager.resume_global_capture()

    yield suspend_guard()
