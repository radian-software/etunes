from setuptools import setup

# https://python-packaging.readthedocs.io/en/latest/minimal.html
setup(
    author="Radian LLC",
    author_email="contact+etunes@radian.codes",
    description="The declarative, version-controlled music library manager.",
    license="MIT",
    install_requires=[
        "jsonschema",
        "psutil",
        "PyYAML",
    ],
    name="etunes",
    scripts=["scripts/etunes"],
    url="https://github.com/radian-software/etunes",
    version="1.0",
    zip_safe=True,
)
