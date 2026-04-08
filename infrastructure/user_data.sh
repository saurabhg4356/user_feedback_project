#!/bin/bash
set -e
sudo dnf update -y
sudo dnf install -y python3 python3-pip git
sudo mkdir -p /opt/feedback-api
sudo chown -R ec2-user:ec2-user /opt/feedback-api
pip3 install --upgrade pip
pip3 install Flask Flask-RESTful boto3 gunicorn