import boto3


class AutoScalingAnalyzer:
    '''Routine to Analyze IOP Provisioned volumes and calculate Gp2 Costs'''

    def __init__(self, **kwargs):
        print("Initialized")

    def run(self):
        autoScale = boto3.client('autoscaling')
        autoScaleReponse = autoScale.describe_auto_scaling_groups()
        emptyGroups = []

        while True:
            groups = autoScaleReponse['AutoScalingGroups']

            for group in groups:
                loadBalancers = autoScale.describe_load_balancers(
                    group['AutoScalingGroupName'])['LoadBalancers']
                if len(group['Instances']) == 0 and len(loadBalancers) == 0:
                    emptyGroups.append({
                        'AutoScalingGroupARN': group['AutoScalingGroupARN'],
                        'AutoScalingGroupName': group['AutoScalingGroupName'],
                        'AvailabilityZones': group['AvailabilityZones'][0]})

            if autoScaleReponse['NextToken']:
                autoScaleReponse = autoScale.describe_auto_scaling_groups(
                    NextToken=autoScaleReponse['NextToken'])
            else:
                break

        return emptyGroups
