# US Visa Rescheduler for Canada

A python script which tries to find a better date for your visa appointment. Tested on Canada only.

![image](https://github.com/user-attachments/assets/70cfed48-7a37-4371-af37-d6d96f4c9e9f)

## Setup

Make sure you have booked an appointment on https://ais.usvisa-info.com/en-ca/.

Install dependencies (Python3 is required):
```sh
pip install requests selenium webdriver_manager
or install it using the options in the GUI
```

Modify 'AVAILABLE_DATE_REQUEST_SUFFIX' based on the location. 

89: Calgary
90: Halifax
91: Montreal
92: Ottawa
93: Quebec City
94: Toronto
95: Vancouver

= '/days/94.json?appointments[expedite]=false'  # Toronto

### How to run the script

```sh
python gui.py
```

or download the executable https://github.com/git-ashwinpandey/US-Visa-Rescheduler/releases

See the script in action. Once you're satisfied with its functionality, set `TEST_MODE` to `False` in `settings.py`. For a headless operation, you can also set `SHOW_GUI` to `False` and allow the script to run unattended.

## Caution

It may not always be feasible to reschedule an appointment multiple times. Therefore, it's crucial to use `TEST_MODE = True` for testing purposes and ensure the `LATEST_ACCEPTABLE_DATE` is genuinely acceptable to you.


## Disclaimer

This script is provided as-is for the purpose of assisting individuals in rescheduling appointments. While it has been developed with care and with the intention of being helpful, it comes with no guarantees or warranties of any kind, either expressed or implied. By using this script, you acknowledge and agree that you are doing so at your own risk. The author(s) or contributor(s) of this script shall not be held liable for any direct or indirect damages that arise from its use. Please ensure that you understand the actions performed by this script before running it, and consider the ethical and legal implications of its use in your context.
