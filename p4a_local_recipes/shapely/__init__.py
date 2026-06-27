from os.path import join

from pythonforandroid.recipe import PyProjectRecipe


class ShapelyRecipe(PyProjectRecipe):
    version = "2.1.2"
    url = "https://github.com/shapely/shapely/archive/{version}.tar.gz"
    depends = ["setuptools", "numpy", "libgeos"]
    hostpython_prerequisites = ["cython", "numpy"]

    def get_recipe_env(self, arch=None, **kwargs):
        env = super().get_recipe_env(arch, **kwargs)
        libgeos_install = join(
            self.get_recipe("libgeos", self.ctx).get_build_dir(arch.arch),
            "install_target",
        )
        geos_include = join(libgeos_install, "include")
        geos_lib = join(libgeos_install, "lib")
        geos_config = join(libgeos_install, "bin", "geos-config")

        env["GEOS_INCLUDE_PATH"] = geos_include
        env["GEOS_LIBRARY_PATH"] = geos_lib
        env["GEOS_CONFIG"] = geos_config
        env["CFLAGS"] += f" -I{geos_include}"
        env["LDFLAGS"] += f" -L{geos_lib} -lgeos_c -lgeos"
        return env


recipe = ShapelyRecipe()
