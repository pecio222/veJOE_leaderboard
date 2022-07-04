


Website hosted on [vejoedashboard.pythonanywhere.com](https://vejoedashboard.pythonanywhere.com). Somehow it still shows data until 20.06, even if it's not paid anymore.
Developed for veJOE Leaderboard Bounty in April 2022. Not developed anymore both because of existing better alternatives, lack of interest, and absolute decimation of competitors by Vector Finance. Not updated to exclude deprecated farms.


Please don't look at code quality/cleanliness - this wasn't refactored for months, and my skills in this matter improved greatly. Seriously.


To install locally and see current data:


1. Clone the repo
   ```sh
   git clone https://github.com/pecio222/TODO.git
   ```
2. Install dependencies
   ```sh
   pip3 install -r requirements.txt
   ```
3. Run the update process
    ```sh
   python .\data_updater.py
   ```
4. Start the website
    ```sh
   python .\dash1.py
   ```



