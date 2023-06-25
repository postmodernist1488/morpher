#!/usr/bin/env python3

from PIL import Image, ImageDraw
import numpy as np
import sys
from sys import argv
from os import makedirs
from os.path import isdir, isfile

BLANK = np.array((0, 0, 0, 0))

from enum import Enum, auto
class Format(Enum):
    PNG = auto()
    GIF = auto()
    JPEG = auto()

DEFAULT_DURATION = 7.0
DEFAULT_NFRAMES = 30
DEFAULT_FORMAT = Format.GIF

TEST_LINE = False

def eprint(*args, **kwargs):
    """Print to stderr"""
    print(*args, file=sys.stderr, **kwargs)

def debug_line(line, width, height):
    """Open a debug pyglet window that draws a given line in a window of size width x height."""
    import pyglet 
    from pyglet import shapes

    window = pyglet.window.Window(width, height)
    pyglet.gl.glClearColor(1,1,1,1)

    batch = pyglet.graphics.Batch()

    point = 0
    circles = []

    @window.event
    def on_draw():
        window.clear()
        batch.draw()

    def callback(_):
        nonlocal point
        i, j = line[point]
        circles.append(shapes.Circle(j, window.height - i, 3, color=(0x9f, 0x34, 0xb9), batch=batch))
        point += 1

        if point == len(line):
            pyglet.clock.unschedule(callback)


    pyglet.clock.schedule_interval(callback, 0.01)
    pyglet.app.run()

def find_first(pic):
    """Find the location of the first non-empty pixel searching from top to bottom"""
    for i in range(len(pic)):
        for j in range(len(pic[0])):
            if pic[i][j][3] != 0:
                return (i, j)
    return len(pic), len(pic[0])

def get_line(path):
    """Returns a list of points on an image that make up a line around the border of a monotonous image.
    The 'outside' of the object is expected to have alpha of 0
    """
    original = np.array(Image.open(path))
    height = len(original)
    width = len(original[0])

    col = np.zeros((height, 1, 4), dtype=np.uint8)
    padded = np.hstack((col, original, col))
    width += 2

    row = np.zeros((1, width, 4), dtype=np.uint8)
    padded = np.vstack((row, padded, row))
    height += 2

    first = find_first(padded)
    i, j = first
    color = tuple(padded[i][j])
    prevs = [(height, width)] * 8
    line = []
    while True:
        for i, j in ((i - 1, j), (i - 1, j + 1), (i, j + 1), (i + 1, j + 1), (i + 1, j), (i + 1, j - 1), (i, j - 1), (i - 1, j - 1)):
            if padded[i][j][3] != 0 and any(x == 0 for x in (padded[i - 1][j][3], padded[i][j + 1][3],  padded[i + 1][j][3], padded[i][j - 1][3])) and \
                    (i, j) not in prevs:
                line.append((i, j))
                prevs.pop(0)
                prevs.append((i, j))
                break
        else:
            eprint(f'ERROR: border could not be traced for {path}. Make sure you provided a picture without any holes')
            if TEST_LINE:
                debug_line(line, width, height)
            exit(1)

        if (i, j) == first:
            break

    if TEST_LINE:
        debug_line(line, width, height)

    '''
#inefficient edge detection algorithm
#left to right
    for i in range(height):
        for j in range(1, width):
            if not any(padded[i][j - 1]) and any(padded[i][j]):
                borders[i][j] = BORDER_VALUE
            elif any(padded[i][j - 1]) and not any(padded[i][j]):
                borders[i][j - 1] = BORDER_VALUE

#top to bottom
    for j in range(width):
        for i in range(1, height):
            if not any(padded[i - 1][j]) and any(padded[i][j]):
                borders[i][j] = BORDER_VALUE
            elif any(padded[i - 1][j]) and not any(padded[i][j]):
                borders[i - 1][j] = BORDER_VALUE
    '''
    return line, color, (width, height)

def flood_fill(img, xy, color):
    """Flood fill a PIL image img starting from tuple point xy with a given color"""
    stack = []
    stack.append(xy)
    while stack:
        n = stack.pop()
        x, y = n
        if 0 <= x < img.width and 0 <= y < img.height and img.getpixel(n) == (255, 255, 255, 255):
            img.putpixel(n, color)
            stack.append((x - 1, y))
            stack.append((x + 1, y))
            stack.append((x, y - 1))
            stack.append((x, y + 1))
        

def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolate on the scale given by a to b, using t as the point on that scale."""
    return (1 - t) * a + t * b


def help(program):
    print(f"Usage: {program} FROM TO [OPTION]")
    print("Create morph animation from one closed shape to another.")
    print("For formats other than gif all frames are output.")
    print()
    print("Options:")
    print("-o <path>                            path to the output GIF or an output")
    print("                                       directory for frames for other formats")
    print(f"-n<frames>                           set the number of frames; default is {DEFAULT_NFRAMES}")
    print(f"-d<seconds>, --duration=<seconds>    set the duration of a GIF in secodns; default is {DEFAULT_DURATION}")
    print(f"-f<format>                           set the output format; default is {str(DEFAULT_FORMAT)[7:]}")
    print("-l<times>, --loop<times>              a number of loops for a GIF animation; default is 0 (meaning loop indefinitely)")
    print("-h                                   print this help message and exit")
    exit(0)

def main():

    program = argv.pop(0)

    original_path = ''
    final_path = ''
    output_path = ''
    nframes = DEFAULT_NFRAMES
    duration = DEFAULT_DURATION
    format = DEFAULT_FORMAT
    loop = 0

    while argv:
        arg = argv.pop(0)
        if arg == "-o":
            if len(argv) > 0:
                output_path = argv.pop(0)
            else:
                eprint(f'{program}: error: missing directory name after `-o`')
                exit(1)
        elif arg.startswith("-n"):
            try:
                nframes = int(arg[2:])
                assert nframes > 0
            except (ValueError, AssertionError):
                eprint(f'{program}: error: a positive number of frames should be provided after `-n`')
                exit(1)
        elif arg.startswith("-d"):
            try:
                duration = float(arg[2:])
                assert duration > 0
            except (ValueError, AssertionError):
                eprint(f'{program}: error: a positive duration in seconds should be provided after `-d`')
                exit(1)
        elif arg.startswith("--duration="):
            try:
                duration = float(arg[11:])
                assert duration > 0
            except (ValueError, AssertionError):
                eprint(f'{program}: error: a positive duration in seconds should be provided after `--duration=`')
                exit(1)
        elif arg.startswith("--loop="):
            try:
                loop = int(arg[7:])
                assert loop >= -1
            except (ValueError, AssertionError):
                eprint(f'{program}: error: a valid loop number should be provided after `--loop=`')
                exit(1)
        elif arg.startswith("-l"):
            try:
                loop = int(arg[2:])
                assert loop >= -1
            except (ValueError, AssertionError):
                eprint(f'{program}: error: a valid loop number should be provided after `-l`')
                exit(1)

        elif arg == "--gif":
            format = Format.GIF
        elif arg.startswith('-f'):
            s = arg[2:]
            if s == 'gif': format = Format.GIF
            elif s == 'png': format = Format.PNG
            elif s == 'jpeg': format = Format.JPEG
        elif arg == "-h" or arg == "--help":
            help(program)
        else:
            if original_path:
                final_path = arg
            else:
                original_path = arg

    if not original_path or not final_path:
        eprint(f'{program}: error: no input files')
        exit(1)

    if not output_path:
        if format == Format.GIF:
            output_path = 'res.gif'
        else:
            output_path = 'res'

    if isfile(output_path) and format != Format.GIF:
        eprint(f'{program}: error: `{output_path}` is not a directory')
        exit(1)

    if isdir(output_path) and format == Format.GIF:
        eprint(f'{program}: error: `{output_path}` is a directory')
        exit(1)

    if not isdir(output_path) and format != Format.GIF:
        makedirs(output_path)

    original_line, original_color, original_size = get_line(original_path)
    final_line, final_color, final_size = get_line(final_path)

    pic_width = max(original_size[0], final_size[0])
    pic_height = max(original_size[1], final_size[1])

# remove one in every `inc` points to make the lengths equal
    a = max(original_line, final_line, key=len)
    b = min(original_line, final_line, key=len)
    while len(a) != len(b):
        inc = len(a) / (len(a) - len(b))
        i = 0.0
        while i < len(a):             
            del a[int(i)]
            if len(a) == len(b):
                break
            i += inc

# interpolate between original_line and final_line

    frames = []
    for t in np.linspace(0.0, 1.0, nframes):
        interpolated = []
        for (i0, j0), (i1, j1) in zip(original_line, final_line):
            interpolated.append((int(lerp(j0, j1, t)), int(lerp(i0, i1, t))))
        
        img = Image.new("RGBA", (pic_width, pic_height), (255, 255, 255, 255))
        draw = ImageDraw.Draw(img)
        color = (int(lerp(original_color[0], final_color[0], t)),
                 int(lerp(original_color[1], final_color[1], t)),
                 int(lerp(original_color[2], final_color[2], t)),
                 255)

        for i in range(len(interpolated) - 1):
            draw.line(interpolated[i - 1] + interpolated[i], fill=color, width=1)
        draw.line(interpolated[-1] + interpolated[0], fill=color, width=1)
        flood_fill(img, (interpolated[0][0], interpolated[0][1] + 5), color)
        frames.append(img)

    if format == Format.GIF:
        frames[0].save(f'{output_path}',
               save_all=True, append_images=frames[1:], optimize=True, duration=duration * 1000.0 / nframes, loop=loop)
    elif format == Format.PNG:
        for i, frame in enumerate(frames):
            frame.save(f'{output_path}/{i + 1}.png')
    elif format == Format.JPEG:
        for i, frame in enumerate(frames):
            frame.convert("RGB").save(f'{output_path}/{i + 1}.jpeg')
    else:
        eprint('unsupported format')
        eprint(f'{program}: error: unsupported format `{format}`')
        exit(1)

    

if __name__ == "__main__":
    main()
