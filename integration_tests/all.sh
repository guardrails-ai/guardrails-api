#!/bin/bash

bash ./integration_tests/build.sh || exit 1;
bash ./integration_tests/run.sh || exit 1;
bash ./integration_tests/check.sh || exit 1;
bash ./integration_tests/test.sh || exit 1;
bash ./integration_tests/clean.sh || exit 1;
