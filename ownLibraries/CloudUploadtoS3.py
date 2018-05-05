#!/usr/bin/python3

import os
import sys
import boto3


class UploadToS3():
	"""
	Upload Files from a local folder to  a S3 folder with name <destination>
	"""
	@staticmethod
	def upload(local_directory, bucket, destination):

		s3_client = boto3.client('s3')

		# enumerate local files recursively
		for root, dirs, files in os.walk(local_directory):
			for filename in files:
				
				# construct the full local path
				local_path = os.path.join(root, filename)

				# construct the full S3 path
				relative_path = os.path.relpath(local_path, local_directory)
				s3_path = os.path.join(relative_path)
				try:
					print ("Uploading {} to  {}...".format( local_path, bucket +'/'+ destination + '/' + s3_path))

					s3_client.upload_file(local_path, bucket, databases + '/' + s3_path)
				except Exception as e:
					print('ERROR in Upload:::', e)
				
				# try:
					# client.delete_object(Bucket=bucket, Key=s3_path)
				# except:
					# print "Unable to delete %s..." % s3_path
					

				

if __name__ == '__main__':
	local_directory, bucket, destination = sys.argv[1:4]

	upload = UploadToS3()

	upload.upload(local_directory, bucket, destination)