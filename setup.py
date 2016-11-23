import foundation
import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='foundation',
    version=foundation.__version__,
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django>=1.10,<1.11',
        'django-sekizai>=0.10',
    ],
    license='MIT License',
    description='A generic website backend implemented in Django using ' \
        'Controllers.',
    long_description=README,
    url='https://github.com/altio/foundation',
    author="John D'Ambrosio",
    author_email='john@alternate.io',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 1.10',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
)
