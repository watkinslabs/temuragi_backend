from setuptools import setup, find_packages

setup(
    name="temuragi_agent",
    version="0.1.0",
    packages=find_packages(),
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