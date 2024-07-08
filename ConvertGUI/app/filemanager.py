import os
import shutil
import fitz
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QFileDialog


class FileManager(QObject):
    # signal for communication back to the MainWindow
    messageSignal = pyqtSignal(tuple)

    def __init__(self, main_window=None):
        super(FileManager, self).__init__()
        self.main_window = main_window

        self.temp_dir = "temp"
        os.makedirs(self.temp_dir, exist_ok=True)  # Create the temp directory if it doesn't exist

        # Cursor for file version tracking
        self.current_files = []
        self.current_version = 0

        # Stacks for undo and redo functionality
        self.undo_stack = []
        self.redo_stack = []

    def select_files(self):
        """" File selection method, loads single or multiple files into the app environment """
        self.messageSignal.emit(("Selecting files...", None))
        options = QFileDialog.Options()
        file_dialog_filter = ("All Supported Files (*.jpg *.jpeg *.png *.bmp"
                              " *.gif *.ppm *.pbm *.pgm *.xbm *.xpm *.pdf);"
                              ";JPEG (*.jpg *.jpeg);;PNG (*.png);;BMP (*.bmp);"
                              ";GIF (*.gif);;PPM (*.ppm);;PBM (*.pbm);"
                              ";PGM (*.pgm);;XBM (*.xbm);;XPM (*.xpm);; PDF (*.pdf)")

        files, _ = QFileDialog.getOpenFileNames(
            self.main_window,
            "Select one or more files to open",
            os.path.expanduser("~"),
            file_dialog_filter,
            options=options
        )
        if files:
            count = len(files)
            self.messageSignal.emit((f"Selected {count} file(s)", None))
            self.handle_files(files)

    def handle_files(self, files):
        """" Method for loading file(s) preview and setting up temp directory for version control """
        # clear the temp folder and reset file cursor at the start of handling new files
        self.clear_temp_folder()
        self.current_files.clear()
        self.current_version = 0
        self.undo_stack.clear()
        self.redo_stack.clear()

        # Make copy of files in temp directory, load to current files list
        for file in files:
            if file.split('.')[-1].upper() == "PDF":
                pdf_document = fitz.open(file)
                pdf_base_name = os.path.splitext(os.path.basename(file))[0]  # file name without extension
                for page_num in range(len(pdf_document)):
                    # new PDF for the single page
                    single_page_pdf = fitz.open()
                    single_page_pdf.insert_pdf(pdf_document, from_page=page_num, to_page=page_num)
                    output_file_name = f"00-{pdf_base_name}-page{page_num + 1}.pdf"
                    output_file_path = os.path.join(self.temp_dir, output_file_name)
                    single_page_pdf.save(output_file_path)
                    single_page_pdf.close()
                    self.current_files.append(output_file_path)
                pdf_document.close()
                print(f"PDF split into single pages and loaded to temp")
            else:
                base_name = os.path.basename(file)
                temp_file = os.path.join(self.temp_dir, f"00-{base_name}")
                shutil.copy(file, temp_file)
                self.current_files.append(temp_file)

        self.main_window.update_preview(self.current_files)
        self.main_window.update_export_format(self.current_files)

    def clear_temp_folder(self, min_version=None):
        """ Method for temp version files clearing. When given number as an argument, deletes from that version up """
        folder = self.temp_dir
        for filename in os.listdir(folder):
            # extract the version number from the filename, format "XX-filename.ext"
            version_number_str = filename.split('-')[0]
            if version_number_str == 'NEW' and min_version is not None:
                # in case of new files after successful convert action
                continue
            try:
                version_number = int(version_number_str)
            except ValueError:  # triggered by ERR- files
                version_number = 10000  # bigger than max reasonable version
            # check if the file version meets the criteria for deletion
            if min_version is not None and version_number < min_version:
                continue
            file_path = os.path.join(folder, filename)  # Full path of the file
            # Attempt to delete the file
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                    print(f'Deleted {file_path}')
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)  # Remove directory and all its contents
                    print(f'Deleted directory {file_path} and its contents')
            except Exception as e:
                self.messageSignal.emit((f'INTERNAL ERROR: Failed to delete {file_path}. Reason: {e}', 'red'))

    def update_current_files(self):
        # Push the current state to the undo stack
        self.undo_stack.append(self.current_files.copy())
        # Clear the redo stack on new action
        self.redo_stack.clear()

        self.current_version += 1
        formatted_version = f"{int(self.current_version):02}"
        self.clear_temp_folder(self.current_version)
        # Remove the prefix NEW- in the files in temp folder that contain it (those would be the files after operation)
        self.current_files.clear()
        for filename in os.listdir(self.temp_dir):
            if filename.startswith("NEW-"):
                # remove the "NEW-" prefix and prepend the current version
                new_filename = f"{formatted_version}-{filename[4:]}"
                old_path = os.path.join(self.temp_dir, filename)
                new_path = os.path.join(self.temp_dir, new_filename)
                # rename the file
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed {old_path} to {new_path}")
                    self.current_files.append(new_path)
                except OSError as e:
                    print(f"Error renaming file {old_path} to {new_path}: {e}")
        if len(self.current_files) == 1:
            self.main_window.update_preview(self.current_files)

    def remove_processed_files(self):
        """ Removes newly created files in temp when error during convert occurs """
        folder = self.temp_dir
        for filename in os.listdir(folder):
            # Extract the version number from the filename, format "XX-filename.ext"
            version_number_str = filename.split('-')[0]
            if version_number_str == 'NEW' or version_number_str == "ERR":
                file_path = os.path.join(folder, filename)  # full path of the file
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                        print(f'Deleted {file_path}')
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)  # Remove directory and all its contents
                        print(f'Deleted directory {file_path} and its contents')
                except Exception as e:
                    self.messageSignal.emit((f'INTERNAL ERROR: Failed to delete {file_path}. Reason: {e}', 'red'))
                    self.messageSignal.emit(('Resetting environment', 'red'))
                    self.clear_temp_folder()

    def undo(self):
        """ Reverts to the previous version of files """
        if not self.undo_stack:
            self.messageSignal.emit(("Undo unavailable.", 'red'))
            return
        self.redo_stack.append(self.current_files.copy())
        self.current_files = self.undo_stack.pop()
        self.current_version -= 1
        print(self.current_version)
        self.messageSignal.emit(("Undoing last operation.", "green"))
        if len(self.current_files) == 1:
            self.main_window.update_preview(self.current_files)

    def redo(self):
        """ Reapplies the previously undone action """
        if not self.redo_stack:
            self.messageSignal.emit(("Redo unavailable.", 'red'))
            return
        self.undo_stack.append(self.current_files.copy())
        self.current_files = self.redo_stack.pop()
        self.current_version += 1
        print(self.current_version)
        self.messageSignal.emit(("Redoing last operation.", "green"))
        if len(self.current_files) == 1:
            self.main_window.update_preview(self.current_files)
