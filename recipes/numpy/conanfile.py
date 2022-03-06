import os

from conan import ConanFile
from conan.tools.env.virtualrunenv import VirtualRunEnv
from conan.tools.env.virtualbuildenv import VirtualBuildEnv

required_conan_version = ">=1.44.1"


class NumpyConan(ConanFile):
    name = "numpy"
    version = "1.21.5"
    description = "NumPy is the fundamental package for array computing with Python."
    topics = ("conan", "python", "pypi", "pip")
    license = "BSD"
    homepage = "https://www.numpy.org"
    url = "https://www.numpy.org"
    settings = "os", "compiler", "build_type", "arch"
    build_policy = "missing"
    default_user = "python"
    default_channel = "stable"
    python_requires = ["UltimakerBase/0.4@ultimaker/testing", "PipBuildTool/0.2@ultimaker/testing"]
    python_requires_extend = "UltimakerBase.UltimakerBase"
    requires = "python/3.10.2@python/stable"
    hashes = [
        "sha256:301e408a052fdcda5cdcf03021ebafc3c6ea093021bf9d1aa47c54d48bdad166",
        "sha256:a7e8f6216f180f3fd4efb73de5d1eaefb5f5a1ee5b645c67333033e39440e63a",
        "sha256:fc7a7d7b0ed72589fd8b8486b9b42a564f10b8762be8bd4d9df94b807af4a089",
        "sha256:58ca1d7c8aef6e996112d0ce873ac9dfa1eaf4a1196b4ff7ff73880a09923ba7",
        "sha256:dc4b2fb01f1b4ddbe2453468ea0719f4dbb1f5caa712c8b21bb3dd1480cd30d9",
        "sha256:6a5928bc6241264dce5ed509e66f33676fc97f464e7a919edc672fb5532221ee"
    ]  # NOTE: these are only the hashes for Windows

    def generate(self):
        rv = VirtualRunEnv(self)
        rv.generate()

        bv = VirtualBuildEnv(self)
        bv.generate()

    def build(self):
        pb = self.python_requires["PipBuildTool"].module.PipBuildTool(self)
        pb.configure()
        pb.build()

    def package(self):
        self.copy("*")

    def package_info(self):
        self._set_python_site_packages()
        self.runenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))
        self.buildenv_info.prepend_path("PATH", os.path.join(self.package_folder, "bin"))

    def package_id(self):
        self.info.settings.build_type = "Release"
