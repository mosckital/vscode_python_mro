#!/usr/bin/env bash

export CODE_TESTS_PATH="$(pwd)/client/out/test"
export CODE_TESTS_WORKSPACE="$(pwd)/tests/examples"

node "$(pwd)/client/out/test/runTest"