#!/bin/bash

git fetch
git pull

# provide execute permission to quotacheck script
sudo chmod +x ./scripts/quota_check_params.sh