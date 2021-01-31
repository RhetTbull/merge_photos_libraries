"""Test merge Photos libraries """

import json
import os
import pathlib

import photoscript
import pytest
from click.testing import CliRunner
from tests.conftest import (
    TEST_DATA,
    TEST_LIBRARY_SOURCE,
    TEST_LIBRARY_TARGET,
    open_photos_library,
    suspend_capture,
)

from osxphotos import PhotosDB
from osxphotos.utils import get_last_library_path


def test_merge(suspend_capture):
    from merge_photos_libraries.cli import merge

    runner = CliRunner()
    test_dir = pathlib.Path(os.getcwd())
    # pylint: disable=not-context-manager
    last_library = get_last_library_path()
    with runner.isolated_filesystem():
        with suspend_capture:
            picture_folder = str(pathlib.Path("~/Pictures").expanduser())
            prompt = (
                "To run these tests, you will need to copy the test libraries to your Pictures directory or another folder. "
                f"Enter the folder path here or press Return to use '{picture_folder}': "
            )
            answer = input(f"\n{prompt}")
            if answer:
                picture_folder = answer
            assert pathlib.Path(picture_folder).exists()
            os.system(f"open {test_dir}/tests/test_libraries")
            os.system(f"open {picture_folder}")
            prompt = (
                "Press 'y' after you have copied the test libraries to your folder. "
                "You should quit Photos if it's running before copying the libraries: "
            )
            answer = input(f"\n{prompt}")
            assert answer.lower() == "y"

        source = pathlib.Path(picture_folder) / TEST_LIBRARY_SOURCE
        dest = pathlib.Path(picture_folder) / TEST_LIBRARY_TARGET

        # delete previous merge database if it exists
        mergedb_path = dest.parent / f"{dest.stem}.osxphotos_merge.db"
        if mergedb_path.exists():
            mergedb_path.unlink()

        source = str(source)
        dest = str(dest)

        open_photos_library(dest, 10)
        result = runner.invoke(merge, [source, dest, "-V"])
        assert result.exit_code == 0

        with open(test_dir / "tests" / TEST_DATA) as fp:
            test_data = json.load(fp)

        photosdb = PhotosDB(dbfile=dest)
        for photo in photosdb.photos():
            filestem = pathlib.Path(photo.original_filename).stem
            assert filestem in test_data
            data = test_data[filestem]
            assert sorted(photo.keywords) == sorted(data["keywords"])
            assert photo.title == data["title"]
            assert photo.description == data["description"]
            assert photo.favorite == data["favorite"]
            folder_albums = photo.render_template("{folder_album,}")
            folder_albums = folder_albums[0] if folder_albums[0][0] != "" else []
            assert sorted(folder_albums) == sorted(data["folder_albums"])

        # re-open the library that was open prior to testing
        # open_photos_library(last_library, 10)
