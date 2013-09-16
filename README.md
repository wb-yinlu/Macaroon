Macaroon
========
Macaroon是一个高效的反向代理测试套件，测试框架本身基于python2.7开发，方便跨平台移植；测试例使用格式化描述，做到编程语言无关性。使用Macaroon能够简>便快捷的完成测试场景的构造、线上失效案例的重建及被测软件（DUT）的功能、模块、协议一致性测试等。

1. 目录结构

  macaroon/ .................. 根目录
  |-- case ................... 测试例目录
  |-- CHANGES ................ change logs
  |-- config.py .............. 全局配置项
  |-- data2case.py ........... 测试例转换为可执行文件
  |-- deploy.py .............. DUT操作module
  |-- doc/ ................... 文档
      |-- Case_Design ........ 测试例编写指南
      |-- Q&A ................ question&answer
  |-- example/ ............... 测试用例样例
      |-- case_example.yaml... 测试样例
      |-- case_reference.yaml. 空的测试例模板
  |-- install.sh ............. Macaroon一键安装
  |-- lib/ ................... Macaroon库文件
      |-- agentclient.py ..... agent for client
      |-- agentserver.py...... agent for server
      |-- httpmockclient.py .. client端mock库
      |-- httpmockserver.py .. server端mock库
      |-- contentfilter.py ... 生成log文件
      |-- parseyaml.py ....... 测试例解析
      |-- Python-2.7.tgz ..... python2.7代码包
      |-- setuptools.tar.gz... setuptools代码包
      |-- PyYAML-3.10.tar.gz.. pyYAML代码包
  |-- log/ ................... 测试例执行结果日志
  |-- mutil.py ............... 通用的测试用例相关方法集
  |-- README ................. Macaroon使用说明
  |-- runcase.sh ............. 执行单个测试例
  |-- runner.py .............. 按目录执行测试例
  |-- VERSION ................ Macaroon当前版本

2. 框架及case设计
   参见doc/Case_Design


3. 如何获取
  i. 从社区获取

4. 安装及使用

  社区公共测试平台地址：http://XXXX(环境已经搭建完成)
  自行安装及使用：
  i. 硬件准备：两台机器A和B，A机器执行测试并同时作为client端与server端，B机器安装被测软件DUT--例如TrafficServer(Proxy).
  ii.软件准备：
        执行install.sh文件
        Client&Server:
       Linux
       Python2.7
       PyYaml包
       Macaroon
       git

        DUT( Device Under Testing):
       被测软件(proxy or cache, 如TrafficServer, Swift等)
       Bind
  iii. 配置DUT：
        使从A机器client端发出的http请求能够通过DUT(proxy)后正确到达A机器server端 ----- *重要
        例如： 在proxy上安装bind, 修改named的相关配置信息,使得named中存在一个域名可以指向A机器(Client的IP)，配置完成后使用dig <域名> 确认是否成功.
  iv. 修改config文件：
        在macaroon目录下, 找到config.py文件,将_server的内容修改为proxy的ip或者hostname，
        _port修改为proxy提供的对外服务的端口, 例如：默认为80.
        将DUT_Strart, DUT_Stop和DUT_Clean分别修改为proxy对应的启动, 停止和清理缓存命令

  v.  将macaroon目录下的agentsever.py 拷贝至proxy机器,并使用sudo权限执行：sudo python agentserver.py
  vi. 环境验证：
        在client端执行httpmockserver.py：python httpmockserver.py
        在proxy端执行curl命令，验证proxy到client的request是否可达：curl http://<proxyip>:<port>/ -H "Host:XXX:[port]"
  更多问题参见：doc/Q&A


5. 如何运行用例
   i. 运行单个case
        在根目录下执行如下命令: sh runcase.sh <case文件>
   ii. 运行多个case
        在根目录下执行如下命令：python runner.py -p your-case-path -s your-email
        详见：python runner.py -h


6. 查看case输出及日志
   i. 执行和调试单个测试例
        sh runcase.sh <case文件>, case执行日志屏幕输出

   ii. 执行多个case
        执行日志输出至日志文件，./log/record_XXXX.log，按时间排序
        
7. 如何编写你的用例

   i.  case/下创建your case dir
   ii. 拷贝case模板example/case_template_example.yaml至your case dir，并重命名
   iii.编辑该文件
       a. 文件头部添加case相关说明
       b. 填写case步骤并准备对应步骤的数据块
       c. 填充和完善每步的数据,如request header, response header, response body, 需要检查的header等
       d. 保存和调试用例

8. 更多信息
   ./doc/文档
