import os
import setuptools
import subprocess
from setuptools.command.build_py import build_py


# Instead of using install_requires, and allowing pip to install dependencies
#   globally, disregarding any other dependencies currently installed/used by
#   other packages, this setup.py installs dependencies to the build directory.
VENDORED_DEPENDENCIES = [
    'pyyaml~=3.0',
    'send2trash~=1.4.0'
]


class BuildCommand(build_py):
    def run(self):
        installation_dir = os.path.dirname(os.path.abspath(__file__))
        setup_cfg_path = os.path.join(installation_dir, 'setup.cfg')
        build_dir = os.path.join(installation_dir, 'build', 'lib', 'saves')

        with open(setup_cfg_path, 'r+') as f:
            contents = f.read()
            contents += '[install]\nprefix='

            f.seek(0)
            f.write(contents)

        processes = []
        for dep in VENDORED_DEPENDENCIES:
            p = subprocess.Popen(['pip', 'install', dep, '-t', build_dir])
            processes.append(p)

        processes = [pr.wait() for pr in processes]

        build_py.run(self)


setuptools.setup(
    name='saves',
    license='MIT',
    version='0.0.1',
    description='copy save games between the local machine and a remote',
    author='Aleem Haji',
    author_email='hajial@gmail.com',
    packages=['saves', 'saves.copy_managers'],
    package_dir={'saves': 'src'},
    package_data={'saves': ['games.yaml', 'config.yaml']},
    entry_points={
        'console_scripts': [
            'saves = saves.cli:do_program'
        ]
    },
    cmdclass={
        'build_py': BuildCommand
    }
)
