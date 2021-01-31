# Merge Photos Libraries

This is a temporary repository for collaborating on "merge libraries" command for [osxphotos](https://github.com/RhetTbull/osxphotos).

If the merge command can be successfully implemented, this code will be added to osxphotos.

## ToDo

- [x] Merge libraries
- [x] Basic tests
- [x] Favorite
- [x] Description
- [x] Title
- [x] Keywords
- [x] RAW+JPEG import
- [x] Live Photos
- [x] Albums and folders
- [x] Dry-run mode (don't actually import)
- [x] Preserve state so merge can be re-started
- [ ] Adjustments/Edits
- [ ] Persons
- [ ] Face regions (see [osxphotos discussion](https://github.com/RhetTbull/osxphotos/discussions/356))

## Testing

There is a basic test suite for Catalina. Not yet implemented for Big Sur.  The test suite requires pytest and requires user interaction to run in order to copy test libraries and tell Photos to switch libraries.