# ThunderPopper
A python application which gives you pop up and launches Thunderbird Email client when new mails arrive.

# How to Use
  - **Clone** this repo using ``git clone git@github.com:acetheultimate/ThunderPopper.git``
  - **Requirements** <sub><sup>You may have them already! Try skipping this step.</sup></sub>
    - **Install** dependencies. ``sudo apt-get install python3-gi python3-gi-cairo gir1.2-gtk-3.0 pkg-config libcairo2-dev``
    - **Install** requirements. ``pip install pygobject``
  - **Run** the app. ``./ThunderPopper.py``
  - To auto start the script at startup, follow the steps below,
      - Open Startup Application Preferences on Ubuntu.
      - Click on Add
      - Type alarmPop in column Name
      - Type /bin/bash -c "sleep 15 && cd /path/to/dir/ThunderPopper/; ./ThunderPopper.py >> /path/to/dir/ThunderPopper/out.txt" in column Command. You may also try cron or any other tool which run the script at startup.
 
Multi Account Syncing support coming up...  
Do let me know if anything breaks. Also, I'd very much appreciate any help or suggestion. Just fork it up and get started!
