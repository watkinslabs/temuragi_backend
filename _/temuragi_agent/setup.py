from setuptools import setup, find_packages


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

from wl_version_manager import VersionManager

setup(
    name="temuragi_agent",
    version=VersionManager.get_version(),
    author="Chris Watkins",
    author_email="chris@watkinslabs.com",
    packages=find_packages(),
    long_description=long_description,
    include_package_data=True,
    package_data={"temuragi_agent": ["config.yaml"]},
    install_requires=[
        "wl_module_builder",
        "wl_config_manager",
        "ai_manager",
        "version_manager",
    ],
    entry_points={
        "console_scripts": [
            "temuragi-agent = temuragi_agent.cli:main",
        ],
    },
    license="BSD-3-Clause",
)