# westream
Under development. Check out the `data` folder and modify the configuration files to your liking before running.

# Installation
## From source
- Clone the repository and enter the folder
    ```sh
    git clone https://github.com/g0ldyy/westream
    cd westream
    ```
- Install dependencies
    ```sh
    pip install uv
    uv sync
    ````
- Start WeStream
    ```sh
    uv run python run.py
    ````

# To Do
- Automatic config setup system with integrity check via Pydantic
- Filter system for regex-based control of xtream catalog content
