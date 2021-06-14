import boto3
import botocore
import json
import csv
import logging
import argparse

class EC2Tag:
    def __init__(self, tagName, tagValue):
        self.Key = tagName
        self.Value = tagValue
    def set_value(self, tagValue):
        self.Value = tagValue
    def get_value(self):
        return self.Value
    def get_tag(self):
        return {'Key':self.Key,'Value': self.Value}
    def __repr__(self):
        return f"{{'Key': {self.Key}','Value': '{self.Value}'}}"

class EC2Instance:
    def __init__(self, instanceId, tags=[]):
        self.instanceId = instanceId
        self.tags = tags  # creates a new empty list for of tags for the instance
    def get_instanceId(self):
        return self.instanceId
    def add_tag(self, tag):
        self.tags.append(tag)
    def get_tags(self):
        return self.tags
    def __repr__(self):
        return f"""Resources=[
            {self.get_instanceId()},
        ],
        Tags={self.get_tags()}
        """

def updateInstanceTags(client, ec2Instance):
    '''Updates tags of an EC2 instance
    '''
    response = client.create_tags(
        DryRun=False,
        Resources=[
            ec2Instance.get_instanceId(),
        ],
        Tags=[vars(tag) for tag in ec2Instance.get_tags()]
    )

def printTags(client):
    '''Prints the tags of all EC2 instances
    '''
    print("printTags not yet implemented")
    return 0

def validateTags(client, ec2InstancesList):
    '''Validates the tags of a list of EC2 instances, should print a list of all deviations.
    '''
    print("validateTags not yet implemented")
    return 0

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    #Parsing arguments
    parser = argparse.ArgumentParser(description="Update instance tags", prog='instance-tagger.py', usage='%(prog)s [options]')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-gt", "--gettags", action='count', help="Get all instance tags and print as CSV")
    group.add_argument("-ut", "--updatetags", type=str, help="Provide a CSV file and update all instance tags based on the file, format instance,tagname,tagvalue")
    group.add_argument("-vt", "--validatetags", type=str, help="Provide a CSV file and validate all instance tags based on the file, informs only deviations")
    args = parser.parse_args()

    ec2Instances = [] #Empty list of instances

    client = boto3.client('ec2')
    if ( args.gettags ):
        printTags(client)
    elif ( args.recordsfile ):
        with open(args.updatetags) as fp:
            line = fp.readline()
            while line:
                record = line.strip().split(',')
                if ( len(record)==3 ):
                    instanceId = record[0]
                    tagName = record[1]
                    tagValue = record[2]
                    if ( instanceId in ec2Instances ):
                        ec2Instances[instanceId].add_tag(EC2Tag(tagName, tagValue))
                    else:
                        ec2Instances.append(EC2Instance(instanceId, EC2Tag(tagName, tagValue)))
                elif ( len(record) > 0 ):
                    print(f"invalid record {record}")
                line = fp.readline()
    elif ( args.validaterecfile ):
        validateTags(client, "ec2InstancesList")