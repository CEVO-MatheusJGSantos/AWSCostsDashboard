# AWSCostsDashboard
Dash application to generate AWS Cost Explorer charts

## How to run the app

Before running the application you will need to install the Pythoin libraries listed in the *requirements.txt* file. The recommended way is to use Python's virtual environment for that, as explained below:

 - Clone the repository and change to the destination directory:
 ```
$ git clone git@github.com:CEVO-MatheusJGSantos/AWSCostsDashboard.git
 
$ cd AWSCostsDashboard
 ```
  - Create the virtual environment and activate it:
```
$ python3 -m venv .env

$ source .env/bin/activate
```

 - Install the Python libraries in the new virtual environment:
```
$ pip install -r requirements.txt
```


This application requires an [AWS credential](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-files.html) with Cost Explorer [access permissions](https://docs.aws.amazon.com/cost-management/latest/userguide/billing-permissions-ref.html) to work. The credential can be set using the environment variables ```AWS_ACCESS_KEY_ID```, ```AWS_SECRET_ACCESS_KEY``` and ```AWS_SESSION_TOKEN``` (for temporary keys), or passing the AWS profile name using the ```--profile <<<profile_name>>>``` as parameter when running the application:

```
$ python3 costDashboard.py --help
usage: costDashboard.py [-h] [-p PROFILE]

options:
  -h, --help            show this help message and exit
  -p PROFILE, --profile PROFILE
                        AWS Profile
```

Example:
```
python3 costDashboard.py --profile myenv-dev
Dash is running on http://127.0.0.1:8050/

 * Serving Flask app 'costDashboard'
 * Debug mode: on

```

Next, open your system's web brower and open the http://127.0.0.1:8050/ address.