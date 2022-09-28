Setup
===

## Clone the repository
Clone the repository to a path of your choice, e.g. `nio-smith`:
If you're looking for a more stable experience, it's recommended to check out the latest tag:
```
mkdir nio-smith
git clone --branch v0.0.8 https://github.com/alturiak/nio-smith.git nio-smith
```

If you really want the latest development commits, e.g. to submit PRs, check out HEAD:
```
mkdir nio-smith
git clone https://github.com/alturiak/nio-smith.git nio-smith
```
## Dependencies

### Install libolm
You should be able to install [libolm](https://gitlab.matrix.org/matrix-org/olm) from your distribution's package 
manager, e.g. `apt install libolm3 libolm-dev` on Debian/Ubuntu

### Install Python dependencies

Create and activate a Python 3 virtual environment:

```
virtualenv -p python3 env
source env/bin/activate
```

Change to the folder created earlier:
```
cd nio-smith
```

Install python dependencies:

```
pip install -r requirements.txt
```

To install all plugin requirements (specified in each plugin's `requirements.txt`), you may optionally run:
```
find . -iname requirements.txt -exec pip install -r {} \;
```

## Configuration

Copy the sample configuration file to a new `config.yaml` file.

```
cp sample.config.yaml config.yaml
```

Edit the config file. The `matrix` section must be modified at least.

## Running

Make sure to source your python environment if you haven't already:

```
source ~/env/bin/activate
```

Change to the bots directory if you haven't already:
```
cd nio-smith
```

Then simply run the bot with:

```
python main.py
```

By default, the bot will run with the config file at `./config.yaml` and load all plugins from the `plugins`-directory.
You may optionally specify a different config-file and plugins-directory by running:
```
python main.py [configfile [plugins_directory]]
```
e.g.
```
python main.py myconfig.yaml myplugins
```

## Upgrading
If you've checked out a tag in step 1, switch to the latest tag.
```
git fetch
git checkout v0.0.8
```

If you've checked out HEAD, just do
```
git pull
```

In case of changed requirements, repeat "Install Python dependencies".

Proceed with "Running" as usual.