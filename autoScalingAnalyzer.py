import boto3


class AutoScalingAnalyzer:
    '''Routine to Analyze IOP Provisioned volumes and calculate Gp2 Costs'''

    def __init__(self, **kwargs):
        self.region = kwargs['Region']
        self.accountId = kwargs['AccountId']
        self.accessKeyId = kwargs['AccessKeyId']
        self.secretKey = kwargs['SecretAccessKey']
        self.session = kwargs['SessionToken']

    def run(self):
        emptyGroups = []

        client = boto3.client('autoscaling', region_name=self.region,
                           aws_access_key_id=self.accessKeyId,
                           aws_secret_access_key=self.secretKey,
                           aws_session_token=self.session)
        autoScaleReponse = client.describe_auto_scaling_groups()

        while True:
            groups = autoScaleReponse['AutoScalingGroups']

            for group in groups:
                loadBalancers = client.describe_load_balancers(
                    group['AutoScalingGroupName'])['LoadBalancers']
                if len(group['Instances']) == 0 and len(loadBalancers) == 0:
                    emptyGroups.append({
                        'AutoScalingGroupARN': group['AutoScalingGroupARN'],
                        'AutoScalingGroupName': group['AutoScalingGroupName'],
                        'AvailabilityZones': group['AvailabilityZones']})

            if 'NextToken' in autoScaleReponse:
                autoScaleReponse = client.describe_auto_scaling_groups(
                    NextToken=autoScaleReponse['NextToken'])
            else:
                break

        return emptyGroups
