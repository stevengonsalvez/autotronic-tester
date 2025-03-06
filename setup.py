from setuptools import setup, find_packages

setup(
    name="autogen-playwright",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "autogen-core>=0.4.0",
        "autogen-agentchat>=0.4.0",
        "autogen-ext>=0.4.0",
        "playwright>=1.41.0",
        "python-dotenv>=1.0.0",
        "agentops>=0.1.0",
        "pandas>=2.0.0",
        "cerebras_cloud_sdk>=0.1.0",
        "streamlit>=1.31.0",
    ],
    python_requires=">=3.9",
) 