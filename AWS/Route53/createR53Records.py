import boto3
import botocore
import json
import csv
import logging
import argparse

def created_hostedzone_record(client, hostedZoneId, recordType, recordTTL, sourceName, targetName):
    '''Creates a record on a hosted zone
    first argument client is of class boto3.client.route53
    sourceName should be the short name as FQDN will be completed automatically
    Usage example: created_hostedzone_record(boto3.route53, '/hostedzone/QWEQWEQWE', 'A', 300, 'mydnsrecord', '10.0.0.1'):
    '''
    
    hostedZoneName=client.get_hosted_zone(Id=hostedZoneId)['HostedZone']['Name']
    response = client.change_resource_record_sets(
		HostedZoneId=hostedZoneId,
		ChangeBatch= {
						'Comment': 'add {0} -> {1}'.format(sourceName, targetName),

						'Changes': [
							{
							 'Action': 'UPSERT',
							 'ResourceRecordSet': {
								 'Name': '{0}.{1}'.format(sourceName, hostedZoneName),
								 'Type': recordType,
								 'TTL': recordTTL,
								 'ResourceRecords': [{'Value': targetName}]
							}
						}]
		})

def print_hostedZones(client):
    '''Prints hosted zones available on 
    first argument client is of class boto3.client.route53
    Usage example: print_hostedZones(boto3.route53):
    '''
    response = client.list_hosted_zones()
    for hostedZone in response['HostedZones']:
        print('{0}: {1}'.format(hostedZone['Id'], hostedZone['Name']))

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    #Parsing arguments
    parser = argparse.ArgumentParser(description="Create Route53 records", prog='createR53Records.py', usage='%(prog)s [options]')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-lz", "--listzones", action='count', help="List available hosted zones")
    group.add_argument("-rf", "--recordsfile", type=str, help="CSV file with records to create")
    group.add_argument("-vrf", "--validaterecfile", type=str, help="CSV file with records to validate")
    args = parser.parse_args()

    client = boto3.client('route53')
    if ( args.listzones ):
        print_hostedZones(client)
    elif ( args.recordsfile ):
        with open(args.recordsfile) as fp:
            line = fp.readline()
            while line:
                record = line.strip().split(',')
                if ( len(record)==5 ):
                    created_hostedzone_record(client, record[0], record[1], int(record[2]), record[3], record[4])
                line = fp.readline()
    elif ( args.validaterecfile ):
        print("validate records")

