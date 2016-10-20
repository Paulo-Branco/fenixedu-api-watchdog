#FenixEdu API Watchdog

This script will perform periodic checks on some external API endpoints and report any problems found to a set of provided email addresses.

## Checked Endpoints
 - /Parking  -  For each park, the "updated" field is checked. If more than 24 hours have passed since the last update, the test fails, triggering an email to the responsible entity.
 
## Configuration
To configure the watchdog, start by renaming the config.py.sample:
```sh
cp config.py.sample config.py
```

Then edit the file to fill in the destination email addresses and content.
 
## Usage
```python
python watchdog.py
```