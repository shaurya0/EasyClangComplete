"""This module encapsulates communication with sublime settings

Attributes:
    log (logging.Logger): logger
"""
import sublime
import logging
import re

import os.path as path

from .tools import PKG_NAME

log = logging.getLogger(__name__)
log.debug(" reloading module")


class Settings:

    """class that encapsulates sublime settings

    Attributes:
        clang_binary (string): name of clang binary to be used
        complete_all (bool): flag to trigger autocompletion on every keystroke
        errors_on_save (bool): if true, show errors on save
        include_dirs (string[]): array of directories with headers
        include_file_folder (bool): if true, current location -> 'include_dirs'
        include_parent_folder (bool): if true, parent -> 'include_dirs'
        project_base_folder (str): root folder of current project
        project_base_name (str): name of the current project
        project_specific_settings (TYPE): use project-specific settings
        search_clang_complete (bool): if true search for '.clang_complete'
            file up the tree
        std_flag (string): flag of the c++ std library, e.g. -std=c++11
        subl_settings (sublime.settings): link to sublime text settings dict
        triggers (string[]): triggers that trigger autocompletion
        use_libclang (bool): use libclang instead of parsing binary output
        verbose (bool): verbose flag
    """

    subl_settings = None

    verbose = None
    include_file_folder = None
    include_parent_folder = None
    complete_all = None
    triggers = None
    include_dirs = None
    clang_binary = None
    std_flag = None
    flags = None
    search_clang_complete = None
    errors_on_save = None
    use_libclang = None
    hide_default_completions = None

    def __init__(self):
        """Initialize the class.
        """
        self.load_settings()
        if not self.is_valid():
            log.critical(" Could not load settings!")
            log.critical(" NO AUTOCOMPLETE WILL BE AVAILABLE")
            return

    def on_settings_changed(self):
        """When user changes settings, trigger this.
        """
        self.load_settings()
        log.info(" settings changed and reloaded")

    def load_settings(self):
        """Load settings from sublime dictionary to internal variables
        """
        self.subl_settings = sublime.load_settings(
            PKG_NAME + ".sublime-settings")
        self.verbose = self.subl_settings.get("verbose")
        self.complete_all = self.subl_settings.get("autocomplete_all")
        self.include_parent_folder = self.subl_settings.get(
            "include_file_parent_folder")
        self.include_file_folder = self.subl_settings.get(
            "include_file_folder")
        self.triggers = self.subl_settings.get("triggers")
        self.include_dirs = self.subl_settings.get("include_dirs")
        self.clang_binary = self.subl_settings.get("clang_binary")
        self.errors_on_save = self.subl_settings.get("errors_on_save")
        self.std_flag = self.subl_settings.get("std_flag")
        self.flags = self.subl_settings.get("flags")
        self.use_libclang = self.subl_settings.get("use_libclang")
        self.search_clang_complete = self.subl_settings.get(
            "search_clang_complete_file")
        self.project_specific_settings = self.subl_settings.get(
            "use_project_specific_settings")
        self.hide_default_completions = self.subl_settings.get(
            "hide_default_completions")

        self.subl_settings.clear_on_change(PKG_NAME)
        self.subl_settings.add_on_change(PKG_NAME, self.on_settings_changed)

        self.project_base_name = ""
        self.project_base_folder = ""
        variables = sublime.active_window().extract_variables()
        if 'folder' in variables:
            self.project_base_folder = variables['folder']
        if 'project_base_name' in variables:
            self.project_base_name = variables['project_base_name']

        if self.std_flag is None:
            self.std_flag = "-std=c++11"
            log.debug(" set std_flag to default: %s", self.std_flag)

    def get_project_clang_flags(self):
        """Get clang flags for the current project

        Returns:
            list(str): flags for clang, None if no project found
        """
        try:
            project_data = sublime.active_window().project_data()
            log.debug(" project data: %s", project_data)
            project_settings = project_data["settings"]
            log.debug(" project settings: %s", project_settings)
            project_flags = []
            for flag in project_settings["clang_flags"]:
                if flag.startswith('-I'):
                    project_flags.append(self.__expand_include(flag))
                elif flag.startswith('-std'):
                    self.std_flag = flag
                else:
                    # we just append everything else
                    project_flags.append(flag)
            log.debug(" project_flags: %s", project_flags)
            return project_flags
        except Exception as e:
            log.error(" failed to read clang flags from project settings.")
            log.error(" error is: %s.", e)
            return None

    def __expand_include(self, include):
        """Expand include. Make sure path is ok given a specific os and add
        current project path if the include path is relative.

        Args:
            include (str): include in form -I<include>

        Returns:
            str: expanded include in form '-I "<include>"'
        """
        flag = None
        path_to_add = include[2:].rstrip()
        if path.isabs(path_to_add):
            flag = '-I "{}"'.format(path.normpath(path_to_add))
        else:
            flag = '-I "{}"'.format(
                path.join(self.project_base_folder, path_to_add))
        return flag

    def is_valid(self):
        """Check settings validity. If any of the settings is None the settings
        are not valid.

        Returns:
            bool: validity of settings
        """
        if self.subl_settings is None:
            log.critical(" no subl_settings found")
            return False
        if self.verbose is None:
            log.critical(" no verbose flag found")
            return False
        if self.include_parent_folder is None:
            log.critical(" no include_parent_folder flag found")
            return False
        if self.include_file_folder is None:
            log.critical(" no include_file_folder flag found")
            return False
        if self.complete_all is None:
            log.critical(" no autocomplete_all flag found")
            return False
        if self.triggers is None:
            log.critical(" no triggers found")
            return False
        if self.include_dirs is None:
            log.critical(" no include_dirs setting found")
            return False
        if self.clang_binary is None:
            log.critical(" no clang_binary setting found")
            return False
        if self.std_flag is None:
            log.critical(" no std_flag setting found")
            return False
        if self.search_clang_complete is None:
            log.critical(" no search_clang_complete setting found")
            return False
        if self.errors_on_save is None:
            log.critical(" no errors_on_save setting found")
            return False
        if self.use_libclang is None:
            log.critical(" no use_libclang setting found")
            return False
        if self.project_specific_settings is None:
            log.critical(" no use_project_specific_settings setting found")
            return False
        if self.hide_default_completions is None:
            log.critical(" no hide_default_completions setting found")
            return False
        return True

    def populate_include_dirs(self, file_current_folder, file_parent_folder):
        """populate the include dirs based on the project

        Args:
            file_current_folder (str): current file folder
            file_parent_folder (str): file parent folder

        Returns:
            str[]: directories where clang searches for header files
        """
        # initialize new include_dirs
        include_dirs = list(self.include_dirs)
        log.debug(" populating include dirs with current variables:")
        log.debug(" project_base_name = %s", self.project_base_name)
        log.debug(" project_base_folder = %s", self.project_base_folder)
        log.debug(" file_parent_folder = %s", file_parent_folder)

        # replace project related variables to real ones
        for i, include_dir in enumerate(include_dirs):
            include_dir = re.sub(
                "(\$project_base_path)", self.project_base_folder, include_dir)
            include_dir = re.sub("(\$project_name)",
                                 self.project_base_name, include_dir)
            include_dir = path.abspath(include_dir)
            include_dirs[i] = include_dir

        if self.include_file_folder:
            include_dirs.append(file_current_folder)
        if self.include_parent_folder:
            include_dirs.append(file_parent_folder)

        # print resulting include dirs
        log.debug(" include_dirs = %s", include_dirs)
        return include_dirs
