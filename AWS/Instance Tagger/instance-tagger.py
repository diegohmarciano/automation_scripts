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
    def get_key(self):
        return self.Key
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
        return f"""(Resources=[
            {self.get_instanceId()},
        ],
        Tags={self.get_tags()})
        """
    def __eq__(self, other):
        return self.instanceId == other


def updateInstanceTags(client, ec2Instance, dryRunFlag):
    '''Updates tags of an EC2 instance
    '''
    try:
        response = client.create_tags(
            DryRun=dryRunFlag,
            Resources=[
                ec2Instance.get_instanceId(),
            ],
            Tags=[vars(tag) for tag in ec2Instance.get_tags()]
        )
    except botocore.exceptions.ClientError as e:
        logging.warning(f"{ec2Instance.get_instanceId()}: {e.response['Error']['Code']}")
        logging.warning(f"{ec2Instance.get_instanceId()}: {e.response['Error']['Message']}")
        return False
    logging.info(f"EC2 Instance {ec2Instance.get_instanceId()} successfully updated")
        
def getTags():
    '''Prints the tags of all EC2 instances
    '''
    ec2Instances = {}
    ec2 = boto3.resource('ec2')
    for instance in ec2.instances.all():
        ec2Instances[instance.id] = EC2Instance(instance.id, [EC2Tag(tag["Key"], tag["Value"]) for tag in instance.tags])
    return ec2Instances

def printTags(ec2Instances):
    [[logger.info(f'"{instance.get_instanceId()}","{tag.get_key()}","{tag.get_value()}"') for tag in instance.get_tags()] for instance in ec2Instances.values()]
    return False
            
def validateTags(client, ec2InstancesList):
    '''Validates the tags of a list of EC2 instances, should print a list of all deviations.
    '''
    logging.error("validateTags not yet implemented")
    return False

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    #Parsing arguments
    parser = argparse.ArgumentParser(description="Update instance tags", prog='instance-tagger.py', usage='%(prog)s [options]')
    parser.add_argument('-dr', '--dryrun', action='store_true', help="Dry Run flag, when step changes are not persisted")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-gt", "--gettags", action='count', help="Get all instance tags and print as CSV")
    group.add_argument("-ut", "--updatetags", type=str, help="Provide a CSV file and update all instance tags based on the file, format instance,tagname,tagvalue")
    group.add_argument("-vt", "--validatetags", type=str, help="Provide a CSV file and validate all instance tags based on the file, informs only deviations")
    args = parser.parse_args()

    ec2Instances = {} #Empty dict of instances

    client = boto3.client('ec2')
    if ( args.gettags ):
        printTags(getTags())
    elif ( args.updatetags ):
        with open(args.updatetags, newline='') as fp:
            csvreader = csv.reader(fp, quotechar='"', delimiter=',',quoting=csv.QUOTE_ALL, skipinitialspace=True)
            for record in csvreader:
                if ( len(record)==3 ):
                    instanceId = record[0]
                    tagName = record[1]
                    tagValue = record[2]
                    if ( instanceId in ec2Instances ):
                        ec2Instances[instanceId].add_tag(EC2Tag(tagName, tagValue))
                    else:
                        ec2Instances[instanceId] = EC2Instance(instanceId, [EC2Tag(tagName, tagValue)])
                elif ( len(record) > 0 ):
                    print(f"invalid record {record}")
            [updateInstanceTags(client, ec2Instance, args.dryrun) for ec2Instance in ec2Instances.values()]
    elif ( args.validatetags ):
        validateTags(client, "ec2InstancesList")