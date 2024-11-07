#!/usr/bin/env python
# coding: utf-8

import glob
import os
from os import system
root_tests_dir = '.'

for test_dir in os.listdir(root_tests_dir):
    if os.path.isdir(os.path.join(root_tests_dir, test_dir)):
        print(test_dir)
        if not os.path.exists("{test_dir}/a".format(test_dir = test_dir)):
            os.makedirs("{test_dir}/a".format(test_dir = test_dir))

        if not os.path.exists("{test_dir}/b".format(test_dir = test_dir)):
            os.makedirs("{test_dir}/b".format(test_dir = test_dir))

        system("g++ -DV1 -o {test_d}/a/program.out -xc++ -g {test_files}".format(test_d = test_dir, test_files = ' '.join(glob.glob(test_dir + '/*.c??'))))
        system("g++ -DV2 -o {test_d}/b/program.out -xc++ -g {test_files}".format(test_d = test_dir, test_files = ' '.join(glob.glob(test_dir + '/*.c??'))))