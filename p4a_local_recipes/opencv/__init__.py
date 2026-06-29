from glob import glob
from os.path import join

import sh
from pythonforandroid.logger import info, shprint
from pythonforandroid.recipes.opencv import OpenCVRecipe as BaseOpenCVRecipe
from pythonforandroid.util import current_directory


class OpenCVRecipe(BaseOpenCVRecipe):
    """Ensure cv2.so is installed even when native OpenCV libs are cached."""

    def install_libraries(self, arch):
        super().install_libraries(arch)
        site_packages = self.ctx.get_site_packages_dir(arch)
        if glob(join(site_packages, "cv2*.so")):
            return

        build_dir = join(self.get_build_dir(arch.arch), "build")
        cv2_built = glob(join(build_dir, "lib", arch.arch, "python3", "cv2*.so"))
        if cv2_built:
            info("Installing cached cv2 binding into site-packages")
            sh.cp(cv2_built[0], join(site_packages, "cv2.so"))
            return

        info("cv2.so missing; rebuilding OpenCV python bindings")
        with current_directory(build_dir):
            env = self.get_recipe_env(arch)
            shprint(
                sh.cmake, "-DCOMPONENT=python", "-P", "./cmake_install.cmake", _env=env
            )


recipe = OpenCVRecipe()
