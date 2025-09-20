from setuptools import setup, find_packages
import os

# Read the README file for the long description
def read_readme():
    with open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
        return f.read()

setup(
    name="django-document-manager",
    version="0.2.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'django_document_manager': [
            'migrations/*.py',
            'data/*.json',
        ],
    },
    install_requires=[
        "Django>=3.2,<6.0",
        "uuid6>=2025.0.0,<2026.0.0",
        # Note: django-crud-audit and django-catalogs are private dependencies
        # Install separately: pip install -r requirements-private.txt
    ],
    python_requires=">=3.8",
    description="A comprehensive Django app for document management with versioning, validation, and AI processing.",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    author="Lorenzo Silva",
    author_email="lorenzo.smb.rayo@gmail.com",
    license="MIT",
    url="https://github.com/LorenzoSilvaMoore/django-document-manager",
    project_urls={
        "Bug Tracker": "https://github.com/LorenzoSilvaMoore/django-document-manager/issues",
        "Documentation": "https://github.com/LorenzoSilvaMoore/django-document-manager#readme",
        "Source Code": "https://github.com/LorenzoSilvaMoore/django-document-manager",
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
    keywords="django document manager",
    zip_safe=False,
)