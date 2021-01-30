"""Proof of concept showing how to merge Apple Photos libraries including most of the metadata """

# Currently working:
# * places photos into correct albums and folder structure
# * sets title, description, keywords, location
# Limitations:
# * doesn't currently handle Live Photos or RAW+JPEG pairs
# * only merges the most recent version of the photo (edit history is lost)
# * very limited error handling
# * doesn't merge Person In Image

import os
import pathlib
import sqlite3
import tempfile

import click
import photoscript

import osxphotos

CLI_COLOR_ERROR = "red"
CLI_COLOR_WARNING = "yellow"

VERBOSE = False


def verbose_(*args, **kwargs):
    """Print output if verbose flag set """
    if VERBOSE:
        styled_args = []
        for arg in args:
            if type(arg) == str:
                if "error" in arg.lower():
                    arg = click.style(arg, fg=CLI_COLOR_ERROR)
                elif "warning" in arg.lower():
                    arg = click.style(arg, fg=CLI_COLOR_WARNING)
            styled_args.append(arg)
        click.echo(*styled_args, **kwargs)


class MergeDB:
    """Database to checkpoint merge progress """

    def __init__(self, dbpath):
        if type(dbpath) != pathlib.Path:
            dbpath = pathlib.Path(dbpath)
        self._dbpath = dbpath
        self._db = self._open_db(dbpath) if dbpath.exists else self._create_db(dbpath)

    def _open_db(self, dbpath):
        print(f"_open_db: {dbpath}")

    def _create_db(self, dbpath):
        print(f"_create_db: {dbpath}")


@click.command()
@click.argument("src_library", metavar="SOURCE", nargs=1, type=click.Path(exists=True))
@click.argument(
    "dest_library", metavar="DESTINATION", nargs=-1, type=click.Path(exists=True)
)
@click.option("--verbose", "-V", is_flag=True, help="Print verbose output.")
@click.option("--dry-run", is_flag=True, help="Dry run, don't actually import.")
@click.pass_context
def merge(ctx, src_library, dest_library, verbose, dry_run):
    """Merge photos libraries """
    global VERBOSE
    VERBOSE = verbose

    if not dest_library:
        dest_library = osxphotos.utils.get_last_library_path()
    else:
        # dest_library is a tuple due to nargs=-1
        dest_library = dest_library[0]

    dest_library = pathlib.Path(dest_library).expanduser()
    src_library = pathlib.Path(src_library).expanduser()

    if src_library.samefile(dest_library):
        click.secho(f"src_library and dest_library cannot be the same", fg="red")
        raise click.Abort()

    verbose_(f"Opening source library {src_library}")
    src = osxphotos.PhotosDB(dbfile=str(src_library))
    src_photos = src.photos()

    verbose_(f"Opening destination library {dest_library}")
    mergedb_path = dest_library.parent / f".{dest_library.stem}.osxphotos_merge.db"
    mergedb = MergeDB(mergedb_path)
    dest = photoscript.PhotosLibrary()
    dest.open(dest_library)
    dest.hide()

    verbose_(f"Merging {len(src_photos)} photos from {src_library} to {dest_library}")
    # send progress bar output to /dev/null if verbose to hide the progress bar
    fp = open(os.devnull, "w") if verbose else None
    with click.progressbar(src_photos, file=fp) as bar:
        for src_photo in bar:
            path = src_photo.path_edited if src_photo.hasadjustments else src_photo.path
            if not path:
                click.secho(
                    f"Skipping missing photo {src_photo.original_filename} ({src_photo.uuid})",
                    fg="red",
                )
                continue

            # export photo to temp file and rename to original_filename
            # handling of RAW+JPEG pairs, Live photos, favorites, etc. left as exercise for the reader
            # RAW+JPEG pairs will be correctly handled if imported like this:
            # dest.import_photos(["/Users/rhet/Desktop/export/IMG_1994.JPG", "/Users/rhet/Desktop/export/IMG_1994.cr2"])
            # Live Photos will be correctly handled if imported like this:
            # dest.import_photos(["/Users/rhet/Desktop/export/IMG_3259.HEIC","/Users/rhet/Desktop/export/IMG_3259.mov"])
            ext = pathlib.Path(path).suffix
            dest_file = pathlib.Path(src_photo.original_filename).stem + ext
            verbose_(f"Importing photo {dest_file}")
            with tempfile.TemporaryDirectory() as tmpdir:
                # get right suffix for original or edited file
                if not dry_run:
                    exported = src_photo.export(
                        tmpdir,
                        dest_file,
                        edited=src_photo.hasadjustments,
                        live_photo=True,
                        raw_photo=True,
                    )
                    if not exported:
                        click.secho(
                            f"Error exporting photo {src_photo.original_filename} ({src_photo.uuid})",
                            fg=CLI_COLOR_ERROR,
                        )
                        continue
                    exported = [
                        str(pathlib.Path(tmpdir) / filename) for filename in exported
                    ]
                    print(exported)

                    dest_photos = dest.import_photos(
                        exported, skip_duplicate_check=True
                    )
                    if not dest_photos:
                        click.secho(
                            f"Error importing photo {src_photo.original_filename} ({src_photo.uuid})",
                            fg=CLI_COLOR_ERROR,
                        )
                        continue

                    for dest_photo in dest_photos:
                        verbose_(f"Setting metadata for {dest_photo.filename}")
                        # todo: add favorite
                        dest_photo.description = src_photo.description
                        dest_photo.title = src_photo.title
                        if src_photo.persons:
                            # add keywords for each person
                            dest_photo.keywords = src_photo.keywords + [
                                f"People/{p}" for p in src_photo.persons
                            ]
                        else:
                            dest_photo.keywords = src_photo.keywords
                        if src_photo.location[0]:
                            dest_photo.location = src_photo.location

                        for album in src_photo.album_info:
                            if album.folder_names:
                                # make_folders silently ignores existing folders (like os.makedirs)
                                verbose_(
                                    f"Adding folder {'/'.join(album.folder_names)}"
                                )
                                folder = dest.make_folders(album.folder_names)
                                dest_album = folder.album(album.title)
                                if not dest_album:
                                    # album doesn't exist
                                    verbose_(f"Creating album: {album.title}")
                                    dest_album = folder.create_album(album.title)
                            else:
                                dest_album = dest.album(album.title)
                                if not dest_album:
                                    dest_album = dest.create_album(album.title)
                            verbose_(
                                f"Adding {dest_photo.filename} to album {album.title}"
                            )
                            dest_album.add([dest_photo])
    if fp is not None:
        fp.close()


if __name__ == "__main__":
    merge()
