Setup
===

## Clone the repository
Clone the repository to a path of your choice, e.g. `nio-smith`:
```
mkdir nio-smith
git clone https://github.com/alturiak/nio-smith.git nio-smith
```
## Dependencies

If you would rather not or are unable to run docker, the following will
instruct you on how to install the dependencies natively:

### Install libolm
You should be able to install [libolm](https://gitlab.matrix.org/matrix-org/olm) from your distribution's package 
manager, e.g. `apt install libolm3` on Debian/Ubuntu

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

By default, the bot will run with the config file at `./config.yaml`.