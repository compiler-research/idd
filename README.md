# Introduction

IDD is a tool for performing interactive dynamic differential debugging capable to identify functional and performance regressions.

##  :beginner: About

IDD loads two versions of the same application. The first one is the base version that works as expected while the second version of the same program has a regression introduced. IDD inspects the two versions of the applications using external tools like gdb and lldb. The two applications are executed side by side and the user is allowed to dispatch commands to the underlying debuggers in order to expect their internal states and isolate the origin of the regression.

## :rocket: Demo
![idd](https://github.com/compiler-research/idd/assets/7579600/dac1b3c6-44f0-48b2-a19d-92eb5f1d973f)

## :zap: Usage
Write about how to use this project.

`python -m idd -c gdb -ba <path to base executable> -ra <path to regressed executable>`

### :electric_plug: Installation
- Steps on how to install this project on Ubuntu 22.04

-- Creating new environment:
```
$ python3 -m venv iddenv
$ source iddenv/bin/activate
```


-- Installing required packages:

```
$ pip install -e.
```

## :cherry_blossom: Community

Join our discord for discussions and collaboration.

<a target="_blank" href="https://discord.gg/Vkv3ne4zVK"><img src="images/discord.svg" /></a>


 ###  :fire: Contribution

 Your contributions are always welcome and appreciated. Following are the things you can do to contribute to this project.

 1. **Report a bug** <br>
 If you think you have encountered a bug, and I should know about it, feel free to report it [here](https://github.com/compiler-research/idd/issues) and we could take care of it.

 2. **Request a feature** <br>
 You can also request for a feature [here](https://github.com/compiler-research/idd/issues), and if it will viable, it will be picked for development.  

 3. **Create a pull request** <br>
 It can't get better then this, your pull request will be appreciated by the community. You can get started by picking up any open issues from [here]() and make a pull request.

## Cite
```bibtex
@article{vassilev2020idd,
  title={IDD--a platform enabling differential debugging},
  author={Vassilev, Martin and Vassilev, Vassil and Penev, Alexander},
  journal={Cybernetics and Information Technologies},
  volume={20},
  number={1},
  pages={53--67},
  year={2020}
}
```

## Issues
1. ~~Support entering commands to a specific analyzer.~~
2. ~~Make panels scrollable~~
3. Make panels configurable
