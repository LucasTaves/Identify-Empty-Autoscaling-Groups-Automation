import concurrent.futures
import boto3
import json
import logging
from typing import (
    Dict,
    List,
)

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

    def lambda_client(self):
        '''Instantiate a thread-safe Lambda client'''
        session = boto3.session.Session()
        return session.client('lambda')

    def invoke_lambda(self,
                      *,
                      function_name: str,
                      payload,
                      invocation_type: str,
                      log_type: str = 'None',
                      ) -> Dict:
        '''Invoke a Lambda function

        :arg function_name: name of the function to invoke
        :arg invocation_type: one of these options:
            'RequestResponse': synchronous call, will wait for Lambda processing
            'Event': asynchronous call, will NOT wait for Lambda processing
            'DryRun': validate param values and user permission
        :arg payload: payload data to submit to the Lambda function
        :arg log_type: one of these options:
            'None': does not include execution logs in the response
            'Tail': includes execution logs in the response
        '''
        aws_lambda = self.lambda_client()

        response = aws_lambda.invoke(
            FunctionName=function_name,
            InvocationType=invocation_type,
            LogType=log_type,
            Payload=json.dumps(payload),
        )

        # Decode response payload
        try:
            payload = response['Payload'].read(amt=None).decode('utf-8')
            response['Payload'] = json.loads(payload)

        except (TypeError, json.decoder.JSONDecodeError):
            logger.warning('Unable to parse Lambda Payload JSON response.')
            response['Payload'] = None

        return response

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
                invoke_futures = [
                    executor.submit(self.invoke_lambda(function_name=self.lambda_function,
                                                       payload=self.lambda_event, invocation_type='RequestResponse',
                                                       log_type='Tail'))
                    for region in regions
                ]

                for future in concurrent.futures.as_completed(invoke_futures):
                    invocation = future.result()
