#!python3
'''Create a font header file for epdiy from a TTF font file.
You can import unicode_intervals.txt with a list of unicode ranges to include in the font.
The format is CSV, one line per range
'''

import freetype
import zlib
import sys
import re
import math
import argparse
from collections import namedtuple

parser = argparse.ArgumentParser(
    description="Generate a header file from a font to be used with epdiy."
)
parser.add_argument("name", action="store", help="name of the font.")
parser.add_argument("size", type=int, help="font size to use.")
parser.add_argument(
    "fontstack",
    action="store",
    nargs="+",
    help="list of font files, ordered by descending priority.",
)
parser.add_argument(
    "--compress", dest="compress", action="store_true", help="compress glyph bitmaps."
)
parser.add_argument(
    "--unicode_intervals_file", type=str, default="", help="Text file with unicode intervals, CSV, one line per range."
)

args = parser.parse_args()


GlyphProps = namedtuple(
    "GlyphProps",
    [
        "width",
        "height",
        "advance_x",
        "left",
        "top",
        "compressed_size",
        "data_offset",
        "code_point",
    ],
)

font_stack = [freetype.Face(f) for f in args.fontstack]
compress = args.compress
size = args.size
font_name = args.name

# inclusive unicode code point intervals
# must not overlap and be in ascending order
intervals = [
    (32, 126),  # basic latin
    # (160, 255),
    # (0x2500, 0x259F),
    # (0x2700, 0x27BF),
    # # powerline symbols
    # (0xE0A0, 0xE0A2),
    # (0xE0B0, 0xE0B3),
    # (0x1F600, 0x1F680),
]


if args.unicode_intervals_file:
    with open(args.unicode_intervals_file, "r", encoding="utf-8") as f:
        for line in f.readlines():
            parts = line.strip().split(",")
            if len(parts) != 2:
                print(f"Invalid line in unicode intervals file: {line}", file=sys.stderr)
                continue
            intervals.append(
                (
                    int(parts[0]),
                    int(parts[1]),
                )
            )


def norm_floor(val):
    return int(math.floor(val / (1 << 6)))


def norm_ceil(val):
    return int(math.ceil(val / (1 << 6)))


for face in font_stack:
    # shift by 6 bytes, because sizes are given as 6-bit fractions
    # the display has about 150 dpi.
    face.set_char_size(size << 6, size << 6, 150, 150)


def chunks(l, n):
    for i in range(0, len(l), n):
        yield l[i : i + n]


total_size = 0
total_packed = 0
all_glyphs = []


def load_glyph(code_point):
    face_index = 0
    while face_index < len(font_stack):
        face = font_stack[face_index]
        glyph_index = face.get_char_index(code_point)
        if glyph_index > 0:
            face.load_glyph(glyph_index, freetype.FT_LOAD_RENDER)
            return face
            break
        face_index += 1
        print(
            f"falling back to font {face_index} for {chr(code_point)}.", file=sys.stderr
        )
    raise ValueError(f"code point {code_point} not found in font stack!")


for i_start, i_end in intervals:
    for code_point in range(i_start, i_end + 1):
        face = load_glyph(code_point)
        bitmap = face.glyph.bitmap
        pixels = []
        px = 0
        for i, v in enumerate(bitmap.buffer):
            y = i / bitmap.width
            x = i % bitmap.width
            if x % 2 == 0:
                px = v >> 4
            else:
                px = px | (v & 0xF0)
                pixels.append(px)
                px = 0
            # eol
            if x == bitmap.width - 1 and bitmap.width % 2 > 0:
                pixels.append(px)
                px = 0

        packed = bytes(pixels)
        total_packed += len(packed)
        compressed = packed
        if compress:
            compressed = zlib.compress(packed)

        glyph = GlyphProps(
            width=bitmap.width,
            height=bitmap.rows,
            advance_x=norm_floor(face.glyph.advance.x),
            left=face.glyph.bitmap_left,
            top=face.glyph.bitmap_top,
            compressed_size=len(compressed),
            data_offset=total_size,
            code_point=code_point,
        )
        total_size += len(compressed)
        all_glyphs.append((glyph, compressed))

# pipe seems to be a good heuristic for the "real" descender
face = load_glyph(ord("|"))

glyph_data = []
glyph_props = []
for index, glyph in enumerate(all_glyphs):
    props, compressed = glyph
    glyph_data.extend([b for b in compressed])
    glyph_props.append(props)

print("total", total_packed, file=sys.stderr)
print("compressed", total_size, file=sys.stderr)



with open(f"{font_name}.h", "w", encoding="utf-8") as f:
    f.write("#pragma once\n")
    f.write('#include "epd_driver.h"\n')
    f.write(f"const uint8_t {font_name}Bitmaps[{len(glyph_data)}] = {{\n")
    for c in chunks(glyph_data, 16):
        f.write("    " + " ".join(f"0x{b:02X}," for b in c))
        f.write("\n")
    f.write("};\n")

    f.write(f"const GFXglyph {font_name}Glyphs[] = {{\n")
    for i, g in enumerate(glyph_props):
        line = "    { " + ", ".join([f"{a}" for a in list(g[:-1])])
        line += "},"
        line += f"// {chr(g.code_point) if g.code_point != 92 else '<backslash>'}"
        f.write(line)
        f.write("\n")
    f.write("};\n")

    f.write(f"const UnicodeInterval {font_name}Intervals[] = {{\n")
    offset = 0
    for i_start, i_end in intervals:
        f.write(f"    {{ 0x{i_start:X}, 0x{i_end:X}, 0x{offset:X} }},")
        offset += i_end - i_start + 1
        f.write("\n")
    f.write("};\n")

    f.write(f"const GFXfont {font_name} = {{\n")
    f.write(f"    (uint8_t*){font_name}Bitmaps,\n")
    f.write(f"    (GFXglyph*){font_name}Glyphs,\n")
    f.write(f"    (UnicodeInterval*){font_name}Intervals,\n")
    f.write(f"    {len(intervals)},\n")
    f.write(f"    {1 if compress else 0},\n")
    f.write(f"    {norm_ceil(face.size.height)},\n")
    f.write(f"    {norm_ceil(face.size.ascender)},\n")
    f.write(f"    {norm_floor(face.size.descender)},\n")
    f.write("};\n")
