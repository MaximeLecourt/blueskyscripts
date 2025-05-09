#!/usr/bin/env python3

import settings
import sys
import argparse
from atproto import Client, client_utils, models
from atproto.exceptions import RequestException
from time import sleep
from pprint import pprint

def login(settings=None,sessionFile=None):
  client = Client()
  profile = None

  if sessionFile:
    try:
      print( f'Attempting to read session from {sessionFile}' )
      with open(sessionFile, 'r') as f:
        session_string = f.read()
      profile = client.login(session_string=session_string)
      print( f'Succeeded reading session from {sessionFile}' )
    except FileNotFoundError as e:
      print( f'Session file {sessionFile} does not exist, will try logging in' )
    except Exception as e:
      client = Client() 
      print( f'Failed logging in from session file {sessionFile}, will try re-logging in' )

  if not profile:
    try:
      print( f'Attempting to login with username/password' )
      profile = client.login(settings.login,settings.password)
      session_string = client.export_session_string()
      print( f'Succeeded logging in with username/password' )
      if sessionFile:
        print( f'Attempting to write session to {sessionFile}' )
        with open(sessionFile, 'w') as f:
          f.write(session_string)
        print( f'Succeeded writing session to {sessionFile}' )
    except Exception as e:
      print( f'ERROR: Somethign went wrong: {e}')
      sys.exit(1)

  return client

def main():

  #arg parse flags
  parser = argparse.ArgumentParser(
    prog='blueSkyIsBlocked',
    description='Check if user is blocked by another specific user',
  )
  parser.add_argument('--did', dest="tgtUserDID", help="The DID of the user you want to check.")
  parser.add_argument('--handle', dest="refUserDID", help="The user you are using as reference.")
  parser.add_argument('--sessionFile', dest="sessionFile", default=None, help="optional session file to cache login. Useful to avoid rate limiting.")
  
  args = parser.parse_args()
  tgtUserDID = args.tgtUserDID
  refUserDID = args.refUserDID.replace('@','')
  sessionFile=args.sessionFile

  #login
  client = login(settings, sessionFile)

  
  # get list of accounts blocked by the reference user
  blocked_accounts = client.app.bsky.graph.block.list(repo=refUserDID)
  #print(f"Blocked accounts by {refUserDID}:")
  #print(blocked_accounts)

  # Check if the target user is in the list of blocked accounts
  is_blocked = any(record.subject == tgtUserDID for record in blocked_accounts.records.values())

  if is_blocked:
    print(f"The user {tgtUserDID} is blocked by {refUserDID}.")
  else:
    print(f"The user {tgtUserDID} is not blocked by {refUserDID}.")

if __name__ == '__main__':
  main()
