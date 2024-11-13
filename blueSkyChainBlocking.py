#!/usr/bin/env python3

import settings
import argparse
from atproto import Client, client_utils, models
from pprint import pprint


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

    #Get the followers of the tgt user
    data = client.get_profile(actor=blockFollowersOf)
    did = data.did
    display_name = data.display_name

    print( f'Blocking all followers of username: {display_name} with DID: {did}' )

    cursor = None
    followers = []
    #Loops over til the cursor returns blank
    while True:
        data = client.get_followers(actor=did,cursor=cursor)
        cursor = data.cursor
        followers.extend( data.followers )
        if not cursor:
            break

    #Loop through followers and start blocking
    for follower in followers:
        tgtUserHandle = follower.handle
        tgtUserDID = follower.did
        print( f'blocking user: {tgtUserHandle} with DID: {tgtUserDID}' )
        block_record = models.AppBskyGraphBlock.Record(
            subject=tgtUserDID, 
            created_at=client.get_current_time_iso()
        )
        if not dryRun:
            pprint( "Actually Blocking" )
            #uri = client.app.bsky.graph.block.create(client.me.did, block_record).uri


if __name__ == '__main__':
    main()
