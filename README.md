# 使用方法

将clanjob_data&job_in_yobot文件放入/ybplugins/文件夹
随后修改yobot.py的加载即可完成安装使用

## 运行环境

必须是完整安装运行了[yobot源码版](https://github.com/yuudi/yobot)的yobot程序

## 额外管理员定义方式

可以通过修改job_in_yobot内的 self.extraAdmin = () 进行修改，值必须是Int且多个QQ号需要用','分割