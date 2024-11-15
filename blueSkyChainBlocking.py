#!/usr/bin/env python3

import settings
import argparse
from atproto import Client, client_utils, models
from pprint import pprint


def block_user(client=None, tgtUserHandle=None, tgtUserDID=None, dryRun=False):
    print( f'blocking user: {tgtUserHandle} with DID: {tgtUserDID}' )
    block_record = models.AppBskyGraphBlock.Record(
        subject=tgtUserDID,
        created_at=client.get_current_time_iso()
    )
    if not dryRun:
        try:
            #uri = client.app.bsky.graph.block.create(client.me.did, block_record).uri
            print( f'>> blocked user: {tgtUserHandle} with DID: {tgtUserDID}' )
        except Exception as e:
            print( f'ERROR: Somethign went wrong: {e}')

def main():

    #arg parse flags
    parser = argparse.ArgumentParser(
        prog='blueSkyChainBlocking',
        description='Blocks everyone who follows the the target user.',
    )
    parser.add_argument('--blockfollowers', dest="blockFollowersOf", help="The username of the user who you want to block all their followers of")
    parser.add_argument('--dryrun', dest="dryRun", action='store_true', help="Do not actually execute the blocks")
    args = parser.parse_args()
    blockFollowersOf = args.blockFollowersOf
    dryRun=args.dryRun

    #Login
    client = Client()
    profile = client.login(settings.login,settings.password)
    myDID = profile.did

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


    #Block the actual target
    block_user(client=client, tgtUserHandle=blockFollowersOf, tgtUserDID=tgtDID, dryRun=dryRun)


if __name__ == '__main__':
    main()
