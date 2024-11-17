#!/usr/bin/env python3

import settings
import sys
import argparse
from atproto import Client, client_utils, models
from atproto.exceptions import RequestException
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
        pprint( f'Attempting to write session to {sessionFile}' )
        with open(sessionFile, 'w') as f:
          f.write(session_string)
        print( f'Succeeded writing session to {sessionFile}' )
    except Exception as e:
      print( f'ERROR: Somethign went wrong: {e}')
      sys.exit(1)

  return client

def block_user(client=None, tgtUserHandle=None, tgtUserDID=None, dryRun=False):
  print( f'blocking user: {tgtUserHandle} with DID: {tgtUserDID}' )
  block_record = models.AppBskyGraphBlock.Record(
    subject=tgtUserDID,
    created_at=client.get_current_time_iso()
  )
  if not dryRun:
    try:
      result = client.app.bsky.graph.block.create(client.me.did, block_record)
      print( f'>> blocked user: {tgtUserHandle} with DID: {tgtUserDID}' )
    except RequestException as e:
      if e.args[0].status_code == '429':
        print("ERROR: We have been ratelimited. Aborting...")
        sys.exit(429)
      else:
        print( f'ERROR: Somethign went wrong: {e}')
    except Exception as e:
      print( f'ERROR: Somethign went wrong: {e}')

def add_user_to_blocklist(client=None, tgtUserHandle=None, tgtUserDID=None, listURI=None, dryRun=False):
  # It only works for normal lists, not moderation lists
  list_record = models.AppBskyGraphListitem.Record(
    subject=tgtUserDID,
    created_at=client.get_current_time_iso(),
    list=listURI,
  )
  if not dryRun:
    try:
      result = client.app.bsky.graph.listitem.create(client.me.did,list_record)
      print( f'>> Added user: {tgtUserHandle} with DID: {tgtUserDID} to block list ${listURI}' )
    except Exception as e:
      print( f'ERROR: Somethign went wrong: {e}')



def main():

  #arg parse flags
  parser = argparse.ArgumentParser(
    prog='blueSkyChainBlocking',
    description='Blocks everyone who follows the the target user.',
  )
  parser.add_argument('--blockfollowers', dest="blockFollowersOf", help="The username of the user who you want to block all their followers of.")
  parser.add_argument('--list', dest="listURI", help="The at:/ uri to a block list.")
  parser.add_argument('--dryrun', dest="dryRun", action='store_true', help="Do not actually execute the blocks.")
  parser.add_argument('--sessionFile', dest="sessionFile", default=None, help="optional session file to cache login. Useful to avoid rate limiting.")
  args = parser.parse_args()
  blockFollowersOf = args.blockFollowersOf
  dryRun=args.dryRun
  listURI=args.listURI
  sessionFile=args.sessionFile

  #login
  client = login(settings, sessionFile )

  #Get the followers of the tgt user
  data = client.get_profile(actor=blockFollowersOf)
  tgtDID = data.did

  print( f'Blocking all followers of username: {blockFollowersOf} with DID: {tgtDID}' )

  cursor = None
  followers = []
  #Loops over til the cursor returns blank
  while True:
    data = client.get_followers(actor=tgtDID,cursor=cursor)
    cursor = data.cursor
    followers.extend( data.followers )
    if not cursor:
      break

  #Loop through followers and start blocking
  for follower in followers:
    tgtUserHandle = follower.handle
    tgtUserDID = follower.did
    block_user(client=client, tgtUserHandle=tgtUserHandle, tgtUserDID=tgtUserDID, dryRun=dryRun)
  
    #Add users to the block list
    if listURI:
      add_user_to_blocklist(client=client, tgtUserHandle=blockFollowersOf, tgtUserDID=tgtDID, listURI=listURI, dryRun=dryRun)

  #Block the actual target
  block_user(client=client, tgtUserHandle=blockFollowersOf, tgtUserDID=tgtDID, dryRun=dryRun)

  #Add users to the block list
  if listURI:
    add_user_to_blocklist(client=client, tgtUserHandle=blockFollowersOf, tgtUserDID=tgtDID, listURI=listURI, dryRun=dryRun)


if __name__ == '__main__':
  main()
