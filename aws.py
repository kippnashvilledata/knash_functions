import boto3

""" Function for Moving Files to AWS S3 Bucket """

def upload_to_s3(source_file, bucket_name, destination_path, access_key_id, access_secret_key):
    """ Function to move files to AWS S3 Bucket """
    s3 = boto3.resource('s3', aws_access_key_id=access_key_id, aws_secret_access_key=access_secret_key)
    s3.meta.client.upload_file(source_file, bucket_name, destination_path)

if __name__ == "__main__":
    print("This code is being run directly.")