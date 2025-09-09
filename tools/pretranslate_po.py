# Copyright (c) 2025-present, PotterWhite (themanuknowwhom@outlook.com).
# All rights reserved.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.
#
# T-HEAD-GR-V0.3.0-20250907
# pretranslate_po.py

import os
import argparse
import polib
import shutil
import time
from googletrans import Translator, LANGUAGES

# A small helper to make console output colorful
class colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def pretranslate_po_file(input_path, output_path, target_lang='zh-cn'):
    """
    Automatically translates untranslated entries in a .po file using Google Translate.

    Args:
        input_path (str): Path to the source .po file.
        output_path (str): Path to save the translated .po file.
        target_lang (str): The target language code (e.g., 'zh-cn', 'ja', 'fr').
    """
    print(f"{colors.BOLD}Starting pre-translation process...{colors.ENDC}")
    print(f"  - Source file: {input_path}")
    print(f"  - Output file: {output_path}")
    print(f"  - Target language: {target_lang}\n")

    try:
        po = polib.pofile(input_path, encoding='utf-8')
    except Exception as e:
        print(f"{colors.FAIL}Error: Could not read the source file '{input_path}'.{colors.ENDC}")
        print(f"Details: {e}")
        return

    untranslated_entries = [e for e in po if not e.msgstr and not e.obsolete]

    if not untranslated_entries:
        print(f"{colors.OKGREEN}All entries are already translated. No action needed.{colors.ENDC}")
        # If no translation is needed, we can just copy the file
        shutil.copy(input_path, output_path)
        print(f"Source file copied to '{output_path}'.")
        return

    print(f"Found {colors.WARNING}{len(untranslated_entries)}{colors.ENDC} untranslated entries. Initializing translator...")

    try:
        translator = Translator()
    except Exception as e:
        print(f"{colors.FAIL}Error: Failed to initialize the translator.{colors.ENDC}")
        print("Please check your internet connection and if the 'googletrans' library is installed correctly.")
        print(f"Details: {e}")
        return

    for i, entry in enumerate(untranslated_entries):
        try:
            # Add a small delay to avoid hitting API rate limits
            time.sleep(0.5)

            translation = translator.translate(entry.msgid, dest=target_lang)
            entry.msgstr = translation.text

            # Use \r to show progress on the same line
            progress = f"[{i+1}/{len(untranslated_entries)}]"
            print(f"\r{colors.OKGREEN}Translating...{colors.ENDC} {progress} \"{entry.msgid[:30]}...\" -> \"{entry.msgstr[:30]}...\"", end="")

        except Exception as e:
            print(f"\n{colors.FAIL}Warning: Could not translate '{entry.msgid}'. Skipping. Error: {e}{colors.ENDC}")
            entry.msgstr = "" # Keep it empty if translation fails

    print(f"\n\n{colors.OKGREEN}{colors.BOLD}Pre-translation complete!{colors.ENDC}")

    try:
        po.save(output_path)
        print(f"Translated file successfully saved to: {colors.BOLD}{output_path}{colors.ENDC}")
        print("Next steps: \n  1. Review the generated .po file for accuracy.\n  2. Run 'python tests/manage.py compilemessages'.")
    except Exception as e:
        print(f"{colors.FAIL}Error: Could not save the output file to '{output_path}'.{colors.ENDC}")
        print(f"Details: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="A tool to automatically pre-translate Django .po files using Google Translate.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "po_file_path",
        type=str,
        help="The path to the source .po file you want to translate."
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        help="Optional: The path for the output translated file.\n"
             "If not provided, it defaults to '<original_name>.translated.po'."
    )
    parser.add_argument(
        "-l", "--lang",
        type=str,
        default='zh-cn',
        help=f"Optional: The target language code.\n"
             f"Default is 'zh-cn' (Simplified Chinese).\n"
             f"Available codes include: {list(LANGUAGES.keys())[:5]}..."
    )

    args = parser.parse_args()

    # Determine the output path if not provided
    output_file = args.output
    if not output_file:
        base, ext = os.path.splitext(args.po_file_path)
        output_file = f"{base}.translated{ext}"

    pretranslate_po_file(args.po_file_path, output_file, args.lang)
