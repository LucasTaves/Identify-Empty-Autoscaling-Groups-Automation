import json
from autoScalingAnalyzer import AutoScalingAnalyzer

def lambda_handler(event, context):
    autoScalingAnalyzer = AutoScalingAnalyzer(**event)
    return autoScalingAnalyzer.run()