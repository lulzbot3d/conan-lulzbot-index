import os
from pathlib import Path

from conan import ConanFile
from conan.tools.files import files, replace_in_file
from conan.tools.layout import cmake_layout
from conan.tools.microsoft import VCVars, is_msvc
from conans.tools import chdir, vcvars

required_conan_version = ">=1.33.0"


class PyQt6Conan(ConanFile):
    name = "pyqt6"
    version = "6.3.1"
    author = "Riverbank Computing Limited"
    description = "Python bindings for the Qt cross platform application toolkit"
    topics = ("conan", "python", "pypi", "pip")
    license = "LGPL v3"
    homepage = "https://www.riverbankcomputing.com/software/pyqt/"
    url = "https://www.riverbankcomputing.com/software/pyqt/"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"

    python_requires = "pyprojecttoolchain/[>=0.1.6]@lulzbot/stable", "sipbuildtool/[>=0.2.2]@lulzbot/stable"

    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "py_build_requires": ["ANY"],
        "py_build_backend": ["ANY"],
    }
    default_options = {
        "shared": True,
        "fPIC": True,
        "py_build_requires": '"sip >=6.5, <7", "PyQt-builder >=1.11, <2"',
        "py_build_backend": "sipbuild.api",
    }

    def layout(self):
        cmake_layout(self)
        self.folders.source = "source"

    def requirements(self):
        self.requires("cpython/3.10.4")
        self.requires(f"qt/{self.version}@lulzbot/testing")

        # Overriding version conflicts of dependencies for cpython and qt
        self.requires("zlib/1.2.12")
        self.requires("openssl/1.1.1q")
        self.requires("libffi/3.2.1")
        self.requires("sqlite3/3.39.2")
        self.requires("expat/2.4.1")
        self.requires("harfbuzz/4.4.1")
        self.requires("glib/2.73.2")
        self.requires("pcre2/10.40")
        self.requires("vulkan-loader/1.3.216.0")
        if self.settings.os == "Linux":
            self.requires("wayland/1.21.0")

    def configure(self):
        self.options["cpython"].shared = self.options.shared
        self.options["qt"].shared = self.options.shared
        self.options["qt"].qtdeclarative = True
        self.options["qt"].qtimageformats = True
        self.options["qt"].qtshadertools = True
        self.options["qt"].qtsvg = True
        self.options["qt"].qtlanguageserver = True
        self.options["qt"].qtnetworkauth = True
        self.options["qt"].qt3d = True
        self.options["qt"].qtquick3d = True
        self.options["qt"].with_vulkan = True  # TODO: check if vulkan is really needed
        self.options["qt"].with_freetype = False
        self.options["qt"].with_doubleconversion = True

        # Disabled harfbuzz and glib for now since these require the use of a bash such as msys2. If we still need
        # these libraries. We should fix these recipes such that they don't use automake and autoconf on Windows and
        # add the configure option: `-o msys2:packages=base-devel,binutils,gcc,autoconf,automake`
        # These recipes are older version and don't handle the run/build environment and the win_bash config options
        # well. Preinstalling these packages is a quick and dirty solution but a viable one due to the time constraints
        self.options["qt"].with_harfbuzz = False
        self.options["qt"].with_glib = False

    def source(self):
        sources = self.conan_data["sources"][self.version]
        files.get(self, **sources, strip_root = True)

        # Might be a bug in PyQt-builder but the option link-full-dll isn't available, even though it is set in the
        # module pyqtbuild\project.py. A lot of sip definition files set the `use_limited_api` to `True` for the module
        # Since we compile PyQt6 for a single application against our own Python version, we can set the
        # `use_limited_api` to `False` this should stop the linker from linking against the limited Python ABI
        # python3.lib. Because now the `Py_LIMITED_API` C preprocessor symbol is no longer used.
        # Keep in mind that this is a quick and dirty hack, which allows us to link against the full
        # python<major><minor> ABI.
        if self.settings.os == "Windows":
            for sip_file in Path(self.source_folder, "sip").glob("**/*.sip"):
                replace_in_file(self, sip_file, "use_limited_api=True", "use_limited_api=False", strict = False)

    def generate(self):
        # if is_msvc(self):
        #     ms = VCVars(self)
        #     ms.generate(scope = "gmake_build")

        # Generate the pyproject.toml and override the shipped pyproject.toml, This allows us to link to our CPython
        # lib
        pp = self.python_requires["pyprojecttoolchain"].module.PyProjectToolchain(self)
        pp.blocks["tool_sip_metadata"].values["name"] = "PyQt6"
        pp.blocks["tool_sip_metadata"].values["description_file"] = "README"

        # The following setting keys and blocks are not used by PyQt6, we should remove these
        pp.blocks["tool_sip_project"].values["sip_files_dir"] = None
        pp.blocks.remove("tool_sip_bindings")
        pp.blocks.remove("extra_sources")
        pp.blocks.remove("compiling")

        pp.generate()

    def build(self):
        with vcvars(self):
            with chdir(self.source_folder):
                self.run(f"""sip-install --pep484-pyi --verbose --confirm-license --no-tools""", run_environment=True, env="conanrun")

    def package(self):
        # already installed by our use of the `sip-install` command during build
        pass

    def package_info(self):
        self.runenv_info.append_path("PYTHONPATH", os.path.join(self.package_folder, "site-packages"))
