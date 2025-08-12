from setuptools import setup, find_packages
import os

# Read the README file for the long description
def read_readme():
    with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
        return f.read()

setup(
    name="django-iso-3166",
    version="0.1.1",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'django_iso_3166': [
            'data/*.json',
            'migrations/*.py',
        ],
    },
    install_requires=[
        "Django>=3.2,<6.0"
    ],
    python_requires=">=3.8",
    description="Django app for managing and bootstrapping ISO 3166 geographical data",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Lorenzo Silva",
    author_email="your.email@example.com",
    license="MIT",
    url="https://github.com/yourusername/django-iso-3166",
    project_urls={
        "Bug Tracker": "https://github.com/yourusername/django-iso-3166/issues",
        "Documentation": "https://github.com/yourusername/django-iso-3166#readme",
        "Source Code": "https://github.com/yourusername/django-iso-3166",
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Framework :: Django",
        "Framework :: Django :: 3.2",
        "Framework :: Django :: 4.0",
        "Framework :: Django :: 4.1",
        "Framework :: Django :: 4.2",
        "Framework :: Django :: 5.0",
        "Topic :: Database",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    keywords="django geography iso3166 countries cities states regions",
    zip_safe=False,
)