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
    def __eq__(self, other):
        return self.Key == other.Key and self.Value == other.Value


class EC2Instance:
    def __init__(self, instanceId, tags=[]):
        self.instanceId = instanceId
        self.tags = tags  # creates a new empty list for of tags for the instance
        self.primaryIP = ""
        self.ami = ""
        self.state = ""
    def get_instanceId(self):
        return self.instanceId
    def add_tag(self, tag):
        self.tags.append(tag)
    def get_tags(self):
        return self.tags
    def getPrimIP(self):
        return self.primaryIP
    def getAmiID(self):
        return self.ami
    def getState(self):
        return self.state
    def setPrimIP(self, primIp):
        self.primaryIP=primIp
    def setAmiID(self, amiID):
        self.ami=amiID
    def setState(self, state):
        self.state=state
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

def getInstanceDetails():
    '''Prints the tags of all EC2 instances
    '''
    ec2Instances = getTags()
    ec2 = boto3.resource('ec2')
    for instance in ec2.instances.all():
        ec2Instances[instance.id].setPrimIP(instance.private_ip_address)
        ec2Instances[instance.id].setAmiID(instance.image_id)
        ec2Instances[instance.id].setState(instance.state['Name'])
    return ec2Instances

def printTags(ec2Instances):
    [[logging.info(f'"{instance.get_instanceId()}","{tag.get_key()}","{tag.get_value()}"') for tag in instance.get_tags()] for instance in ec2Instances.values()]
    return False

def printDetailed(ec2Instances):
    [[logging.info(f'"{instance.get_instanceId()}","{instance.getState()}","{instance.getPrimIP()}","{instance.getAmiID()}","{tag.get_key()}","{tag.get_value()}"') for tag in instance.get_tags()] for instance in ec2Instances.values()]
    return False

def parseTagsCsv(csvFile):
    ec2Instances = {}
    with open(csvFile, newline='') as fp:
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
                logging.error(f"invalid record {record} in line {csvreader.line_num}")
    return ec2Instances
            
def validateTags(client, awsInstances, csvInstances):
    '''Validates the tags of a list of EC2 instances, should print a list of all deviations.
    '''
    for instance in csvInstances:
        instanceExists = (instance in awsInstances)
        logging.info(f"Instance {instance} exists in AWS: {instanceExists}")
        if instanceExists:
            awsInstance = awsInstances[instance] 
            for tag in csvInstances[instance].get_tags():
                if tag in awsInstance.get_tags():
                    logging.info(f"{instance}:{tag.get_key()} consistent")   
                else:
                    logging.warning(f"{instance}:{tag.get_key()} not consistent")
    return False

if __name__=="__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()

    #Parsing arguments
    parser = argparse.ArgumentParser(description="Update instance tags", prog='instance-tagger.py', usage='%(prog)s [options]')
    parser.add_argument('-dr', '--dryrun', action='store_true', help="Dry Run flag, when step changes are not persisted")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-gt", "--gettags", action='count', help="Get all instance tags and print as CSV")
    group.add_argument("-gd", "--getdetailed", action='count', help="Get all instance tags with instance details and print as CSV")
    group.add_argument("-ut", "--updatetags", type=str, help="Provide a CSV file and update all instance tags based on the file, format instance,tagname,tagvalue")
    group.add_argument("-vt", "--validatetags", type=str, help="Provide a CSV file and validate all instance tags based on the file, informs only deviations")
    args = parser.parse_args()

    client = boto3.client('ec2')
    if ( args.gettags ):
        printTags(getTags())
    elif ( args.getdetailed ):
        printDetailed(getInstanceDetails())
    elif ( args.updatetags ):
            [updateInstanceTags(client, ec2Instance, args.dryrun) for ec2Instance in parseTagsCsv(args.updatetags).values()]
    elif ( args.validatetags ):
        validateTags(client, getTags(), parseTagsCsv(args.validatetags))