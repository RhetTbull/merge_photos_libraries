"""Database to track merge progress"""

# implemented as a JSON flat-file with TinyDB

import pathlib

from tinydb import Query, TinyDB
from tinydb.storages import MemoryStorage

from osxphotos.utils import noop


class MergeDB:
    """Database to checkpoint merge progress """

    def __init__(self, dbpath, source_library, destination_library, verbose=None):
        if type(dbpath) != pathlib.Path:
            dbpath = pathlib.Path(dbpath)
        self._dbpath = dbpath
        self.verbose = verbose or noop
        if not source_library or not destination_library:
            raise ValueError("source_library and dest_library must be set")
        self._source = str(source_library)
        self._dest = str(destination_library)
        self._db = self._open_db(dbpath) if dbpath.exists else self._create_db(dbpath)

    def _open_db(self, dbpath):
        self.verbose(f"Opening merge database: '{dbpath}'")
        return TinyDB(dbpath)

    def _create_db(self, dbpath):
        self.verbose(f"Creating merge database: '{dbpath}'")
        return TinyDB(dbpath)

    def insert(self, record):
        """Insert a record into merge database """
        if not isinstance(record, dict):
            raise ValueError("record must be a dict")
        record["src"] = self._source
        record["dest"] = self._dest
        self._db.insert(record)

    def update(self, record):
        """Update record that matches record["src_uuid"] """
        uuid = record["src_uuid"]
        Record = Query()
        return self._db.update(
            record,
            (Record.src_uuid == uuid)
            & (Record.src == self._source)
            & (Record.dest == self._dest),
        )

    def upsert(self, record):
        """Update or insert record that matches record["src_uuid"] """
        uuid = record["src_uuid"]
        record["src"] = self._source
        record["dest"] = self._dest
        Record = Query()
        return self._db.upsert(
            record,
            (Record.src_uuid == uuid)
            & (Record.src == self._source)
            & (Record.dest == self._dest),
        )

    def get(self, uuid, imported=None):
        """Get a record by source uuid """
        Record = Query()
        if imported is not None:
            return self._db.search(
                (Record.src_uuid == uuid)
                & (Record.src == self._source)
                & (Record.dest == self._dest)
                & (Record.imported == imported)
            )
        else:
            return self._db.search(
                (Record.src_uuid == uuid)
                & (Record.src == self._source)
                & (Record.dest == self._dest)
            )


class MergeDBInMemory(MergeDB):
    """Database to checkpoint merge progress, in memory only """

    def _open_db(self, dbpath):
        self.verbose(f"Opening merge database: '{dbpath}'")
        # copy the existing database into memory
        db = TinyDB(dbpath)
        db_ram = TinyDB(storage=MemoryStorage)
        db_ram.insert_multiple(db.all())
        return db_ram

    def _create_db(self, dbpath):
        self.verbose(f"Creating merge database: '{dbpath}'")
        return TinyDB(storage=MemoryStorage)
