'''Create unicode_intervals.txt for fontconvert.py'''
import freetype, sys
import argparse


def main(font_filename: str, output_filename: str, *, start_from: int = -1, end_at: int = -1, word_list: list[str] = []):

    font_face: freetype.Face = freetype.Face(font_filename)
    sorted_chars:list[str] = sorted([chr(c) for c, g in font_face.get_chars() if c])

    
    number_of_characters:int = len(sorted_chars)
    number_of_outputed_characters:int = 0

    print(f"Number of characters in word_list: {len(word_list)}")
    print(f"Number of characters in {font_filename}: {number_of_characters}")

    with open(output_filename, "w", encoding="utf-8") as f:

        last_char:str|None = None
        first_char:str|None = None
        for each_char in sorted_chars:
            # skip
            if start_from != -1:
                if ord(each_char) < start_from:
                    continue
            if end_at != -1:
                if ord(each_char) > end_at:
                    break
            if word_list and each_char not in word_list:
                continue
            
            # f.write(f"{each_char}: {ord(each_char):04X},{ord(each_char):d}\n")
            if not first_char:
                first_char = each_char
                last_char = each_char
            elif (ord(each_char) - ord(last_char)) > 1:
                # finish a range
                f.write(f"{ord(first_char)},{ord(last_char)}\n")

                first_char = each_char
                last_char = each_char
            else:
                last_char = each_char

            number_of_outputed_characters += 1

        # finish the last range
        if first_char is not None and last_char is not None:
            f.write(f"{ord(first_char)},{ord(last_char)}\n")
            number_of_outputed_characters += 1

    print(f"Number of characters included in {output_filename}: {number_of_outputed_characters}")



if __name__ == "__main__":
    parser:argparse.ArgumentParser = argparse.ArgumentParser(description="Generate a list of characters from a font file.")
    parser.add_argument("font", type=str, help="Path to the font file")
    parser.add_argument("--word_list", type=str, help="Wordlist file to filter characters")
    parser.add_argument("--output", type=str, default="unicode_intervals.txt", help="Output file name")
    parser.add_argument("--start_from", type=int, default=-1, help="Start from this unicode value")
    parser.add_argument("--end_at", type=int, default=-1, help="End at this unicode value")

    args: argparse.Namespace = parser.parse_args()

    font_filename: str = args.font
    output_filename: str = args.output
    start_from: int = args.start_from
    end_at: int = args.end_at
    word_list: list[str] = []
    if args.word_list:
        with open(args.word_list, "r", encoding="utf-8") as f:
            word_list = [word for word in f.read().replace("\n", "").replace("\r", "").replace(" ", "")[:]]

    main(font_filename, output_filename, start_from=start_from, end_at=end_at, word_list=word_list)


