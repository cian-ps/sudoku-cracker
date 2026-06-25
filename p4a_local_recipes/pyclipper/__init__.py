from pythonforandroid.recipe import PyProjectRecipe


class PyclipperRecipe(PyProjectRecipe):
    version = "1.4.0"
    url = (
        "https://files.pythonhosted.org/packages/source/p/pyclipper/"
        "pyclipper-{version}.tar.gz"
    )


recipe = PyclipperRecipe()
