import os
import setuptools
import subprocess
from setuptools.command.build_py import build_py


# Instead of using install_requires, and allowing pip to install dependencies
#   globally, disregarding any other dependencies currently installed/used by
#   other packages, this setup.py installs dependencies to the build directory.
VENDORED_DEPENDENCIES = []
with open('requirements.install.txt') as f:
    for v in f.readlines():
        if v:
            VENDORED_DEPENDENCIES.append(v)


class BuildCommand(build_py):
    def run(self):
        installation_dir = os.path.dirname(os.path.abspath(__file__))
        setup_cfg_path = os.path.join(installation_dir, 'setup.cfg')
        build_dir = os.path.join(installation_dir, 'build', 'lib', 'backup')

        with open(setup_cfg_path, 'r+') as f:
            contents = f.read()
            contents += '[install]\nprefix='

            f.seek(0)
            f.write(contents)

        processes = []
        for dep in VENDORED_DEPENDENCIES:
            p = subprocess.Popen(['pip3', 'install', dep, '-t', build_dir])
            processes.append(p)

        processes = [pr.wait() for pr in processes]

        build_py.run(self)


setuptools.setup(
    cmdclass={
        'build_py': BuildCommand
    }
)
