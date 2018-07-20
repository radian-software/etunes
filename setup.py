from setuptools import setup

# https://python-packaging.readthedocs.io/en/latest/minimal.html
setup(
    author="Radon Rosborough",
    author_email="radon.neon@gmail.com",
    description="The declarative, version-controlled music library manager.",
    license="MIT",
    install_requires=[
        "jsonschema",
        "psutil",
        "PyYAML",
    ],
    name="etunes",
    scripts=["scripts/etunes"],
    url="https://github.com/raxod502/etunes",
    version="1.0",
    zip_safe=True,
)
