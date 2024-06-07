import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="freecad_build_instruction_generator",
    install_requires=[],
    version="0.1.0",
    author="Martin Klomp",
    author_email="m.klomp@tudelft.nl",
    description="Create SVG build instructions with FreeCAD",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mirte-robot/freecad-build-instruction-generator",
    packages=['freecad_build_instruction_generator'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
