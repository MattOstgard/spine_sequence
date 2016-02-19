# spine_sequence.py
Add an image sequence to an Esoteric Spine skeleton.

#Installation and Usage
[![IMAGE ALT TEXT HERE](http://img.youtube.com/vi/c9-UdM7oHKg/1.jpg)](http://www.youtube.com/watch?v=c9-UdM7oHKg)
- Requires Python 2.7 or above. Mac users have this installed by default. Windows users will have to download: https://www.python.org/downloads/
- Usage (same as --help argument):
```
spine_sequence.py [-h] --output JSON_FILE --images WILDCARD_PATH
                 [--images_root FOLDER_PATH] [--merge SPINE_JSON_FILE]
                 [--bone NAME] [--framerate NUMBER]

Creates a spine .json file from an image sequence.

optional arguments:
  -h, --help            show this help message and exit
  --output JSON_FILE    Output .json file: Example: "my_image_sequence.json"
  --images WILDCARD_PATH
                        Wildcard path to image sequence. This is relative to
                        --images_root_path. Example: "my_images/*.png"
  --images_root FOLDER_PATH
                        (Optional, default is current folder)The root path
                        used in spine for images. Example: "assets/images/"
  --merge SPINE_JSON_FILE
                        (Optional) Spine skeleton to add image sequence to. If
                        not supplied it will be added to an empty spine
                        skeleton. Example: "my_existing_skeleton.json"
  --bone NAME           (Optional, default is "root") Bone name to attach to.
                        Example: "my_bone"
  --framerate NUMBER    (Optional, default is 30) Framerate to animate at.
```
