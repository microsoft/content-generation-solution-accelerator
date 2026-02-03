#!/bin/bash

export NODE_OPTIONS=--max_old_space_size=8192

# Restoring backend python packages
echo ""
echo "Restoring backend python packages"
echo ""
python3 -m pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Failed to restore backend python packages"
    exit $?
fi

echo ""
echo "Restoring frontend npm packages"
echo ""
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "Failed to restore frontend npm packages"
    exit $?
fi

echo ""
echo "Building frontend"
echo ""
npm run build
if [ $? -ne 0 ]; then
    echo "Failed to build frontend"
    exit $?
fi

cd ..
echo ""
echo "Starting backend"
echo ""
python3 -m quart run --port=50505 --host=127.0.0.1 --reload
if [ $? -ne 0 ]; then
    echo "Failed to start backend"
    exit $?
fi