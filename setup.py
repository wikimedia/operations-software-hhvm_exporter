from setuptools import setup

setup(name='hhvm_exporter',
      version='0.5',
      description='Prometheus exporter for HHVM',
      url='https://github.com/wikimedia/operations-software-hhvm_exporter',
      author='Filippo Giunchedi',
      author_email='filippo@wikimedia.org',
      license='Apache License, Version 2.0',
      packages=['hhvm_exporter'],
      install_requires=[
          'prometheus-client',
          'requests',
      ],
      entry_points={
          'console_scripts': [
              'hhvm_exporter = hhvm_exporter.exporter:main'
          ]
      },
)
