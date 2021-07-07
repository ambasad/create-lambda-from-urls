import os
import urllib.request
from urllib.parse import urlparse
import json
import boto3
import cfnresponse
import zipfile

print('Loading function')

s3 = boto3.resource('s3')


def save_to_local(url):
    urlPath = urlparse(url).path
    fileName = os.path.basename(urlPath)
    filePath = '/tmp/' + fileName
    urllib.request.urlretrieve(url, filePath)
    return filePath, fileName


def upload_to_s3(filePath, bucket):
    fileName = os.path.basename(filePath)
    s3.Object(bucket, fileName).put(Body=open(filePath, 'rb'))


def copy_to_s3(url, bucket, zipFilePath):
    filePath, fileName = save_to_local(url)
    upload_to_s3(filePath, bucket)
    with zipfile.ZipFile(zipFilePath, "a", zipfile.ZIP_DEFLATED) as zf:
        zf.write(filePath, fileName)

def lambda_handler(event, context):
    print('Received event: ' + json.dumps(event, indent=2))

    if event['RequestType'] == 'Create':
        # get the properties set in the CloudFormation resource
        properties = event['ResourceProperties']
        urls = properties['Urls']
        bucket = properties['S3BucketName']
        zipFileName = properties['ZipFileName']

        try:
            zipFilePath = '/tmp/' + zipFileName
            for url in urls:
                copy_to_s3(url, bucket, zipFilePath)
            s3.Bucket(bucket).upload_file(zipFilePath, zipFileName)

        except Exception as e:
            print(e)
            cfnresponse.send(event, context, cfnresponse.FAILED, {
                            'Response': 'Failure'})
            return

    cfnresponse.send(event, context, cfnresponse.SUCCESS,
                    {'Response': 'Success'})