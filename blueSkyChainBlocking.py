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
      if e.args[0].status_code == 429:
        print("ERROR: We have been ratelimited. Aborting...")
        sys.exit(429)
      else:
        print( f'ERROR: RequestException Something went wrong: {e}')
    except Exception as e:
      print( f'ERROR: Exception Something went wrong: {e}')

def add_user_to_blocklist(client=None, tgtUserHandle=None, tgtUserDID=None, listURI=None, dryRun=False):
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
      print( f'ERROR: Something went wrong: {e}')

def get_list_at( listName=None, listURL=None, client=None):
    at_uri = None

    if listURL:
      listURLSplit = listURL.split('/')
      actor = listURLSplit[4]
      listID = listURLSplit[6]
    else:
      actor = client.me.did
      listID = None

    params={'actor': actor}
    myLists =  client.app.bsky.graph.get_lists(params)

    for myList in myLists['lists']:
      if listID:
        if listID in myList.uri:
          at_uri = myList.uri
      elif myList.name == listName:
        at_uri = myList.uri
    return at_uri

def get_list_members( listAT=None, client=None ):
    listMembers = []
    cursor=None

    #Loops over til the cursor returns blank
    while True:
      params={'list': listAT, 'cursor': cursor }
      data = client.app.bsky.graph.get_list(params)
      cursor = data.cursor
      listMembers.extend( data.items )
      if not cursor:
        break

    return listMembers


def main():

  #arg parse flags
  parser = argparse.ArgumentParser(
    prog='blueSkyChainBlocking',
    description='Blocks everyone who follows the the target user.',
  )
  parser.add_argument('--blockfollowers', dest="blockFollowersOf", help="The username of the user who you want to block all their followers of.")
  parser.add_argument('--list', dest="listName", help="The name of the list.")
  parser.add_argument('--listURI', dest="listURI", help="The at:/ uri to a block list.")
  parser.add_argument('--dryrun', dest="dryRun", action='store_true', help="Do not actually execute the blocks.")
  parser.add_argument('--sessionFile', dest="sessionFile", default=None, help="optional session file to cache login. Useful to avoid rate limiting.")
  parser.add_argument('--sleep', dest="sleepBetweenBlocks", default=1, help="optional time to delay between blocks to avoid rate limit. Default: 1")
  parser.add_argument('--blockBlockListMembersofURL', dest="blockMembersListUrl", default=None, help="Block all members of Block list.")

  args = parser.parse_args()
  blockFollowersOf = args.blockFollowersOf.replace('@','')
  dryRun=args.dryRun
  listName=args.listName
  listURI=args.listURI
  sessionFile=args.sessionFile
  sleepBetweenBlocks=int(args.sleepBetweenBlocks)
  blockMembersListUrl=args.blockMembersListUrl

  #login
  client = login(settings, sessionFile )

  #Get the followers of the tgt user
  if blockFollowersOf:
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
  else:
    followers=None

  #Block the actual target
  if blockFollowersOf and tgtDID:
    #Get the list at:// uri
    if listName:
      listURI = get_list_at( listName=listName, client=client)
      print( listURI )
    if listName and not listURI:
      print( f'ERROR: List {listName} not found' )
      sys.exit(1)

    block_user(client=client, tgtUserHandle=blockFollowersOf, tgtUserDID=tgtDID, dryRun=dryRun)
  
    #Add users to the block list
    if listURI:
      add_user_to_blocklist(client=client, tgtUserHandle=blockFollowersOf, tgtUserDID=tgtDID, listURI=listURI, dryRun=dryRun)

    #Loop through followers and start blocking
    for follower in followers:
      tgtUserHandle = follower.handle
      tgtUserDID = follower.did
      sleep(sleepBetweenBlocks)
      block_user(client=client, tgtUserHandle=tgtUserHandle, tgtUserDID=tgtUserDID, dryRun=dryRun)
  
      #Add users to the block list
      if listURI:
        add_user_to_blocklist(client=client, tgtUserHandle=tgtUserHandle, tgtUserDID=tgtUserDID, listURI=listURI, dryRun=dryRun)

  #Block memebers of list
  if blockMembersListUrl and not followers:
    count = 0
    listURI = get_list_at( listURL=blockMembersListUrl, client=client)
    print( listURI )
    listMembers = get_list_members( listAT=listURI, client=client )
    for listMember in listMembers:
      tgtUserHandle = listMember.subject.handle
      tgtUserDID = listMember.subject.did
      count = count + 1
      sleep(sleepBetweenBlocks)
      block_user(client=client, tgtUserHandle=tgtUserHandle, tgtUserDID=tgtUserDID, dryRun=dryRun)



if __name__ == '__main__':
  main()
