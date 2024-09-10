# US Visa Rescheduler for Canada

A python script which tries to find a better date for your visa appointment. Tested on Canada only.

NOTE: You'll probably see System is busy during the day. Use this after 9-10PM EST.

![image](https://github.com/user-attachments/assets/551f7ca8-a2d3-4b57-aa4b-86da78327d49)


## Setup

Make sure you have booked an appointment on https://ais.usvisa-info.com/en-ca/.

Install dependencies (Python3 is required):
```sh
pip install requests selenium webdriver_manager
or install it using the options in the GUI
```

### How to use the script

```sh
python gui.py
```

or download the latest release https://github.com/git-ashwinpandey/US-Visa-Rescheduler/releases

See the script in action using Test Mode. Test mode stops before confirming appointment selection.
Once you're satisfied with its functionality, disable Test Mode. 
For a headless operation, you can enable headless mode and allow the script to run unattended.

## Caution

It may not always be feasible to reschedule an appointment multiple times. Use Testing mode to test the script before actually rescheduling your date.

## Disclaimer

This script is provided as-is for the purpose of assisting individuals in rescheduling appointments. While it has been developed with care and with the intention of being helpful, it comes with no guarantees or warranties of any kind, either expressed or implied. By using this script, you acknowledge and agree that you are doing so at your own risk. The author(s) or contributor(s) of this script shall not be held liable for any direct or indirect damages that arise from its use. Please ensure that you understand the actions performed by this script before running it, and consider the ethical and legal implications of its use in your context.
