import time
import os
from pathlib import Path
import argparse 
import datetime
import pyautogui
import psutil
from PIL import ImageGrab, ImageChops, ImageStat
import img2pdf
import ctypes
import logging

# pywin32 libraries.
import win32gui
import win32con
import win32process
import win32api

# Own modules.
from src.util import setup_logging


ctypes.windll.user32.SetProcessDPIAware()
todayDate = datetime.datetime.now()
LOGGER = setup_logging()

# Find the first FileHandler (if any)
log_file = None
for handler in LOGGER.handlers:
    if isinstance(handler, logging.FileHandler):
        log_file = handler.baseFilename
        break

if log_file:
    LOGGER.info(f"Logging is set up to log at {log_file}")
else:
    LOGGER.info("No file handler attached to the logger")

# Example is "[Kindle owner name]'s Kindle for PC - [Name of book]"
# eg. Wesley's Kindle for PC - Her Dark Silence: Small Town Murder Mystery Romance
# The script will do a (case-insensitive) substring wildcard search 
NAME_OF_APP_STUB = "Kindle for PC" 
DEFAULT_SCREENSHOT_TARGET_DIR = f"./Output/Screenshots/{todayDate.strftime("%Y%m%d_%H%M%S")}"
DEFAULT_BOOK_MARGIN = 0.33203125 # Represents the margin percentage for book border between 0 and 1. The higher the value, the larger the margin.
DEFAULT_PDF_FILEPATH = f"./Output/PDFs/{todayDate.strftime("%Y%m%d_%H%M%S")}_Output.pdf"
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

    LOGGER.info(f"PDF saved as {output_path}")


def images_are_similar(img1, img2, threshold=5.0):
    """Helper method to determine whether images are the same.

    img1: Pillow image object.
    img2: Pillow image object.
    threshold: RMS threshold for similarity. Lower = stricter.

    returns: True if similar, False otherwise.
    """

    if img1.size != img2.size or img1.mode != img2.mode:
        return False  # completely different

    diff = ImageChops.difference(img1, img2)
    stat = ImageStat.Stat(diff)

    # RMS difference over all channels
    rms = sum((x ** 2 for x in stat.mean)) ** 0.5
    return rms < threshold

def calculate_client_screen_dim(handler: int) -> tuple:
    """Calculates the current dimensions of the client screen.

    handler: The handler associated with the process.

    Returns:
        A tuple of the form:
            (x, y, width, height)

        Where:
            (x, y) is the top-left corner of the client area in SCREEN coordinates
            width  is the width of the client area
            height is the height of the client area

        Derived corners:
            top-left     = (x, y)
            top-right    = (x + width, y)
            bottom-left  = (x, y + height)
            bottom-right = (x + width, y + height)
    """
    rect = win32gui.GetClientRect(handler)  # returns (0,0,width,height)

    # client coordinates
    x, y = win32gui.ClientToScreen(handler, (0,0))
    width, height = win32gui.ClientToScreen(handler, (rect[2], rect[3]))
    screen_dimensions = (x, y, width, height)

    return screen_dimensions

def calculate_crop(handler: int, book_margin: float = DEFAULT_BOOK_MARGIN) -> tuple:
    """
    Calculates cropping bounds for the client area in SCREEN coordinates.

    handler:
        Window handle (HWND).

    book_margin:
        Percentage (0 <= z < 1) of total width to crop from BOTH left and right sides.
        Example: 0.30 removes 30% from the left and 30% from the right.

    Returns:
        A tuple of the form:
            (x, y, width, height)

        Where:
            (x, y) is the top-left corner of the CROPPED client area in SCREEN coordinates
            width is the width of the CROPPED client area
            height is the height of the CROPPED client area

        Derived corners:
            top-left     = (x, y)
            top-right    = (x + width, y)
            bottom-left  = (x, y + height)
            bottom-right = (x + width, y + height)

    NOTES:
        We are assuming that only the left and right margins need to be cropped in this method. This does not crop top or bottom margins!
    """

    #
    screen_dimensions = calculate_client_screen_dim(handler)

    # These dimensions represent the dimensions of the current window.
    x = screen_dimensions[0]
    y = screen_dimensions[1]
    width = screen_dimensions[2]
    height = screen_dimensions[3]

    horizontal_length = width
    margin_size = horizontal_length * book_margin

    new_x = x + margin_size
    new_width = x + width - margin_size
    new_height = y + height
    cropped_dim = (new_x, y, new_width, new_height)

    return cropped_dim

def get_monitor_for_window(hwnd):
    """
    Returns the monitor rectangle (left, top, right, bottom) that contains the given window.
    """
    # Get the window rectangle in screen coordinates
    win_rect = win32gui.GetWindowRect(hwnd)
    
    # Find the monitor that contains the window
    monitor = win32api.MonitorFromRect(win_rect, win32con.MONITOR_DEFAULTTONEAREST)
    info = win32api.GetMonitorInfo(monitor)
    
    # Monitor rectangle
    monitor_rect = info['Monitor']  # (left, top, right, bottom)
    return monitor_rect

def is_window_fullscreen_on_its_monitor(hwnd):
    """
    Returns True if the window fills its monitor's work area.
    """
    # Client area in screen coordinates
    x, y, width, height = calculate_client_screen_dim(hwnd)
    
    # Monitor containing the window
    # Coordinates (left, top) represent the top-left corner.
    # Coordinates (right, bottom) represent the bottom-right corner.
    left, top, right, bottom = get_monitor_for_window(hwnd)
    monitor_width = right - left
    monitor_height = bottom - top
    
    # Allow small tolerance for borders/taskbars
    tolerance = 2  # pixels
    return (abs(width - monitor_width) <= tolerance) and (abs(height - monitor_height) <= tolerance)


def take_screenshots(handler: int, target_dir: str, page_name: str=None, page_limit: int=DEFAULT_SCREENSHOT_NUM_LIMIT) -> None:
    """
    Captures screenshots of the Kindle book and saves them to a directory.

    This function works by taking sequential screenshots of the Kindle window and
    comparing each screenshot to the previous one. If two consecutive screenshots
    are sufficiently similar, it assumes the end of the book has been reached.

    Args:
        handler: Window handle (HWND) for the Kindle window.
        target_dir: Directory to save the screenshots.
        page_name: Base name for screenshot files. Defaults to 'page'.
        page_limit: Maximum number of screenshots to take.
    
    Returns:
        None
    """

    # Since we don't have access to the Kindle desktop software internals, we have to compare the n-th screenshot versus the (n+1)th screenshot to check if they're the same.

    found_same_page = False
    previous_image = None
    page_name_base = page_name or "page"
    counter = 0

    while not found_same_page and counter < page_limit:

        # Screenshot

        if not is_window_fullscreen_on_its_monitor(handler):
            LOGGER.info(f"Kindle not in full screen mode. Switching to full screen...") 
            LOGGER.info(f"Screenshotting will start after {FULL_SCREEN_PAUSE_SEC} seconds. Please do not do anything else while this script is running.")
            pyautogui.press("f11")
            for i in range(0, FULL_SCREEN_PAUSE_SEC):
                LOGGER.info(f"{FULL_SCREEN_PAUSE_SEC-i}")
                time.sleep(1)
            LOGGER.info(f"Screenshotting.")

        # Determine the cropping rectangle of the client area
        cropped_dimensions = calculate_crop(handler)

        # Construct the filename for the current page
        page_name = f"{page_name_base}_{counter:07}.png"
        page_target_file_path = f"{target_dir}/{page_name}"
        
        # Ensure Kindle window is in the foreground for accurate screenshots
        force_foreground(handler)

        img = ImageGrab.grab(cropped_dimensions)

        # do comparison so we can set flag.
        if previous_image is not None:
            if images_are_similar(previous_image, img):
                found_same_page = True

        if not found_same_page:
            LOGGER.info(f"Saving page {page_name}")
            with open(page_target_file_path,'wb') as f:
                img.save(f)

        previous_image = img

        # Page turn
        pyautogui.press("right")
        counter += 1

    LOGGER.info("Done taking screenshots. ")

    return None

def process_name_from_handler(handler):
    """Helper method for getting the associated process with the handle."""
    _, pid = win32process.GetWindowThreadProcessId(handler)
    return psutil.Process(pid).name()

def find_kindle_handler():
    """Finds the kindle program handler with the windows API."""
    result = []
    def enum(handler, _):
        #
        ps_name = process_name_from_handler(handler)

        #LOGGER.info(f"Process Name: {ps_name} (Handler: {handler})")

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

def force_foreground(hwnd):
    """Forces the handler application to be at the foreground.
    """

    # Restore first
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)

    # Simulate user input (ALT key)
    win32api.keybd_event(win32con.VK_MENU, 0, 0, 0)    # ALT down
    win32api.keybd_event(win32con.VK_MENU, 0, win32con.KEYEVENTF_KEYUP, 0)  # ALT up

    # Now Windows allows this
    win32gui.SetForegroundWindow(hwnd)

    time.sleep(0.1)  # let focus settle

def main():

    formattedArgs = handle_arguments()

    handler_info = find_kindle_handler()
    if not handler_info:
        raise RuntimeError("Kindle not found")

    #win32gui.ShowWindow(handler, win32con.SW_RESTORE)
    handler = handler_info['handler']
    kindle_app_name = handler_info['windowName']
    force_foreground(handler)
    time.sleep(1)

    cur_handler = win32gui.GetForegroundWindow()
    if cur_handler != handler:
        raise ValueError(f"Current handler (cur_handler) does not match the target handler: {handler}")
        
    time.sleep(0.3)

    screenshotDir = formattedArgs['screenshotDir']
    page_limit = formattedArgs['screenshotNumLimit']
    if not os.path.exists(screenshotDir):
        os.makedirs(screenshotDir)
    take_screenshots(handler=handler, target_dir=screenshotDir, page_limit=page_limit)

    if is_window_fullscreen_on_its_monitor(handler):
        LOGGER.info("Exiting full screen mode.")
        pyautogui.press("f11")

    # use current working directory for pdf output
    pdfPath = formattedArgs['pdfOutputFilePath']
    available_pdf_path = get_available_filename(base_path=pdfPath).resolve()

    # Ensure output directory exists for PDF.
    directory = Path(available_pdf_path).parent.resolve()
    if not os.path.exists(directory):
        LOGGER.info(f"Creating PDF output directory at {directory}...")    
        os.makedirs(directory)

    LOGGER.info(f"Generating PDF at {available_pdf_path}...")

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

    LOGGER.info(f"Screenshots will be saved in {Path(formattedArgs['screenshotDir']).resolve()}")

    return(formattedArgs)

if __name__ == '__main__':
    LOGGER.info("Start of Kindle book page extraction program. ")
    LOGGER.info("Ensure that you have a book opened at the cover page in the Kindle for PC desktop application.")

    main()

    LOGGER.info("End of Kindle book page extraction program. ")