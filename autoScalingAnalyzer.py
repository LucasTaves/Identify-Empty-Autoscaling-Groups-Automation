import boto3


class AutoScalingAnalyzer:
    '''Routine to Analyze IOP Provisioned volumes and calculate Gp2 Costs'''

    def __init__(self, **kwargs):
        ec2 = boto3.client('ec2')
        self.regions = [region['RegionName']
                        for region in ec2.describe_regions()['Regions']]

    def run(self):
        emptyGroups = []

        for region in self.regions:
            client = boto3.client('autoscaling', region_name=region)
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
