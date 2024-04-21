IDD is a tool for performing interactive dynamic differential debugging capable to identify functional and performance regressions.

## About IDD

IDD loads two versions of the same application. The first one is the base version that works as expected while the second version of the same program has a regression introduced. IDD inspects the two versions of the applications using external tools like gdb and lldb. The two applications are executed side by side and the user is allowed to dispatch commands to the underlying debuggers in order to expect their internal states and isolate the origin of the regression.

## Demo
![idd](https://github.com/compiler-research/idd/assets/7579600/dac1b3c6-44f0-48b2-a19d-92eb5f1d973f)

## Installation

TODO

## How to use IDD

TODO

## Issues

1. Make panels scrollable
2. Make panels configurable
3. Support entering commands to a specific analyzer.
