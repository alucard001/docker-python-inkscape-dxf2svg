from flask import Flask
from flask import request
from werkzeug.utils import environ_property, secure_filename

import boto3
from botocore.config import Config

import os
import uuid
import subprocess

app = Flask(__name__)

@app.route("/inkscape/dxf2svg", methods=['POST'])
def dxf2svg():
    try:
        # Access S3 repo from HTTP header
        # app.logger.info("X-Amz-Key: " + request.headers.get("X-Amz-Key"))
        aws_public_key = request.headers.get("x-Amz-Key")
        if( aws_public_key is None ):
            raise ValueError("aws_public_key is empty or not set")
        # else:
        #     app.logger.info("aws_public_key: " + aws_public_key)

        # app.logger.info("x-Amz-Secret: " + request.headers.get("x-Amz-Secret"))
        aws_secret = request.headers.get("x-Amz-Secret")
        if( aws_secret is None ):
            raise ValueError("aws_secret is empty or not set")
        # else:
        #     app.logger.info("aws_secret: " + aws_secret)

        # This is the full path to the dxf file in S3
        # app.logger.info("dxf_file: " + request.form['dxf_file'])
        dxf_file = request.form['dxf_file']
        if( dxf_file is None ):
            raise ValueError("dxf_file is empty or not set")
        else:
            app.logger.info("dxf_file: " + dxf_file)

        s3_bucket = request.form['s3_bucket']
        if( s3_bucket is None ):
            raise ValueError("s3_bucket is empty or not set")
        else:
            app.logger.info("s3_bucket: " + s3_bucket)

        # Read dxf file from S3
        client = boto3.client('s3',
                    aws_access_key_id=aws_public_key,
                    aws_secret_access_key=aws_secret,
                    region_name="ap-east-1"
                )

        s3_resp = client.get_object(
            ResponseCacheControl="no-cache",
            Bucket=s3_bucket,   # vep-dev-wordpress
            Key=dxf_file,   # hkjewellery/efloorplan/01-hall1_option2_fence1.dxf
        )

        # https://stackoverflow.com/a/68459143/1802483
        dxf_ctn = s3_resp['Body'].read().decode("utf-8")

        # save it to a temporary place
        str_uuid = str(uuid.uuid4())
        dxf_local_filename = str_uuid + ".dxf"
        svg_local_filename = str_uuid + ".svg"

        s3_svg_path = dxf_file.replace(".dxf", ".svg")

        with open(dxf_local_filename, "w") as _dxf:
            _dxf.write(dxf_ctn)
            _dxf.close()

        app.logger.info("dxf_local_filename: " + dxf_local_filename)
        app.logger.info("svg_local_filename: " + svg_local_filename)
        app.logger.info("s3_svg_path: " + s3_svg_path)

        # run command to convert dxf to svg: Linux only
        #   ./inkscape/usr/bin/python ./inkscape/usr/share/inkscape/extensions/dxf_input.py truelove5.dxf --output=dev_truelove5.svg --scalemethod=auto

        # str_command = f"/usr/bin/sh /root/squashfs-root/usr/bin/python /root/squashfs-root/usr/share/inkscape/extensions/dxf_input.py /root/{dxf_local_filename} --output=/root/{svg_local_filename} --scalemethod=auto"
        # app.logger.info("Command: " + str_command)

        command = [
            "/usr/bin/sh",
            "/root/squashfs-root/usr/bin/python",
            "/root/squashfs-root/usr/share/inkscape/extensions/dxf_input.py",
            "/root/" + dxf_local_filename,
            "--output=/root/" + svg_local_filename,
            "--scalemethod=auto",
        ]

        completed_process = subprocess.run(command)
        app.logger.info("completed_process:")
        app.logger.info(completed_process)

        # Put output svg file to S3
        client.upload_file(svg_local_filename, s3_bucket, s3_svg_path)

        # https://flask.palletsprojects.com/en/2.0.x/quickstart/#apis-with-json
        result = True
        message = "Success"

    except ValueError as e:
        result = False
        message = e.args[0]

    return {
        "success": result,
        "message": message
    }

if __name__ == "__main__":
    app.run(host='0.0.0.0')