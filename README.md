#API Token
* Goto https://bsky.app/settings/app-passwords and create an APP Password
* Copy the info into settings.py (see settings.py.example)
* For login, use the handle without the @ (example bsky.app for https://bsky.app/profile/bsky.app)
* For password, use the APP Password created at step 1

#UNIX
* on Unix systems, use python3 instead of python command

#Install
* Create virtual env and activate it with the following command
  * python -m venv .venv
* pip install -r requirements.txt

#USAGE
* Check if given user is blocked by reference user
  * Reuses session if possible to avoid rate limiting.
  * Sleeps 1 sec between commands to avoid spamming api endpoint
  * did : given user
  * handle : reference user
  * sessionFile : optional session file to cache login
  * `python .\blueSkyIsBlocked.py  --did="did:plc:m5ibvdgcxm4y5psuttiukunj"  --handle="did:plc:vcds5wbo25cln5wx5ttd4vjx"  --sessionFile=./session.txt --sleep=1`
  * Here, the script will check if --did user is blocked by --handle user
