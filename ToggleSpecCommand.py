import sublime, sublime_plugin
import re, os

class ToggleSpecCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        try:
            if self.is_spec:
                self.window.open_file(self.file_under_test)
            else:
                self.window.open_file(self.test_under_file)
        except NoMatchingFileFoundException as e:
            sublime.status_message(e.message)

    @property
    def folder_exclude_patterns(self):
        patterns = []
        patterns.extend(self.project_folder_exclude_patterns)
        patterns.extend(self.settings_folder_exclude_patterns)
        return patterns

    @property
    def project_folder_exclude_patterns(self):
        exclude_patterns = []

        project_data = self.window.project_data()
        for folder in project_data.get('folders', []):
            folder_exclude_patterns = folder.get('folder_exclude_patterns', [])
            exclude_patterns.extend(folder_exclude_patterns)

        return exclude_patterns

    @property
    def settings_folder_exclude_patterns(self):
        settings = self.view.settings()
        return settings.get('folder_exclude_patterns', [])

    @property
    def file_under_test(self):
        dirname, basename = self.dirname_and_basename(self.file_name)
        basename = re.sub(r"[_-]spec", "", basename, 1)
        return self.first_file_matching(basename, dirname)

    @property
    def file_name(self):
        return self.view.file_name()

    @property
    def open_file_names(self):
        file_names = []
        for view in self.window.views():
            if view.file_name():
                file_names.append(view.file_name())
        return file_names

    @property
    def is_spec(self):
        return re.search("spec", self.file_name)

    @property
    def test_under_file(self):
        dirname, basename = self.dirname_and_basename(self.file_name)
        basename = basename.replace(".", "[_-]spec.", 1)
        return self.first_file_matching(basename, dirname)

    @property
    def window(self):
        return self.view.window()

    def filter_dirnames(self, dirnames):
        filtered_dirnames = []
        for dirname in dirnames:
            if not self.is_ignored_directory(dirname):
                filtered_dirnames.append(dirname)
        return filtered_dirnames

    def is_ignored_directory(self, dirname):
        for pattern in self.folder_exclude_patterns:
            if re.search(pattern, dirname):
                return True

    def walk(self, directory):
        for dir, dirnames, files in os.walk(directory):
            dirnames[:] = self.filter_dirnames(dirnames)
            yield dir, dirnames, files

    def first_file_matching(self, match_string, dirname):
        open_file = self.first_open_file_matching(match_string, dirname)
        if open_file:
            return open_file

        open_file = self.first_project_file_matching(match_string, dirname)
        if open_file:
            return open_file

        raise NoMatchingFileFoundException(match_string)

    def first_project_file_matching(self, match_string, match_dirname):
        folders = self.window.folders()
        for folder in folders:
            return self.first_file_matching_in_folder(folder, match_string, match_dirname)

    def first_file_matching_in_folder(self, folder, match_string, match_dirname):
        for path, _, file_names in self.walk(folder):
            if match_dirname != os.path.basename(path):
                continue

            for file_name in file_names:
                if re.search(match_string, file_name):
                    return os.path.join(path, file_name)

    def first_open_file_matching(self, match_string, match_dirname):
        secondary_match = None

        for file_name in self.open_file_names:
            dirname, basename = self.dirname_and_basename(file_name)
            if re.search(match_string, basename):
                if dirname == match_dirname:
                    return file_name
                secondary_match = file_name

        return secondary_match

    def dirname_and_basename(self, full_path):
        path, basename = os.path.split(full_path)
        dirname = os.path.basename(path)
        return [dirname, basename]

class NoMatchingFileFoundException(Exception):
    def __init__(self, file_name):
        self._file_name = file_name
        Exception.__init__(self, self.message)

    @property
    def message(self):
        return "Could not find file matching: {0}".format(self._file_name)



