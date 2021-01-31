"""Generate test data for merge_photos_libraries """

import json
import pathlib

import osxphotos


def generate_test_data():
    photosdb = osxphotos.PhotosDB()
    photos = photosdb.photos()
    records = {}
    for p in photos:
        filestem = pathlib.Path(p.original_filename).stem
        folder_albums = p.render_template("{folder_album,}")
        folder_albums = folder_albums[0] if folder_albums[0][0] != "" else []
        record = {
            "uuid": p.uuid,
            "filestem": filestem,
            "original_filename": p.original_filename,
            "keywords": p.keywords,
            "title": p.title,
            "description": p.description,
            "favorite": p.favorite,
            "folder_albums": folder_albums,
            "live_photo": p.live_photo,
            "has_raw": p.has_raw,
            "hasadjustments": p.hasadjustments,
            "persons": p.persons,
            "faces": [f.asdict() for f in p.face_info],
            "isphoto": p.isphoto,
            "ismovie": p.ismovie,
            "burst": p.burst,
        }
        records[filestem] = record
    print(json.dumps(records))


if __name__ == "__main__":
    generate_test_data()
