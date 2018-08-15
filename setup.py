import os
import setuptools
import subprocess
from setuptools.command.build_py import build_py


PRIMARY_PACKAGE_EXECUTABLE_NAME = 'photos'

# Instead of using install_requires, and allowing pip to install dependencies
#   globally, disregarding any other dependencies currently installed/used by
#   other packages, this setup.py installs dependencies to the build directory.
# Note: The google-oauth2l will probably not work so well with this process,
#   because the executable probably won't hook up into a reachable path.
VENDORED_DEPENDENCIES = [
    'google-oauth2l==0.9.0',
    'oauth2client==2.1.0'
]


class BuildCommand(build_py):
    def run(self):
        installation_dir = os.path.dirname(os.path.abspath(__file__))
        setup_cfg_path = os.path.join(installation_dir, 'setup.cfg')
        build_dir = os.path.join(installation_dir, 'build', 'lib', PRIMARY_PACKAGE_EXECUTABLE_NAME)

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
    name=PRIMARY_PACKAGE_EXECUTABLE_NAME,
    license='MIT',
    version='0.0.1',
    description='copy content from Google Photos to a locally accessible path',
    author='Aleem Haji',
    author_email='hajial@gmail.com',
    packages=[PRIMARY_PACKAGE_EXECUTABLE_NAME],
    package_dir={PRIMARY_PACKAGE_EXECUTABLE_NAME: 'src'},
    entry_points={
        'console_scripts': [
            '{0} = {0}.backup:do_program'.format(PRIMARY_PACKAGE_EXECUTABLE_NAME)
        ]
    },
    cmdclass={
        'build_py': BuildCommand
    }
)
