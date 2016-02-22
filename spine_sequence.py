#!/usr/bin/env python3

import os
import json
from collections import OrderedDict
from glob import glob


def main():
    # Import extra modules
    import argparse
    import struct
    import imghdr
    

    # Extra function to get image sizes
    def get_image_size(fname):
        '''Determine the image type of fhandle and return its size.
        from draco'''
        with open(fname, 'rb') as fhandle:
            head = fhandle.read(24)
            if len(head) != 24:
                return
            if imghdr.what(fname) == 'png':
                check = struct.unpack('>i', head[4:8])[0]
                if check != 0x0d0a1a0a:
                    return
                width, height = struct.unpack('>ii', head[16:24])
            elif imghdr.what(fname) == 'gif':
                width, height = struct.unpack('<HH', head[6:10])
            elif imghdr.what(fname) == 'jpeg':
                try:
                    fhandle.seek(0) # Read 0xff next
                    size = 2
                    ftype = 0
                    while not 0xc0 <= ftype <= 0xcf:
                        fhandle.seek(size, 1)
                        byte = fhandle.read(1)
                        while ord(byte) == 0xff:
                            byte = fhandle.read(1)
                        ftype = ord(byte)
                        size = struct.unpack('>H', fhandle.read(2))[0] - 2
                    # We are at a SOFn block
                    fhandle.seek(1, 1)  # Skip `precision' byte.
                    height, width = struct.unpack('>HH', fhandle.read(4))
                except Exception: #IGNORE:W0703
                    return
            else:
                return
            return width, height

    
    # Process arguments
    parser = argparse.ArgumentParser(description='Creates a spine .json file from an image sequence.')
    
    parser.add_argument('--output', metavar='JSON_FILE', required=True,
        help='Output .json file: Example: "my_image_sequence.json"'
    )
    
    parser.add_argument('--images', metavar='WILDCARD_PATH', required=True, nargs='+',
        help='Wildcard path to image sequence. This is relative to --images_root_path. Example: "my_images/*.png"'
    )
    
    parser.add_argument('--images_root', metavar='FOLDER_PATH', default='',
        help='(Optional, default is current folder)The root path used in spine for images. Example: "assets/images/"'
    )
    
    parser.add_argument('--merge', metavar='SPINE_JSON_FILE',
        help='(Optional) Spine skeleton to add image sequence to. If not supplied it will be added to an empty spine '
        'skeleton. Example: "my_existing_skeleton.json"'
    )
    
    parser.add_argument('--bone', metavar='NAME', default='root',
        help='(Optional, default is "root") Bone name to attach to. Example: "my_bone"'
    )
    
    parser.add_argument('--framerate', metavar='NUMBER', default=30, type=float,
        help='(Optional, default is 30) Framerate to animate at.'
    )
    
    args = parser.parse_args()


    # Print a new line for sanity
    print()

    # Get images from wildcard argument
    globbed_paths = []
    for glob_pattern in args.images:
        glob_pattern = os.path.join(args.images_root, glob_pattern)
        globbed_paths += glob(glob_pattern)
    
    # Make image paths relative to image root
    image_paths = []
    for path in globbed_paths:
        image_paths.append(os.path.relpath(path, args.images_root))

    if len(image_paths) == 0:
        print(' - No images to process!')
        print('No images found in supplied path.')
        print('Please verify --images and --images_root arguments are correct.\n')
        return False

    # Get first image's width and height
    width, height = get_image_size(globbed_paths[0])

    # Full images path
    print(' - {} images found.'.format(len(image_paths)))

    # Do the actual work
    spineSeq = SpineSequence(image_paths, width, height, args.merge, args.bone, args.framerate)

    # Save the new json file
    with open(args.output, 'w') as outfile:
        json.dump(spineSeq.skel, outfile, indent=4)

    # Goodbye!
    print(' - Saved new json file: {}\n'.format(args.output))



class SpineSequence:
    json_root_sort_order = ['skeleton', 'bones', 'slots', 'skins', 'events', 'animations']
    empty_spine_skeleton_string = (
        '{'
        '"skeleton": { "hash": "AnNGCgm1KE26nDxUu2R4xqNyrKs", "spine": "3.0.10", "width": 0, "height": 0 },'
        '"bones": ['
        '    { "name": "root" }'
        '],'
        '"animations": {'
        '    "animation": {}'
        '}'
        '}'
    )
    
    def __init__(self, image_paths, width, height, skeleton_path=None, bone_name='root', framerate=30,
        anim_name='animation'):
        # type: (image_paths:str, width:int, height:int, skeleton_path:str, bone_name:str, framerate:int, anim_name:str) -> None

        # Get skeleton dict from json file
        if skeleton_path:
            with open(skeleton_path) as f:
                self.skel = json.load(f, object_pairs_hook=OrderedDict)
        else:
            self.skel = json.loads(self.empty_spine_skeleton_string)


        # Verify there is a bone to attach to
        if not self.has_bone(bone_name):
            raise LookupError('Cannot find bone_name "{}" in skeleton "{}".\n'.format(bone_name, skeleton_path))


        # Set width and height of document
        if width > self.skel['skeleton']['width']:
            self.skel['skeleton']['width'] = width

        if height > self.skel['skeleton']['height']:
            self.skel['skeleton']['height'] = height


        # Ensure we have a slots array
        if not 'slots' in self.skel:
            self.skel['slots'] = []


        # Ensure we have a skins dict
        if not 'skins' in self.skel:
            self.skel['skins'] = OrderedDict()
        
        if not 'default' in self.skel['skins']:
            self.skel['skins']['default'] = OrderedDict()


        # Ensure we have a slots animation dict
        if not 'animations' in self.skel:
            self.skel['animations'] = OrderedDict()
        
        if not anim_name in self.skel['animations']:
            self.skel['animations'][anim_name] = OrderedDict()
        
        if not 'slots' in self.skel['animations'][anim_name]:
            self.skel['animations'][anim_name]['slots'] = OrderedDict()

        
        # Make a unique slot name
        existing_slot_names = []
        for slot in self.skel['slots']:
            existing_slot_names.append(slot['name'])
        
        slot_name = os.path.splitext(image_paths[0])[0].replace('\\', '/')
        unique_slot_name = slot_name
        i = 0
        while unique_slot_name in existing_slot_names:
            i += 1
            unique_slot_name = '{} ({})'.format(slot_name, i)
        slot_name = unique_slot_name
        

        # Add slot
        # { "name": "fancy_slot", "bone": "fancy", "attachment": "fancy_000" }
        slot = OrderedDict()
        slot['name'] = slot_name
        slot['bone'] = bone_name
        slot['attachment'] = os.path.splitext(image_paths[0])[0].replace('\\', '/')
        self.skel['slots'].append(slot)
        

        # Add attachments to slot
        # "fancy_000": { "width": 512, "height": 256 },
        attachments = OrderedDict()
        for image_path in image_paths:
            name = os.path.splitext(image_path)[0].replace('\\', '/')
            attachments[name] = OrderedDict()
            attachments[name]['width'] = width
            attachments[name]['height'] = height
        
        self.skel['skins']['default'][slot_name] = attachments


        # Add frames to animation
        # { "time": 0.0333, "name": "fancy_000" },
        keyframes = []
        count = 0
        for image_path in image_paths:
            keyframe = OrderedDict()
            keyframe['time'] = self.round_time_like_spine((count / framerate))
            keyframe['name'] = os.path.splitext(image_path)[0].replace('\\', '/')
            keyframes.append(keyframe)
            count += 1
        
        self.skel['animations'][anim_name]['slots'][slot_name] = OrderedDict()
        self.skel['animations'][anim_name]['slots'][slot_name]['attachment'] = keyframes

        # Reorder dict so it can be easily diffed against original
        ordered = OrderedDict()
        for key in self.json_root_sort_order:
            if key in self.skel:
                ordered[key] = self.skel[key]
        self.skel = ordered


    def has_bone(self, bone_name):
        for bone in self.skel['bones']:
            if bone_name == bone['name']:
                return True
        return False


    def round_time_like_spine(self, time):
        # Floor to 4 decimal points
        time = int(time * 10000) / 10000.0
        
        # Remove decimals for whole numbers
        if time == int(time):
            time = int(time)

        # 
        return time


if __name__ == '__main__':    
    import time
    start_time = time.time()
    main()
    print('--- {} seconds ---'.format(round(time.time() - start_time, 5)))