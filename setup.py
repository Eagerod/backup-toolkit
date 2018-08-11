import setuptools


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
    install_requires=[
        'pyyaml~=3.0',
        'send2trash~=1.4.0'
    ]
)
