import concurrent.futures
import boto3
import json
import logging
from typing import (
    Dict,
    List,
)
from autoScalingAnalyzer import AutoScalingAnalyzer

logger = logging.getLogger()
logger.setLevel(logging.WARNING)


class Iterator():

    def __init__(
            self,
            *,
            lambda_function: str = None,
            lambda_event: Dict = {},
            timeout: int = 15000,
            **kwargs,
    ):
        self.lambda_function = lambda_function
        self.lambda_event = lambda_event
        self.timeout = timeout

    def get_Access_Keys(self, roleId: str = '572481847476'):
        sts_connection = boto3.client('sts')
        acct = sts_connection.assume_role(
            RoleArn="arn:aws:iam::" + roleId +
                    ":role/CrossAccountRoleFromCentralAccount",
            RoleSessionName="CrossAccountRoleFromCentralAccount"
        )
        ACCESS_KEY = acct['Credentials']['AccessKeyId']
        SECRET_KEY = acct['Credentials']['SecretAccessKey']
        SESSION_TOKEN = acct['Credentials']['SessionToken']

        return {'AccessKey': ACCESS_KEY, 'SecretKey': SECRET_KEY, 'SessionToken': SESSION_TOKEN}

    def get_Regions(self, accessKeys):
        ec2 = boto3.client('ec2',
                           aws_access_key_id=accessKeys['AccessKey'],
                           aws_secret_access_key=accessKeys['SecretKey'],
                           aws_session_token=accessKeys['SessionToken'])
        regions_List = []
        awsregions = ec2.describe_regions()
        awsregions_list = awsregions['Regions']
        for region in awsregions_list:
            regions_List.append(region['RegionName'])
        return regions_List

    def run(self):
        accessKeys = self.get_Access_Keys()
        client = boto3.client(
            'organizations',
            aws_access_key_id=accessKeys['AccessKey'],
            aws_secret_access_key=accessKeys['SecretKey'],
            aws_session_token=accessKeys['SessionToken']
        )

        accountResponse = client.list_accounts()

        for account in accountResponse['Accounts']:
            accessKeys = self.get_Access_Keys(account['Id'])
            regions = self.get_Regions(accessKeys)

            with concurrent.futures.ThreadPoolExecutor(len(regions)) as executor:
                autoScalingAnalyzer = AutoScalingAnalyzer()
                invoke_futures = [
                    executor.submit(autoScalingAnalyzer.run())
                    for region in regions
                ]

                for future in concurrent.futures.as_completed(invoke_futures):
                    invocation = future.result()
