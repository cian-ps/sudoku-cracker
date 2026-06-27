from os.path import join

from pythonforandroid.recipe import PythonRecipe


class Pybind11Recipe(PythonRecipe):
    # 2.11.x fails against Python 3.14 (_PyThreadState_UncheckedGet deprecated as error)
    version = "2.13.6"
    url = "https://github.com/pybind/pybind11/archive/refs/tags/v{version}.zip"
    depends = ["setuptools"]
    call_hostpython_via_targetpython = False
    install_in_hostpython = True

    def get_include_dir(self, arch):
        return join(self.get_build_dir(arch.arch), "include")


recipe = Pybind11Recipe()
