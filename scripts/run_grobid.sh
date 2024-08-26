#!/usr/bin/env bash

cd $HOME/grobid-0.7.3

./gradlew clean assemble 

## Start Grobid
./gradlew run
