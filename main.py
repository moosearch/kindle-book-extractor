import time
import os
from pathlib import Path
import argparse 

# pywin32 libraries.
import win32gui
import win32con
import win32process

import pyautogui
import psutil
from PIL import ImageGrab, ImageChops, ImageStat
import img2pdf

import ctypes
ctypes.windll.user32.SetProcessDPIAware()

# Example is "[Kindle owner name]'s Kindle for PC - [Name of book]"
# eg. Wesley's Kindle for PC - Her Dark Silence: Small Town Murder Mystery Romance
# The script will do a (case-insensitive) substring wildcard search 
NAME_OF_APP_STUB = "Kindle for PC" 
DEFAULT_SCREENSHOT_TARGET_DIR = "c:/temp/kindle_page_screenshots"
DEFAULT_BOOK_MARGIN = 0.33203125 # Represents the margin percentage for book border between 0 and 1. The higher the value, the larger the margin.
DEFAULT_PDF_FILEPATH = "./Output.pdf"
DEFAULT_SCREENSHOT_NUM_LIMIT = 1000000 # At some point, we should be terminating the program if it goes beyond a certain number of screen shots. Each screenshot may not necessarily correspond to a singular page.

FULL_SCREEN_PAUSE_SEC = 5 # Need a delay to wait for the "Press F11 to exit screen"

def get_available_filename(base_path):
    """
    Given a Path object like Path("output.pdf"), return a Path
    that doesn't exist by appending _1, _2, ... if needed.
    """
    base_path = Path(base_path)
    if not base_path.exists():
        return base_path

    # Split stem and suffix
    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent

    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_path = parent / new_name
        if not new_path.exists():
            return new_path
        counter += 1

def generate_pdf(target_dir, output_path):
    """
    Generate a PDF from all PNG images in a target directory.

    This function scans the specified directory for PNG files,
    sorts them alphabetically, and combines them into a single
    PDF saved at the given output path.

    Parameters
    ----------
    target_dir: Path to the directory containing PNG images.
    output_path: Path (including filename) where the resulting PDF will be saved.

    Notes
    -----
    - Only files ending with ".png" are included.
    - Files are combined in **alphabetical order**, so make sure
      filenames are named to reflect the desired order (e.g., zero-padded).
    - Existing directories in the target_dir are ignored.
    """

    imgs = []
    for fname in os.listdir(target_dir):
        if not fname.endswith(".png"):
            continue
        path = os.path.join(target_dir, fname)
        if os.path.isdir(path):
            continue
        imgs.append(path)

    with open(output_path, "wb") as f:
        f.write(img2pdf.convert(imgs))

    print(f"PDF saved as {output_path}")


def images_are_similar(img1, img2, threshold=2.0):
    diff = ImageChops.difference(img1, img2)
    stat = ImageStat.Stat(diff)
    return sum(stat.mean) < threshold

def calculate_client_screen_dim(handler):

    rect = win32gui.GetClientRect(handler)  # returns (0,0,width,height)

    # client coordinates
    left, top = win32gui.ClientToScreen(handler, (0,0))
    right, bottom = win32gui.ClientToScreen(handler, (rect[2], rect[3]))
    screen_dimensions = (left, top, right, bottom)

    return screen_dimensions

def calculate_crop(screen_dimensions: tuple, book_margin: float = DEFAULT_BOOK_MARGIN) -> tuple:
    """
    
    tuple: left, top, right, bottom
    """

    # These dimensions represent the dimensions of the current window.
    left = screen_dimensions[0]
    top = screen_dimensions[1]
    right = screen_dimensions[2]
    bottom = screen_dimensions[3]

    horizontal_length = right - left
    margin_size = horizontal_length * book_margin
    left_new = left + margin_size
    right_new = right - margin_size

    cropped_dim = (left_new, top, right_new, bottom)

    return cropped_dim

def take_screenshots(handler: int, target_dir: str, page_name: str=None, page_limit: int=DEFAULT_SCREENSHOT_NUM_LIMIT) -> None:
    """Takes the screenshots of the book and publishes them to a directory.
    
    handler: The value of the windows handler.
    target_dir: The directory to publish the screen shots to.

    returns: None
    """

    # Since we don't have access to the Kindle desktop software internals, we have to compare the n-th screenshot versus the (n+1)th screenshot to check if they're the same.

    found_same_page = False

    counter = 0
    
    previous_image = None
    page_name_base = "page" if page_name is None else page_name


    #pyautogui.press("f11")
    time.sleep(1)

    while not found_same_page and counter < page_limit:

        # Screenshot
        #left, top, right, bottom = win32gui.GetWindowRect(handler)
        rect = win32gui.GetClientRect(handler)  # returns (0,0,width,height)
        screen_dimensions = calculate_client_screen_dim(handler)

        if not screen_dimensions == rect:
            print(f"Kindle not in full screen mode... Turning into full screen mode. The program will continue after {FULL_SCREEN_PAUSE_SEC} seconds. Please refrain from touching until the program is finished.")
            pyautogui.press("f11")
            time.sleep(FULL_SCREEN_PAUSE_SEC)

            ctypes.windll.user32.SetProcessDPIAware()
            left, top, right, bottom = calculate_client_screen_dim(handler)
            screen_dimensions = calculate_client_screen_dim(handler)

        cropped_dimensions = calculate_crop(screen_dimensions)
        page_name = f"{page_name_base}_{counter:07}.png"
        page_target_file_path = f"{target_dir}/{page_name}"
        
        force_foreground(handler)

        img = ImageGrab.grab(cropped_dimensions)

        print(f"Saving page {page_name}")
        with open(page_target_file_path,'wb') as f:
            img.save(f)

        # do comparison so we can set flag.
        if previous_image is not None:
            b = images_are_similar(previous_image, img)

            if b:
                found_same_page = True

        previous_image = img

        # Page turn
        pyautogui.press("right")
        counter += 1

        


def process_name_from_handler(handler):
    """Helper method for getting the associated process with the handle."""
    _, pid = win32process.GetWindowThreadProcessId(handler)
    return psutil.Process(pid).name()

def force_foreground(handler):
    if not win32gui.IsWindow(handler):
        raise RuntimeError("Invalid handler")

    # Restore window if minimized
    win32gui.ShowWindow(handler, win32con.SW_RESTORE)

    foreground = win32gui.GetForegroundWindow()

    # If already foreground, nothing to do
    if handler == foreground:
        return

    fg_thread, _ = win32process.GetWindowThreadProcessId(foreground)
    target_thread, _ = win32process.GetWindowThreadProcessId(handler)

    # Temporarily attach threads
    win32process.AttachThreadInput(fg_thread, target_thread, True)
    try:
        win32gui.SetForegroundWindow(handler)
        win32gui.BringWindowToTop(handler)
    finally:
        win32process.AttachThreadInput(fg_thread, target_thread, False)

    time.sleep(0.1)  # allow focus to settle

def find_kindle_handler():
    """Finds the kindle program handler with the windows API."""
    result = []
    def enum(handler, _):
        #
        ps_name = process_name_from_handler(handler)

        #print(f"Process Name: {ps_name} (Handler: {handler})")

        is_window_visible = win32gui.IsWindowVisible(handler)
        window_text = win32gui.GetWindowText(handler)

        is_process_kindle = NAME_OF_APP_STUB.lower() in window_text.lower()
        
        if is_window_visible and is_process_kindle:
            result.append({
                'handler' : handler
                ,'windowName' : window_text
            })

        return(None)

    win32gui.EnumWindows(enum, None)
    return result[0] if result else None

def main():

    formattedArgs = handle_arguments()

    handler_info = find_kindle_handler()
    if not handler_info:
        raise RuntimeError("Kindle not found")

    #win32gui.ShowWindow(handler, win32con.SW_RESTORE)
    handler = handler_info['handler']
    kindle_app_name = handler_info['windowName']
    force_foreground(handler)

    cur_handler = win32gui.GetForegroundWindow()
    if cur_handler != handler:
        raise ValueError(f"Current handler (cur_handler) does not match the target handler: {handler}")
        
    time.sleep(0.3)

    screenshotDir = formattedArgs['screenshotDir']
    page_limit = formattedArgs['screenshotNumLimit']
    if not os.path.exists(screenshotDir):
        os.makedirs(screenshotDir)
    take_screenshots(handler=handler, target_dir=screenshotDir, page_limit=page_limit)

    # use current working directory for pdf output
    pdfPath = formattedArgs['pdfOutputFilePath']
    available_pdf_path = get_available_filename(base_path=pdfPath)

    print(f"Generating PDF at {available_pdf_path}...")

    generate_pdf(target_dir=screenshotDir, output_path=available_pdf_path)

def handle_arguments():

    parser = argparse.ArgumentParser(description="Take screenshots of Kindle books and compile into a PDF.")

    parser.add_argument(
        "--output-dir",
        type=str,
        help=f"Directory where screenshots will be saved. "
    )

    parser.add_argument(
        "--book-margin",
        type=float,
        help=f"Margin percentage for book border (0 to 1). Higher values increase margin. "
    )

    parser.add_argument(
        "--pdf-file",
        type=str,
        help=f"Filepath for the final compiled PDF. "
    )

    parser.add_argument(
        "--screenshot-limit",
        type=int,
        help=f"Maximum number of screenshots to take before terminating. "
    )

    args = parser.parse_args()

    formattedArgs = {

    }
    # Update globals if arguments are provided
    formattedArgs['screenshotDir'] = args.output_dir or DEFAULT_SCREENSHOT_TARGET_DIR
    formattedArgs['pageMargins'] = args.book_margin or DEFAULT_BOOK_MARGIN
    formattedArgs['pdfOutputFilePath'] = args.pdf_file or DEFAULT_PDF_FILEPATH
    formattedArgs['screenshotNumLimit'] = args.screenshot_limit or DEFAULT_SCREENSHOT_NUM_LIMIT

    print(f"Screenshots will be saved in {formattedArgs['screenshotDir']}")

    return(formattedArgs)

if __name__ == '__main__':
    print("Start of Kindle book page extraction program. ")
    print("Ensure that you have a book opened at the cover page in the Kindle for PC desktop application.")

    main()

    print("End of Kindle book page extraction program. ")