# 大作业使用文档

## 开发环境

本程序在 Windows 10 下开发测试通过，Python 版本为 3.6，依赖包为：

- opencv-python 3.4
- numpy 1.16
- pyaudio 0.2
- PyQt 5.12.1

## 运行方法

在命令行键入：

```shell
python main.py
```

即可运行

## 代码结构

- classes/ 中是定义的底层类

1. camera.py 是调用摄像头读取图片和视频通话模块
2. chat.py 是三种聊天类的实现
3. message.py 是三种消息类的实现
4. microphone.py 是调用麦克风读取音频和语音通话模块
5. user.py 是用户类的实现

- src/ 中是程序中用到的图标
- UI/ 中是 PyQt 界面设计的 UI 文件
- central_server_connector.py 是与中央服务器连接的模块
- config.py 是程序各种超参数、资源路径的定义
- main.py 是主界面运行程序
- my_central_server.py 是我所实现的中央服务器
- sub_windows.py 是子界面定义（登录窗口等）
- utils.py 是一些功能函数的实现

## 使用方法

### 登录
  
<center><img src="https://github.com/Wuziyi616/Computer_Network_Project/blob/master/figures/login.png" alt="login" style="zoom:50%;" /></center>  
  
输入学号、密码（net2019）即可登录。同时在登录界面可以选择是否使用自制服务器。若勾选该项则需事先在本机上运行服务器，在命令行键入：

```shell
python my_central_server.py
```

看见 central server running 字样就表明服务器开始运行。

### 主界面
  
<center><img src="https://github.com/Wuziyi616/Computer_Network_Project/blob/master/figures/UI.png" alt="UI" style="zoom:100%;" /></center>  
  
主要功能标注如图，个人认为自己的 label 名称还是很明确的，几个需要特别指出的操作：

- 添加好友需输入学号再点击 '+'，删除好友只需在列表中选中然后点击 '-' 即可
- 点击好友列表或群聊列表中项即可切换聊天对象
- 发起群聊时会出现一个群友选择界面，点击好友再点 OK 即可
  
<center><img src="https://github.com/Wuziyi616/Computer_Network_Project/blob/master/figures/login.png" alt="groupchat" style="zoom:55%;" /></center>  
  
- 发送语音和语音输入需长按说话
- 发送文件和图片需在发送框中输入其在本机上的相对路径，同时勾选相应类型
- 若要结束视频通话，只需再点击一次视频聊天按钮即可
