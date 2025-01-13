#!/usr/bin/env python3

import settings
import sys
import argparse
from atproto import Client, client_utils, models
from atproto.exceptions import RequestException
from time import sleep
from datetime import datetime
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
    prog='blueSkyChainBlocking',
    description='Blocks everyone who follows the the target user.',
  )
  parser.add_argument('--likes', dest="likesOlderThan", help="Likes older then X days.",default=30)
  parser.add_argument('--dryrun', dest="dryRun", action='store_true', help="Do not actually execute the blocks.")
  parser.add_argument('--sessionFile', dest="sessionFile", default=None, help="optional session file to cache login. Useful to avoid rate limiting.")

  args = parser.parse_args()
  likesOlderThan = int( args.likesOlderThan )
  dryRun=args.dryRun
  sessionFile=args.sessionFile

  #login
  client = login(settings, sessionFile )

  #Get the followers of the tgt user
  if likesOlderThan > 0:
    myDID = client.me.did
    cursor = None
    feeds = []

    #Loops over til the cursor returns blank
    while True:
      params={'actor': myDID, 'cursor': cursor}
      data = client.app.bsky.feed.get_actor_likes(params)
      cursor = data.cursor
      feeds.extend( data.feed )
      if not cursor:
        break
      if len( data.feed ) == 0:
        break
      feedCount = len(feeds)
      print( f'Loaded {feedCount} records' )


    now = datetime.now()
    for feed in feeds:
      post = feed.post
      uri = post.viewer.like
      record = post.record
      likedAt = record.created_at
      likedAtDateTime = datetime.strptime(likedAt, '%Y-%m-%dT%H:%M:%S.%fZ')
      timeDelta = now - likedAtDateTime

      if timeDelta.days >= likesOlderThan:
        print( f'{uri} {likedAt}' )
        if not dryRun:
          try:
            print( f'>> Unliking post: {uri} , liked {timeDelta.days} ago with date: {likedAt} ' )
            client.unlike( uri )
          except RequestException as e:
            if e.args[0].status_code == 429:
              print("ERROR: We have been ratelimited. Aborting...")
              sys.exit(429)
            else:
              print( f'ERROR: RequestException Something went wrong: {e}')
          except Exception as e:
            print( f'ERROR: Exception Something went wrong: {e}')


if __name__ == '__main__':
  main()
