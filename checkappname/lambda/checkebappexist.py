import json
import boto3
import cfnresponse
import logging
import signal

def handler(event, context):
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Setup alarm for remaining runtime minus a second
    signal.alarm((context.get_remaining_time_in_millis() / 1000) - 1)

    # initialize our responses, assume failure by default

    response_data = {}
    response_status = cfnresponse.FAILED

    logger.info('Received event: {}'.format(json.dumps(event)))
    try:
        if event['RequestType'] == 'Delete' or event['RequestType'] == 'Create' or event['RequestType'] == 'Update':
            response_status = cfnresponse.SUCCESS
    except Exception as e:
        logger.info('Exception during processing: {}'.format(e))
    
    try:
        eb = boto3.client('elasticbeanstalk')
    except Exception as e:
        logger.info('boto3.client failure: {}'.format(e))
        cfnresponse.send(event, context, response_status, response_data)

    app_name = event['ResourceProperties']['NameFilter']
    try:
        apps = eb.describe_applications(ApplicationNames=[app_name])
        # apps = eb.describe_applications()
    except Exception as e:
        logger.info('eb.describe_applications failure: {}'.format(e))
        cfnresponse.send(event, context, response_status, response_data)

    logger.info('{}'.format(apps))
    number_of_apps = len(apps['Applications'])
    logger.info('number of applications returned: {}'.format(number_of_apps))

    if number_of_apps == 1:
        response_data['AppExist'] = "true"
        response_status = cfnresponse.SUCCESS
        cfnresponse.send(event, context, response_status, response_data)

    elif number_of_apps == 0:
        response_data['AppExist'] = "false"
        logger.info('no matching applcation name for filter {}'.format(app_name))
        cfnresponse.send(event, context, response_status, response_data)

    else:
        logger.info('multiple matching applcation name for filter {}'.format(app_name))
        cfnresponse.send(event, context, response_status, response_data)

def timeout_handler(_signal, _frame):
    '''Handle SIGALRM'''
    raise Exception('Time exceeded')


signal.signal(signal.SIGALRM, timeout_handler)