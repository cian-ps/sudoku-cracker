from multiprocessing import cpu_count
from os.path import join

import sh
from pythonforandroid.recipe import PyProjectRecipe
from pythonforandroid.toolchain import current_directory, shprint

PAGE_SIZE_LDFLAGS = "-Wl,-z,max-page-size=16384 -Wl,-z,common-page-size=16384"


class OnnxRuntimeRecipe(PyProjectRecipe):
    version = "1.22.1"
    url = "https://github.com/microsoft/onnxruntime/archive/refs/tags/v{version}.tar.gz"

    depends = ["setuptools", "wheel", "numpy", "protobuf", "pybind11"]
    patches = [
        "patches/onnx_numpy.patch",
        "patches/abseil_codeload_url.patch",
    ]
    build_in_src = True

    def get_recipe_env(self, arch=None, **kwargs):
        env = super().get_recipe_env(arch, **kwargs)
        python_include_dir = self.ctx.python_recipe.include_root(arch.arch)
        env["CPPFLAGS"] += f" -Wno-unused-variable -I{python_include_dir}"
        env["CXXFLAGS"] += f" -I{python_include_dir}"
        env["CFLAGS"] += f" -I{python_include_dir}"
        env["Python_INCLUDE_DIRS"] = python_include_dir
        env["LDFLAGS"] += f" {PAGE_SIZE_LDFLAGS}"
        return env

    def build_arch(self, arch):
        env = self.get_recipe_env(arch)
        android_platform = str(self.ctx.ndk_api)

        build_dir = self.get_build_dir(arch.arch)
        cmake_dir = join(build_dir, "cmake")
        capi_dir = join(build_dir, "onnxruntime", "capi")
        dist_dir = join(build_dir, "dist")
        python_include_dir = self.ctx.python_recipe.include_root(arch.arch)
        pybind11_recipe = self.get_recipe("pybind11", self.ctx)
        pybind11_include_dir = pybind11_recipe.get_include_dir(arch)
        python_link_root = self.ctx.python_recipe.link_root(arch.arch)
        python_link_version = self.ctx.python_recipe.link_version
        python_library = join(
            python_link_root,
            f"libpython{python_link_version}.so",
        )
        python_site_packages = self.ctx.get_site_packages_dir(arch)
        python_include_numpy = join(
            python_site_packages,
            "numpy",
            "_core",
            "include",
        )
        toolchain_file = join(
            self.ctx.ndk_dir,
            "build/cmake/android.toolchain.cmake",
        )
        python_path = self.ctx.hostpython
        shprint(sh.mkdir, "-p", capi_dir)
        shprint(sh.mkdir, "-p", dist_dir)

        cmake_args = [
            "cmake",
            cmake_dir,
            f"-DCMAKE_TOOLCHAIN_FILE={toolchain_file}",
            f"-DANDROID_ABI={arch.arch}",
            f"-DANDROID_PLATFORM={android_platform}",
            "-Donnxruntime_ENABLE_PYTHON=ON",
            "-Donnxruntime_BUILD_SHARED_LIB=OFF",
            "-DPYBIND11_USE_CROSSCOMPILING=TRUE",
            "-Donnxruntime_USE_NNAPI_BUILTIN=ON",
            "-Donnxruntime_USE_XNNPACK=ON",
            "-DONNX_CUSTOM_PROTOC_EXECUTABLE=/usr/bin/protoc",
            f"-DPython_NumPy_INCLUDE_DIR={python_include_numpy}",
            f"-DPython_EXECUTABLE={python_path}",
            (
                f"-Dpybind11_INCLUDE_DIRS={pybind11_include_dir};"
                f"{python_include_dir};{python_include_numpy}"
            ),
            f"-DPython_LIBRARY={python_library}",
            f"-DPython_LIBRARIES={python_library}",
            "-DCMAKE_BUILD_TYPE=RELEASE",
            "-DCMAKE_POLICY_VERSION_MINIMUM=3.5",
            "-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON",
            f"-DCMAKE_SHARED_LINKER_FLAGS={PAGE_SIZE_LDFLAGS}",
            f"-DCMAKE_EXE_LINKER_FLAGS={PAGE_SIZE_LDFLAGS}",
            "-Donnxruntime_BUILD_UNIT_TESTS=OFF",
        ]

        with current_directory(build_dir):
            shprint(sh.Command("cmake"), *cmake_args, _env=env)
            shprint(sh.make, "-j" + str(cpu_count()), _env=env)

        super().build_arch(arch)


recipe = OnnxRuntimeRecipe()
