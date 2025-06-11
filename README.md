# api-server


## Setup

1. Install Python 3.11

```shell
# On macOS
brew install python@3.11

```

2. Create a virtual environment

```shell
virtualenv venv --python="python3.11"
```

3. Activate the virtual environment

```shell
source venv/bin/activate
```

4. Install the required packages

```shell
pip install -r requirements.txt
```

## Development

To run the API server locally, use the following command:

```shell
python3 formsg_webhook.py
```

## Build

```shell
airbase build && ./patch_build.sh
```
