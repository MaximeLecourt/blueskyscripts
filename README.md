#API Token
* Goto https://bsky.app/settings/app-passwords and create an APP Password
* Copy the info into settings.py (see settings.py.example)

#Install
* Create virtual env and activate it
* pip install -r requirements.txt

#USAGE
* Block followers of a user (Chain Blocking):
  * Reuses session if possible to avoid rate limiting.
  * Sleeps 1 sec between blocks to avoid spamming api endpoint
  * `python3 blueSkyChainBlocking.py  --blockfollowers=${userNameToBlock}  --sessionFile=./session.txt  --sleep=1`
* Block but also add your users to a list of yours (moderation or normal)
  * `python3 blueSkyChainBlocking.py  --blockfollowers=${userNameToBlock}  --list=${nameOfYourList} --sessionFile=./session.txt  --sleep=1`
* Block all memebers of a list:
  * `python3 blueSkyChainBlocking.py  --blockBlockListMembersofURL=${URLofList}  --sessionFile=./session.txt  --sleep=1`

