import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

bower_json = {
"dependencies": {
    "jquery": "^3.2.1",
    "bootstrap": "^3.3.7",
    "bootstrap-multiselect": "^0.9.13",
    "bootstrap-datepicker": "^1.7.0",
    "jquery-tablesort": "^0.0.11",
    "leaflet": "^1.1.0",
    "tooltipster": "^4.2.5",
    "leaflet.markercluster": "Leaflet.markercluster#^1.0.6",
  },
  "resolutions": {
    "jquery": "1.9.1 - 3"
  }
}

setup(
    name='apis-highlighter',
    version='0.8.6',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',  # example license
    description='Addon to APIS webapplication that allows to annotate texts',
    long_description=README,
    url='https://www.apis.acdh.oeaw.ac.at/',
    author='Matthias Schlögl',
    author_email='matthias.schloegl@oeaw.ac.at',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.0',  # replace "X.Y" as appropriate
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'calmjs.bower',
        'Django>=2.0',
        'django-autocomplete-light>=3.2.10',
        'django-crispy-forms>=1.7.0',
        'django-filter>=1.0.4',
        'django-tables2>=1.12.0',
        'djangorestframework>=3.6.2',
        'djangorestframework-csv>=2.0.0',
        'djangorestframework-xml>=1.3.0',
    ],
    bower_json=bower_json,
)
