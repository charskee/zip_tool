import os
import time
import zipfile
import sys
import re
import datetime as dt
import shutil
import threading
import concurrent.futures
import plistlib
from plistlib import load, dump
from PySide2.QtWidgets import QApplication
from PySide2.QtUiTools import QUiLoader
from PySide2.QtGui import QIcon
from PySide2.QtCore import Signal, QObject

# 当前工作路径
BASE_DIR = os.path.dirname(os.path.relpath(sys.argv[0]))
vpn_path = 'com.ss.iphone.ugc.Aweme/Documents/vpn.plist'
uid_path = 'com.ss.iphone.ugc.Aweme/Library/Preferences/com.ss.iphone.ugc.Aweme.plist'
apm_path = 'com.ss.iphone.ugc.Aweme/Library/Preferences/apm.heimdallr.userdefaults.plist'
IR_path = 'IR.plist'
Plist_path = os.path.join(BASE_DIR, './res/vpn.plist')
Thread_NUM = 0
Change_NUM = 0
Work_NUM = 0
Change_Work_Num = 0
repect_time = 1


class Mysignal(QObject):
    signal = Signal(str)


class RenameOS:
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        # 从文件中加载ui定义
        print(os.path.join(BASE_DIR, '/res/rename.ui'))
        self.ui = QUiLoader().load(os.path.join(BASE_DIR, './res/rename.ui'))
        # 初始化控件内容
        self.rename_btn = self.ui.renameBT  # UID命名
        self.chaxun_btn = self.ui.chaxunBT  # 省份+UID命名
        self.chaxunmd_btn = self.ui.chaxunMD # 查询机型
        self.chaxunzc_btn = self.ui.chaxunZC # 查询注册时间
        self.chaxunos_btn = self.ui.chaxunOS # 查询系统

        self.choose_pro = self.ui.choseprovince #省份选择框
        self.addcity_input = self.ui.changecity #添加城市输入框
        self.addpro_btn = self.ui.addprovince #添加省份按钮

        self.choose_os = self.ui.oscomboBox #系统选择框
        self.addos_btn = self.ui.ospushButton #添加系统按钮

        self.regx_btn = self.ui.regexNameBT
        # 日志
        self.log = self.ui.text_log

        # 省份
        self.hunan = self.ui.hunan
        self.hubei = self.ui.hubei
        self.gd = self.ui.gd
        self.gx = self.ui.gx
        self.henan = self.ui.henan
        self.hebei = self.ui.hebei
        self.jx = self.ui.jx
        self.cq = self.ui.cq
        self.js = self.ui.js
        self.zj = self.ui.zj
        self.ah = self.ui.ah
        self.gs = self.ui.gs
        self.sc = self.ui.sc
        self.jls = self.ui.jls
        self.sd = self.ui.sd
        self.sx_2 = self.ui.sx_2
        self.ln = self.ui.ln
        self.sh = self.ui.sh
        self.bj = self.ui.bj
        self.fj = self.ui.fj
        self.qh = self.ui.qh
        self.sx = self.ui.sx
        self.gz = self.ui.gz
        self.hn = self.ui.hn
        self.nmg = self.ui.nmg
        self.nx = self.ui.nx
        self.xj = self.ui.xj
        self.yn = self.ui.yn
        # 信号绑定
        self.rename_btn.clicked.connect(self.rename) # UID命名
        self.chaxun_btn.clicked.connect(self.chaxun) # 省份+UID命名
        self.chaxunmd_btn.clicked.connect(self.chaxunmd) # 查询机型
        self.addpro_btn.clicked.connect(self.add) #添加省份
        self.regx_btn.clicked.connect(self.regexzip) # 去除省份命名
        self.chaxunzc_btn.clicked.connect(self.chaxunzc) #查询注册时间
        self.chaxunos_btn.clicked.connect(self.chaxunos) #查询系统版本
        self.addos_btn.clicked.connect(self.addos) #添加系统

        # 信号绑定
        self.my_signal = Mysignal()
        self.my_signal.signal.connect(self.update)

    def regexzip(self):
        self.log.append(f'[{self.now_time()}]: ' + '去除省份命名')
        self.setButton(False)
        # 文件列表
        filepath = os.path.join(BASE_DIR, './ir')
        fileList = os.listdir(filepath)
        self.log.append(f'[{self.now_time()}]: ' + f'本次工作 {len(fileList)} 个文件')
        # 遍历文件
        for i in range(0, len(fileList)):
            filename = fileList[i]
            newpath = filepath + '/' + filename
            # 跳过非zip文件
            if zipfile.is_zipfile(newpath) == False:
                continue
            print(filename)
            new_name = self.regexName(filename)
            new_name = filepath + '/' + new_name
            try:
                os.rename(newpath, new_name)
            except Exception as e:
                self.log.append(f'[{self.now_time()}]: ' + str(e))

        self.log.append(f'[{self.now_time()}]: ' + '去除省份命名完毕')
        self.setButton(True)

    def addos(self):
        # 1.获取需要更改的系统版本
        # 2.获取需要更改的文件列表
        # 3.列表循环 解压一个文件到当前目录
        # 4.修改ir.plist的内容
        # 6.压缩文件夹全部内容到当前目录 重命名
        # 7.删除原文件
        self.log.append(f'[{self.now_time()}]: ' + '写入自定义系统开始')
        self.setButton(False)
        choose_os_version = self.choose_os.currentText()
        print(choose_os_version)
        self.log.append(f'[{self.now_time()}]: ' + f'本次修改的系统版本为{choose_os_version}')
        # os_message = self.setOSmessage(choose_os_version)
        # print(os_message)
        # 3.获取需要更改的文件列表
        filelist = self.work_file()
        self.log.append(f'[{self.now_time()}]: ' + f'本次需要修改的备份包数量为 {len(filelist)}')
        if len(filelist) == 0:
            self.setButton(True)
            self.log.append(f'[{self.now_time()}]: ' + '写入自定义系统完毕')
            return
        # 设置最大线程数
        max_workers = 10  # 限制为 10 个线程
        # 使用多线程处理每个 .zip 文件
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            process_zip_with_os = lambda zip_file: self.process_zip(zip_file, choose_os_version)
            executor.map(process_zip_with_os, filelist)
        self.log.append(f'[{self.now_time()}]: ' + '写入自定义系统完毕')
        self.setButton(True)

    def chaxunos(self):
        self.log.append(f'[{self.now_time()}]: ' + '查询系统开始')
        self.setButton(False)
        # 文件列表
        filepath = os.path.join(BASE_DIR, './ir')
        fileList = os.listdir(filepath)
        self.log.append(f'[{self.now_time()}]: ' + f'本次查询 {len(fileList)} 个文件')
        # 遍历文件
        for i in range(0,len(fileList)):
            is_hasir = False
            os_version = ""
            filename = fileList[i]
            newpath = filepath + '/' + filename
            # 跳过非zip文件
            if zipfile.is_zipfile(newpath) == False:
                continue
            # 读取zip文件
            with zipfile.ZipFile(newpath, 'r') as myzip:
                # zip文件的路径列表
                all_filelist = myzip.namelist()
                # 判断是否存在IR文件
                for i in range(0, len(all_filelist)):
                    filelist_name = all_filelist[i]
                    if filelist_name == IR_path:
                        is_hasir = True
                        break
                if is_hasir == True:
                    with myzip.open(IR_path, 'r') as ir:
                        try:
                            pl = load(ir)
                            RandomOSversion = pl['RandomOSversion']
                            print(RandomOSversion)
                            if RandomOSversion :
                                print("存在自定义系统")
                                os_version = pl["osversionItem"]["osversion"]
                                print(os_version)
                        except:
                            print("IR.plist存在非法字符")
                myzip.close()
            if os_version == "":
                os_version = "未自定义系统或包无法读取"
            newname = filepath + '/' + os_version + '-' + filename
            os.rename(newpath, newname)
        self.log.append(f'[{self.now_time()}]: ' + '查询系统完毕')
        self.setButton(True)


    def chaxunzc(self):
        # 查询注册时间
        self.log.append(f'[{self.now_time()}]: ' + '查询开始')
        self.setButton(False)
        # 文件列表
        filepath = os.path.join(BASE_DIR, './ir')
        fileList = os.listdir(filepath)
        self.log.append(f'[{self.now_time()}]: ' + f'本次查询 {len(fileList)} 个文件')
        # 遍历文件
        for i in range(0, len(fileList)):
            createtime = ""
            filename = fileList[i]
            newpath = filepath + '/' + filename
            # 跳过非zip文件
            if zipfile.is_zipfile(newpath) == False:
                continue
            # 读取zip文件
            with zipfile.ZipFile(newpath, 'r') as myzip:
                # zip文件的路径列表
                all_filelist = myzip.namelist()

                # 判断是否存在Vpn.plist文件
                for i in range(0, len(all_filelist)):
                    filelist_name = all_filelist[i]
                    if filelist_name == vpn_path:
                        zipInfo  = myzip.getinfo(vpn_path)
                        createtime = str(zipInfo.date_time[0]) + "-" + str(zipInfo.date_time[1]) + "-" + str(zipInfo.date_time[2])
                        print(createtime)
                        break
                myzip.close()
            if createtime == "":
                createtime = "未知注册时间"
            newname = filepath + '/' + createtime + '-' + filename
            os.rename(newpath, newname)
        self.log.append(f'[{self.now_time()}]: ' + '查询完毕')
        self.setButton(True)

    def chaxunmd(self):
        self.log.append(f'[{self.now_time()}]: ' + '查询机型开始')
        self.setButton(False)
        # 文件列表
        filepath = os.path.join(BASE_DIR, './ir')
        fileList = os.listdir(filepath)
        self.log.append(f'[{self.now_time()}]: ' + f'本次查询 {len(fileList)} 个文件')
        # 遍历文件
        for i in range(0,len(fileList)):
            is_hasir = False
            model = ""
            filename = fileList[i]
            newpath = filepath + '/' + filename
            # 跳过非zip文件
            if zipfile.is_zipfile(newpath) == False:
                continue
            # 读取zip文件
            with zipfile.ZipFile(newpath, 'r') as myzip:
                # zip文件的路径列表
                all_filelist = myzip.namelist()
                # 判断是否存在IR文件
                for i in range(0, len(all_filelist)):
                    filelist_name = all_filelist[i]
                    if filelist_name == IR_path:
                        is_hasir = True
                        break
                if is_hasir == True:
                    with myzip.open(IR_path, 'r') as ir:
                        try:
                            pl = load(ir)
                            model = pl['Model']
                        except:
                            print("IR.plist存在非法字符")
                myzip.close()
            if model == "":
                model = "未知机型"
            newname = filepath + '/' + model + '-' + filename
            os.rename(newpath, newname)
        self.log.append(f'[{self.now_time()}]: ' + '查询机型完毕')
        self.setButton(True)

    def chaxun(self):
        print("查询省份")
        self.log.append(f'[{self.now_time()}]: ' + '查询省份')
        self.setButton(False)
        # 文件列表
        filepath = os.path.join(BASE_DIR, './ir')
        fileList = os.listdir(filepath)
        self.log.append(f'[{self.now_time()}]: ' + f'本次查询 {len(fileList)} 个文件')
        province_dict = {}
        for i in range(0,len(fileList)):
            is_hasvpn = False
            province = ''
            city = ''
            filename = fileList[i]
            newpath = filepath+'/'+filename
            # 跳过非zip文件
            if zipfile.is_zipfile(newpath) == False:
                continue
            # 读取zip文件
            with zipfile.ZipFile(newpath,'r')as myzip:
                # zip文件的路径列表
                all_filelist = myzip.namelist()
                # 判断是否存在vpn列表
                for i in range(0, len(all_filelist)):
                    filelist_name = all_filelist[i]
                    if filelist_name == vpn_path:
                        is_hasvpn = True
                    if is_hasvpn:
                        break
                # 读取省份
                if is_hasvpn:
                    # vpn = myzip.open(vpn_path, 'r')
                    with myzip.open(vpn_path,'r')as vpn:
                        pl = load(vpn)
                        province = pl['province']
                        city = pl['phone']
                        if province in province_dict:
                            # 有
                            province_dict[province] += 1
                        else:
                            # 没有
                            province_dict[province] = 1
                # 关闭文件对象
                myzip.close()
                # 1.更新内容
                self.update_info(province_dict)
            # 2.重命名
            if province == '':
                province = '省份未知'
            if city == '18888888888':
                newname = filepath + '/' + province + '-自定义-' + filename
            else:
                newname = filepath + '/' + province + '-' + filename
            self.myrename(newpath,newname)
        self.log.append(f'[{self.now_time()}]: ' + '查询完毕')
        self.setButton(True)

    def myrename(self,path_name,new_name):
        global repect_time
        try:
            os.rename(path_name,new_name)
        except Exception as e:
            if e.args[0] == 17:  # 重命名
                repect_str = str(repect_time)
                fname, fename = os.path.splitext(new_name)  # 分割一下符号以及别的 然后重命名
                self.myrename(path_name, fname + "-重复-" + repect_str + fename)  # 递归玩法
                repect_time = repect_time + 1
                print(f"{new_name}出现重复")

    def regexUID(self,str):
        print(str)
        print("REGX")
        regex = r"'uid':\s'(\d\d+)'"
        find_str = ''
        matches = re.finditer(regex, str, re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1
                # print(match.group(groupNum))
                find_str = match.group(groupNum)
        return find_str

    def regexName(self,str):
        regex = r"(\d+.zip)"
        find_str = ''
        matches = re.finditer(regex, str, re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1
                # print(match.group(groupNum))
                find_str = match.group(groupNum)
        return find_str

    def regexVersionKey(self,str):
        regex = r"kTIMConvLastMsgBatchUpdateProcesserVersionKey_(\d+)"
        find_str = ''
        matches = re.finditer(regex, str, re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1
                # print(match.group(groupNum))
                find_str = match.group(groupNum)
        return find_str

    def rename(self):
        print("uid命名")
        self.setButton(False)
        self.log.append(f'[{self.now_time()}]: ' + 'uid命名')
        # 文件列表
        filepath = os.path.join(BASE_DIR, './ir')
        fileList = os.listdir(filepath)
        self.log.append(f'[{self.now_time()}]: ' + f'本次操作 {len(fileList)} 个文件')
        for i in range(0, len(fileList)):
            is_hasUID = False
            is_hasApm = False
            UID = ''
            filename = fileList[i]
            newpath = filepath+'/'+filename
            # 跳过非zip文件
            if zipfile.is_zipfile(newpath) == False:
                continue
            # 读取zip文件
            with zipfile.ZipFile(newpath,'r')as myzip:
                # zip文件的路径列表
                all_filelist = myzip.namelist()
                # 判断是否存在vpn列表
                for i in range(0, len(all_filelist)):
                    filelist_name = all_filelist[i]
                    if filelist_name == uid_path:
                        is_hasUID = True
                    if filelist_name == apm_path:
                        is_hasApm = True
                    if is_hasUID and is_hasApm:
                        break
                # 读取uid

                if is_hasUID:
                    print("存在UID文件")
                    with myzip.open(uid_path,'r')as keypath:
                        pl = load(keypath)
                        keybool = 'ABTestCurrentUserKey' in pl.keys()
                        if keybool:
                            UID = pl['ABTestCurrentUserKey']
                            print("已从ABTestCurrentUserKey获取到uid")
                            print(UID)
                        else:
                            for key in pl.keys():
                                tmp_uid = self.regexVersionKey(key)
                                print(tmp_uid)
                                if tmp_uid:
                                    UID = tmp_uid
                                    print("已从VerisonKey获取到uid")
                                    break
                if is_hasApm and UID == '':
                    print("存在APM文件")
                    with myzip.open(apm_path,'r')as apm:
                        pl = load(apm)
                        str_pl = str(pl)
                        print(str_pl)
                        UID = self.regexUID(str_pl)
                        if UID:
                            print("已从apm获取到uid")
                            print(UID)
                # 关闭文件对象
                myzip.close()
            if UID == '':
                UID = 'UID未知'
            newname = filepath + '/' + UID + '.zip'
            self.myrename(newpath, newname)
        self.log.append(f'[{self.now_time()}]: ' + 'uid命名完毕')
        self.setButton(True)

    def update_info(self, dict):
        keys = dict.keys()
        for key in keys:
            if key == '湖南':
                self.hunan.setText(str(dict[key]))
            elif key == '湖北':
                self.hubei.setText(str(dict[key]))
            elif key == '广东':
                self.gd.setText(str(dict[key]))
            elif key == '广西':
                self.gx.setText(str(dict[key]))
            elif key == '河南':
                self.henan.setText(str(dict[key]))
            elif key == '河北':
                self.hebei.setText(str(dict[key]))
            elif key == '江西':
                self.jx.setText(str(dict[key]))
            elif key == '重庆':
                self.cq.setText(str(dict[key]))
            elif key == '江苏':
                self.js.setText(str(dict[key]))
            elif key == '浙江':
                self.zj.setText(str(dict[key]))
            elif key == '安徽':
                self.ah.setText(str(dict[key]))
            elif key == '甘肃':
                self.gs.setText(str(dict[key]))
            elif key == '四川':
                self.sc.setText(str(dict[key]))
            elif key == '吉林省':
                self.jls.setText(str(dict[key]))
            elif key == '山东':
                self.sd.setText(str(dict[key]))
            elif key == '山西':
                self.sx_2.setText(str(dict[key]))
            elif key == '辽宁':
                self.ln.setText(str(dict[key]))
            elif key == '上海':
                self.sh.setText(str(dict[key]))
            elif key == '北京':
                self.bj.setText(str(dict[key]))
            elif key == '福建':
                self.fj.setText(str(dict[key]))
            elif key == '青海':
                self.qh.setText(str(dict[key]))
            elif key == '陕西':
                self.sx.setText(str(dict[key]))
            elif key == '贵州':
                self.gz.setText(str(dict[key]))
            elif key == '海南':
                self.hn.setText(str(dict[key]))
            elif key == '内蒙古':
                self.nmg.setText(str(dict[key]))
            elif key == '宁夏':
                self.nx.setText(str(dict[key]))
            elif key == '新疆':
                self.xj.setText(str(dict[key]))
            elif key == '云南':
                self.yn.setText(str(dict[key]))

    def do_zip_compress(self, dirpath):
        # print("原始文件夹路径：" + dirpath)
        output_name = f"{dirpath}.zip"
        parent_name = os.path.dirname(dirpath)
        # print("压缩文件夹目录：", parent_name)
        zip = zipfile.ZipFile(output_name, "w", zipfile.ZIP_DEFLATED)
        # 多层级压缩

        for root, dirs, files in os.walk(dirpath):
            for file in files:
                if str(file).startswith("~$"):
                    continue
                filepath = os.path.join(root, file)
                abs_path = os.path.abspath(filepath)
                new_abs_path = '\\\\?\\' + abs_path
                # print("压缩文件路径：" + filepath)
                writepath = os.path.relpath(filepath, dirpath)
                # print(filepath)
                # print(writepath)
                zip.write(new_abs_path, writepath,compress_type=zipfile.ZIP_DEFLATED)
        zip.close()

    def un_zip(self, file_name):
        """unzip zip file"""
        zip_file = zipfile.ZipFile(file_name)
        if os.path.isdir(file_name + "_files"):
            pass
        else:
            os.mkdir(file_name + "_files")
        abs_path = os.path.abspath('./'+file_name + '_files')
        new_abs_path = '\\\\?\\' + abs_path
        for names in zip_file.namelist():
            zip_file.extract(names, new_abs_path)
        zip_file.close()

    def edit_plist(self, province, city):
        plist_msg = {}
        with open(Plist_path,'rb')as p:
            plist_msg = load(p)
            print(plist_msg)
        plist_msg['province'] = province
        plist_msg['city'] = city
        print(plist_msg)
        with open(Plist_path,'wb')as p:
            dump(plist_msg,p)

    def work_file(self):
        filepath = os.path.join(BASE_DIR, './ir')
        fileList = os.listdir(filepath)
        print(len(fileList))
        new_filelist = []
        for i in range(0, len(fileList)):
            filename = fileList[i]
            newpath = filepath + '/' + filename
            # 跳过非zip文件
            if zipfile.is_zipfile(newpath) == False:
                print(newpath)
                continue
            new_filelist.append(filename)
        return new_filelist

    def mycopyfile(self, srcfile, dstpath):  # 复制文件函数
        if not os.path.isfile(srcfile):
            print("%s not exist!" % (srcfile))
        else:
            fpath, fname = os.path.split(srcfile)  # 分离文件名和路径
            if not os.path.exists(dstpath):
                os.makedirs(dstpath)  # 创建路径
            shutil.copy(srcfile, dstpath + fname)  # 复制文件
            print("copy %s -> %s" % (srcfile, dstpath + fname))

    def add(self):
        global Thread_NUM
        # 1.获取需要更改的省份
        # 2.读取res中的plist文件 更改省份的值为获取到的省份
        # 3.获取需要更改的文件列表
        # 4.列表循环 解压一个文件到当前目录
        # 5.复制res中的plist文件到指定目录
        # 6.压缩文件夹全部内容到当前目录 并且命名为 省份-自定义省份-uid
        # 7.删除原文件
        # 1.获取需要更改的省份
        self.log.append(f'[{self.now_time()}]: ' + '写入自定义省份文件开始')
        self.setButton(False)
        province = self.choose_pro.currentText()
        city = self.addcity_input.text()
        if city:
            # 2.读取res中的plist文件 更改省份的值为获取到的省份
            self.edit_plist(province,city)
            # 3.获取需要更改的文件列表
            filelist = self.work_file()
            self.log.append(f'[{self.now_time()}]: ' + f'本次需要注入的备份包数量为 {len(filelist)}')
            print(len(filelist))
            if len(filelist) == 0 :
                self.setButton(True)
                self.log.append(f'[{self.now_time()}]: ' + '写入自定义省份文件完毕')
                return
            Thread_NUM = len(filelist)
            # 4.列表循环 解压一个文件到当前目录
            filepath = os.path.join(BASE_DIR, './ir')
            for file in filelist:
                # 创建线程请求
                argms_plist = [filepath, province, file]
                t = threading.Thread(target=self.add_plist, args=(argms_plist,))
                t.start()
        else:
            self.my_signal.signal.emit('请先填写城市')
            self.setButton(True)


    def add_plist(self, argms_plist):
        global Work_NUM
        filepath = argms_plist[0]
        province = argms_plist[1]
        file = argms_plist[2]
        # self.log.append(f'[{self.now_time()}]: ' + f'正在解压 {file}')
        self.my_signal.signal.emit(f'正在解压 {file}')
        newpath = filepath + '/' + file
        self.un_zip(newpath)
        # self.log.append(f'[{self.now_time()}]: ' + f'解压成功 {file}')
        # self.log.append(f'[{self.now_time()}]: ' + '写入vpn.plist')
        self.my_signal.signal.emit(f'解压成功 {file}')
        self.my_signal.signal.emit('写入vpn.plist')
        # 5.复制res中的plist文件到指定目录
        unzip_dir = filepath + '/' + file + '_files/' + vpn_path.strip('vpn.plist')
        # print(unzip_dir)
        self.mycopyfile(Plist_path, unzip_dir)
        # self.log.append(f'[{self.now_time()}]: ' + f' {file} 写入vpn.plist成功')
        self.my_signal.signal.emit(f'{file} 写入vpn.plist成功 开始压缩文件')
        # 6.删除原文件 压缩文件夹全部内容到当前目录 并且命名为 省份-自定义省份-uid
        os.remove(newpath)
        zip_dir = filepath + '/' + file + '_files'
        new_zip_dir = filepath + '/' + province + '-自定义-' + file.strip('.zip')

        try:
            os.rename(zip_dir, new_zip_dir)
        except Exception as e:
            print(e)
        self.do_zip_compress(new_zip_dir)
        # self.log.append(f'[{self.now_time()}]: ' + f'压缩完成 {province}-自定义-{file}')
        self.my_signal.signal.emit(f'压缩完成 {province}-自定义-{file}')
        print("删除文件夹")
        # delete_path = new_zip_dir + '/'
        abs_path = os.path.abspath('./'+ new_zip_dir + '/')
        new_abs_path = '\\\\?\\' + abs_path
        print(new_abs_path)
        shutil.rmtree(new_abs_path)
        Work_NUM += 1
        if Work_NUM == Thread_NUM:
            self.my_signal.signal.emit('写入自定义省份文件完毕')
            self.setButton(True)
        else:
            print(f'Work_NUM::{Work_NUM},Thread_NUM::{Thread_NUM}')

    def change_plist(self, argms_plist):
        global Change_Work_Num
        filepath = argms_plist[0]
        province = argms_plist[1]
        file = argms_plist[2]
        # self.log.append(f'[{self.now_time()}]: ' + f'正在解压 {file}')
        self.my_signal.signal.emit(f'正在解压 {file}')
        newpath = filepath + '/' + file
        self.un_zip(newpath)
        # self.log.append(f'[{self.now_time()}]: ' + f'解压成功 {file}')
        # self.log.append(f'[{self.now_time()}]: ' + '写入vpn.plist')
        self.my_signal.signal.emit(f'解压成功 {file}')
        self.my_signal.signal.emit('写入vpn.plist')
        # 5.复制res中的plist文件到指定目录
        unzip_dir = filepath + '/' + file + '_files/' + vpn_path.strip('vpn.plist')
        v_path = filepath + '/' + file + '_files/' + vpn_path
        # print(unzip_dir)
        os.remove(v_path)
        self.mycopyfile(Plist_path, unzip_dir)
        # self.log.append(f'[{self.now_time()}]: ' + f' {file} 写入vpn.plist成功')
        self.my_signal.signal.emit(f'{file} 写入vpn.plist成功 开始压缩文件')
        # 6.删除原文件 压缩文件夹全部内容到当前目录 并且命名为 省份-自定义省份-uid
        os.remove(newpath)
        zip_dir = filepath + '/' + file + '_files'
        new_zip_dir = filepath + '/' + province + '-自定义-' + file.strip('.zip')
        os.rename(zip_dir, new_zip_dir)
        self.do_zip_compress(new_zip_dir)
        # self.log.append(f'[{self.now_time()}]: ' + f'压缩完成 {province}-自定义-{file}')
        self.my_signal.signal.emit(f'压缩完成 {province}-自定义-{file}')
        print("删除文件夹")
        # delete_path = new_zip_dir + '/'
        abs_path = os.path.abspath('./'+ new_zip_dir + '/')
        new_abs_path = '\\\\?\\' + abs_path
        print(new_abs_path)
        shutil.rmtree(new_abs_path)
        Change_Work_Num += 1
        if Change_Work_Num == Change_NUM:
            self.my_signal.signal.emit('修改省份完毕')
            self.setButton(True)
        else:
            print(f'Work_NUM::{Change_Work_Num},Thread_NUM::{Change_NUM}')

    def now_time(self):
        return dt.datetime.now().strftime('%T')

    def setButton(self, type):
        self.rename_btn.setEnabled(type)
        self.chaxun_btn.setEnabled(type) # 一键查询
        self.addpro_btn.setEnabled(type)  # 添加省份按钮
        # self.changepro_btn.setEnabled(type)

    def update(self, message):
        self.log.append(f'[{self.now_time()}]: ' + message)

    def modify_plist(self, plist_file , osversion):
        print("开始修改plist")
        print("文件路径"+plist_file)
        with open(plist_file, 'rb') as f:
            plist_data = plistlib.load(f)
            print(plist_data["osversionItem"])
            print(osversion)
            # 修改 RandomOSversion 键为 true
            plist_data['RandomOSversion'] = True
            # 新增 osversionItem 键值对
            if osversion == '15.0':
                plist_data['osversionItem']['osversion'] = '15.0'
                plist_data['osversionItem']['osversionBuild'] = '19A346'
                plist_data['osversionItem']['osversionNumber'] = '1854'
                plist_data['osversionItem']['buildTime'] = '2021-09-16 13:39:21.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 21.0.0: Sun Aug 15 20:55:58 PDT 2021; root:xnu-8019.12.5~1/RELEASE_ARM64_T8101'
                plist_data['osversionItem']['kernosrelease'] = '21.0.0'
                plist_data['osversionItem']['dylduuid'] = 'D7A0282E-93DE-3A1E-9813-27E84517CC96'
                plist_data['osversionItem']['SystemImageID'] = 'B3FE2383-83F6-4D08-8928-EAE442B4F99C'
                plist_data['osversionItem']['BuildID'] = '0FD736D6-16A8-11EC-83AB-237CA1EF5A19'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2021 Apple Inc.'
            elif osversion == '15.0.2':
                plist_data['osversionItem']['osversion'] = '15.0.2'
                plist_data['osversionItem']['osversionBuild'] = '19A404'
                plist_data['osversionItem']['osversionNumber'] = '1854'
                plist_data['osversionItem']['buildTime'] = '2021-10-07 11:06:09.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 21.0.0: Wed Sep 29 08:30:00 PDT 2021; root:xnu-8019.12.5~35/RELEASE_ARM64_T8110'
                plist_data['osversionItem']['kernosrelease'] = '21.0.0'
                plist_data['osversionItem']['dylduuid'] = 'D7A0282E-93DE-3A1E-9813-27E84517CC96'
                plist_data['osversionItem']['SystemImageID'] = 'C8A92C32-8E44-4782-8405-7616560A5B95'
                plist_data['osversionItem']['BuildID'] = '239D3DCA-2713-11EC-9C98-70E2489C1635'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2021 Apple Inc.'
            elif osversion == '15.0.1':
                plist_data['osversionItem']['osversion'] = '15.0.1'
                plist_data['osversionItem']['osversionBuild'] = '19A348'
                plist_data['osversionItem']['osversionNumber'] = '1854'
                plist_data['osversionItem']['buildTime'] = '2021-09-28 19:09:53.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 21.0.0: Sun Aug 15 20:55:58 PDT 2021; root:xnu-8019.12.5~1/RELEASE_ARM64_T8101'
                plist_data['osversionItem']['kernosrelease'] = '21.0.0'
                plist_data['osversionItem']['dylduuid'] = 'D7A0282E-93DE-3A1E-9813-27E84517CC96'
                plist_data['osversionItem']['SystemImageID'] = '281FBDC2-0BC2-41DD-8944-E4412ED6BF7F'
                plist_data['osversionItem']['BuildID'] = '397AEFF0-2044-11EC-9384-D08C742505B7'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2021 Apple Inc.'
            elif osversion == '15.1':
                plist_data['osversionItem']['osversion'] = '15.1'
                plist_data['osversionItem']['osversionBuild'] = '19B74'
                plist_data['osversionItem']['osversionNumber'] = '1855.105000'
                plist_data['osversionItem']['buildTime'] = '2021-10-15 13:57:35.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 21.1.0: Wed Oct 13 18:16:52 PDT 2021; root:xnu-8019.42.4~1/RELEASE_ARM64_T8110'
                plist_data['osversionItem']['kernosrelease'] = '21.1.0'
                plist_data['osversionItem']['dylduuid'] = '5E7EF577-1CC5-369A-A04D-28FBBA883086'
                plist_data['osversionItem']['SystemImageID'] = '524A74D5-5EAB-461B-A15B-BC4E36E9A9E2'
                plist_data['osversionItem']['BuildID'] = '69887A86-2D74-11EC-A173-B4EB040748D7'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2021 Apple Inc.'
            elif osversion == '15.2':
                plist_data['osversionItem']['osversion'] = '15.2'
                plist_data['osversionItem']['osversionBuild'] = '19C56'
                plist_data['osversionItem']['osversionNumber'] = '1856.105000'
                plist_data['osversionItem']['buildTime'] = '2021-12-03 14:27:10.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 21.2.0: Sun Nov 28 20:43:39 PST 2021; root:xnu-8019.62.2~1/RELEASE_ARM64_T8110'
                plist_data['osversionItem']['kernosrelease'] = '21.2.0'
                plist_data['osversionItem']['dylduuid'] = '0B12AEC1-CAEF-38AD-8FB7-3CAB3DA30489'
                plist_data['osversionItem']['SystemImageID'] = '7F19B9A2-ED0F-400E-96EF-02150A2FA3DB'
                plist_data['osversionItem']['BuildID'] = 'AA08C5F6-53F9-11EC-AEA1-89BC549413F1'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2021 Apple Inc.'
                print(plist_data)
            elif osversion == '15.2.1':
                plist_data['osversionItem']['osversion'] = '15.2.1'
                plist_data['osversionItem']['osversionBuild'] = '19C63'
                plist_data['osversionItem']['osversionNumber'] = '1856.105000'
                plist_data['osversionItem']['buildTime'] = '2022-01-08 12:48:54.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 21.2.0: Sun Nov 28 20:43:39 PST 2021; root:xnu-8019.62.2~1/RELEASE_ARM64_T8110'
                plist_data['osversionItem']['kernosrelease'] = '21.2.0'
                plist_data['osversionItem']['dylduuid'] = '0B12AEC1-CAEF-38AD-8FB7-3CAB3DA30489'
                plist_data['osversionItem']['SystemImageID'] = '49A0E2EA-4213-4DAA-9C95-6CA1E95AF427'
                plist_data['osversionItem']['BuildID'] = 'E63E5132-7035-11EC-93A1-9C3957DBE9D0'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2022 Apple Inc.'
            elif osversion == '15.3':
                plist_data['osversionItem']['osversion'] = '15.3'
                plist_data['osversionItem']['osversionBuild'] = '19D50'
                plist_data['osversionItem']['osversionNumber'] = '1856.105000'
                plist_data['osversionItem']['buildTime'] = '2022-01-22 17:06:41.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 21.3.0: Wed Jan 5 21:44:44 PST 2022; root:xnu-8019.80.24~23/RELEASE_ARM64_T8110'
                plist_data['osversionItem']['kernosrelease'] = '21.3.0'
                plist_data['osversionItem']['dylduuid'] = '2F28A224-0775-36D0-B118-8EACCC225191'
                plist_data['osversionItem']['SystemImageID'] = '21E0744E-76D1-49E8-8C58-BC8A828CDEAB'
                plist_data['osversionItem']['BuildID'] = '3B3B4198-7B5A-11EC-956E-40A3ACE7B264'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2022 Apple Inc.'
            elif osversion == '15.3.1':
                plist_data['osversionItem']['osversion'] = '15.3.1'
                plist_data['osversionItem']['osversionBuild'] = '19D52'
                plist_data['osversionItem']['osversionNumber'] = '1856.105000'
                plist_data['osversionItem']['buildTime'] = '2022-02-04 11:50:31.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 21.3.0: Wed Jan 5 21:44:44 PST 2022; root:xnu-8019.80.24~23/RELEASE_ARM64_T8110'
                plist_data['osversionItem']['kernosrelease'] = '21.3.0'
                plist_data['osversionItem']['dylduuid'] = '2F28A224-0775-36D0-B118-8EACCC225191'
                plist_data['osversionItem']['SystemImageID'] = '70245ECA-E2EE-4BAB-8CF6-E8A21949403A'
                plist_data['osversionItem']['BuildID'] = '38018522-8565-11EC-948E-C1C9012B3D54'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2022 Apple Inc.'
            elif osversion == '15.4':
                plist_data['osversionItem']['osversion'] = '15.4'
                plist_data['osversionItem']['osversionBuild'] = '19E241'
                plist_data['osversionItem']['osversionNumber'] = '1858.112'
                plist_data['osversionItem']['buildTime'] = '2022-02-25 20:44:48.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 21.4.0: Mon Feb 21 21:27:57 PST 2022; root:xnu-8020.102.3~1/RELEASE_ARM64_T8110'
                plist_data['osversionItem']['kernosrelease'] = '21.4.0'
                plist_data['osversionItem']['dylduuid'] = '5C4972A8-EF81-32DC-A848-42CC7F7874CF'
                plist_data['osversionItem']['SystemImageID'] = '1DD77CC2-525D-4B33-A485-273C5663447C'
                plist_data['osversionItem']['BuildID'] = '55FDA52A-9630-11EC-A16D-926371514C11'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2022 Apple Inc.'
            elif osversion == '15.4.1':
                plist_data['osversionItem']['osversion'] = '15.4.1'
                plist_data['osversionItem']['osversionBuild'] = '19E258'
                plist_data['osversionItem']['osversionNumber'] = '1858.112'
                plist_data['osversionItem']['buildTime'] = '2022-03-26 15:45:38.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 21.4.0: Mon Feb 21 21:27:57 PST 2022; root:xnu-8020.102.3~1/RELEASE_ARM64_T8110'
                plist_data['osversionItem']['kernosrelease'] = '21.4.0'
                plist_data['osversionItem']['dylduuid'] = '5C4972A8-EF81-32DC-A848-42CC7F7874CF'
                plist_data['osversionItem']['SystemImageID'] = '69D00D53-90BA-40A6-A67D-B3DDA5CE5715'
                plist_data['osversionItem']['BuildID'] = '59005B44-ACD0-11EC-BC82-8A9E29A8C1E3'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2022 Apple Inc.'
            elif osversion == '15.5':
                plist_data['osversionItem']['osversion'] = '15.5'
                plist_data['osversionItem']['osversionBuild'] = '19F77'
                plist_data['osversionItem']['osversionNumber'] = '1863'
                plist_data['osversionItem']['buildTime'] = '2022-05-10 18:37:43.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 21.5.0: Thu Apr 21 21:51:30 PDT 2022; root:xnu-8020.122.1~1/RELEASE_ARM64_T8110'
                plist_data['osversionItem']['kernosrelease'] = '21.5.0'
                plist_data['osversionItem']['dylduuid'] = '0912A37C-9592-34F1-938F-FDBCFCD1CF2F'
                plist_data['osversionItem']['SystemImageID'] = '59A91D03-5D9A-43D9-ADDD-F382D6F4CAF7'
                plist_data['osversionItem']['BuildID'] = 'D7586ED6-D044-11EC-B17C-553C2BCEED73'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2022 Apple Inc.'
            elif osversion == '15.6':
                plist_data['osversionItem']['osversion'] = '15.6'
                plist_data['osversionItem']['osversionBuild'] = '19G71'
                plist_data['osversionItem']['osversionNumber'] = '1866'
                plist_data['osversionItem']['buildTime'] = '2022-07-13 18:35:46.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 21.6.0: Sat Jun 18 18:56:54 PDT 2022; root:xnu-8020.140.41~4/RELEASE_ARM64_T8110'
                plist_data['osversionItem']['kernosrelease'] = '21.6.0'
                plist_data['osversionItem']['dylduuid'] = 'C7B2BEF3-7F6B-36EB-80ED-CC49F96B9BEE'
                plist_data['osversionItem']['SystemImageID'] = 'A0DFE4A0-3627-41DA-98B1-4286B94DC024'
                plist_data['osversionItem']['BuildID'] = '2C12EBE6-028F-11ED-8A19-B57CA291DBA7'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2022 Apple Inc.'
            elif osversion == '16.0':
                plist_data['osversionItem']['osversion'] = '16.0'
                plist_data['osversionItem']['osversionBuild'] = '20A362'
                plist_data['osversionItem']['osversionNumber'] = '1946.102'
                plist_data['osversionItem']['buildTime'] = '2022-09-03 09:37:01.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 22.0.0: Thu Aug 11 19:34:50 PDT 2022; root:xnu-8792.3.9~1/RELEASE_ARM64_T8006'
                plist_data['osversionItem']['kernosrelease'] = '22.0.0'
                plist_data['osversionItem']['dylduuid'] = '341BBF64-6034-357E-8AA6-E1E4B988E03C'
                plist_data['osversionItem']['SystemImageID'] = 'E463CB7E-1189-4929-B4E5-B669877D7BB7'
                plist_data['osversionItem']['BuildID'] = '86A59360-2B20-11ED-B0A8-D0C75CB45F7D'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2022 Apple Inc.'
            elif osversion == '16.1':
                plist_data['osversionItem']['osversion'] = '16.1'
                plist_data['osversionItem']['osversionBuild'] = '20B82'
                plist_data['osversionItem']['osversionNumber'] = '1953.1'
                plist_data['osversionItem']['buildTime'] = '2022-10-19 13:29:49.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 22.1.0: Thu Sep 29 23:20:02 PDT 2022; root:xnu-8792.43.3~6/RELEASE_ARM64_T8006'
                plist_data['osversionItem']['kernosrelease'] = '22.1.0'
                plist_data['osversionItem']['dylduuid'] = '41605DC7-F412-37D1-B51B-FEE1A26701E9'
                plist_data['osversionItem']['SystemImageID'] = '55599997-D030-49C5-8332-A2E24A144A06'
                plist_data['osversionItem']['BuildID'] = 'CB3FF411-4762-34D2-86A4-ECA13F9FB6C3'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2022 Apple Inc.'
            elif osversion == '16.4':
                plist_data['osversionItem']['osversion'] = '16.4'
                plist_data['osversionItem']['osversionBuild'] = '20E247'
                plist_data['osversionItem']['osversionNumber'] = '1971'
                plist_data['osversionItem']['buildTime'] = '2023-03-23 19:07:13.000000000'
                plist_data['osversionItem'][
                    'kernversion'] = 'Darwin Kernel Version 22.4.0: Mon Mar 6 20:23:42 PST 2023; root:xnu-8796.103.6~1/RELEASE_ARM64_T8301'
                plist_data['osversionItem']['kernosrelease'] = '22.4.0'
                plist_data['osversionItem']['dylduuid'] = '41605DC7-F412-37D1-B51B-FEE1A26701E9'
                plist_data['osversionItem']['SystemImageID'] = '669BA8CE-BE4F-420C-AAA5-20FCCF6CA5BA'
                plist_data['osversionItem']['BuildID'] = '7BAF19DC-C962-11ED-86E0-CAF2576C5965'
                plist_data['osversionItem']['ProductCopyright'] = '1983-2023 Apple Inc.'

        # 保存修改后的 plist 数据到文件
        print(plist_data["osversionItem"])
        with open(plist_file, 'wb') as f:
            plistlib.dump(plist_data, f)

    def zip_folder(self, folder_path, zip_file):
        print("开始压缩文件：文件路径"+folder_path +"文件名"+zip_file)
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zip_ref.write(file_path, arcname)

    def extract_zip(self, zip_file, extract_to):
        print("解压缩文件")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

    # 处理单个 .zip 文件
    def process_zip(self, zip_file_name ,osversion):
        print("修改单个文件开始 文件名:"+zip_file_name+"系统版本"+osversion)
        self.log.append(f'[{self.now_time()}]: ' +"开始解压"+ zip_file_name)

        zip_file_path = os.path.join(BASE_DIR, './ir/', zip_file_name)
        print("文件路径:"+zip_file_path)
        self.log.append(f'[{self.now_time()}]: ' + "路径:" + zip_file_path)

        extract_to = os.path.join('./ir/', zip_file_name[:-4])
        print(f"解压路径:"+extract_to)

        # 解压缩 .zip 文件
        self.extract_zip(zip_file_path, extract_to)

        # 找到 ir.plist 文件路径
        plist_file = extract_to + '/IR.plist'

        # 修改 ir.plist 文件
        self.modify_plist(plist_file,osversion)

        # 压缩文件夹为 .zip 文件
        modified_zip_file = "./ir/" + osversion + "-" + zip_file_name
        print(modified_zip_file)
        self.zip_folder(extract_to, modified_zip_file)

        # 删除原文件
        os.remove(zip_file_path)
        print("删除原文件")
        print(zip_file_name)
        abs_path = os.path.abspath('./'+ extract_to + '/')
        new_abs_path = '\\\\?\\' + abs_path
        print(new_abs_path)
        shutil.rmtree(new_abs_path)
        #os.remove(zip_file_name)

        # print(f"Modification and compression complete for {zip_file_name}")


    def setOSmessage(self, osversion):
        osversion_dict = {}
        if osversion == '15.0':
            osversion_dict["osversion"] = "15.0"
            osversion_dict["osversionBuild"] = "19A346"
            osversion_dict["osversionNumber"] = "1854"
            osversion_dict["buildTime"] = "2021-09-16 13:39:21.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 21.0.0: Sun Aug 15 20:55:58 PDT 2021; root:xnu-8019.12.5~1/RELEASE_ARM64_T8101"
            osversion_dict["kernosrelease"] = "21.0.0"
            osversion_dict["dylduuid"] = "D7A0282E-93DE-3A1E-9813-27E84517CC96"
            osversion_dict["SystemImageID"] = "B3FE2383-83F6-4D08-8928-EAE442B4F99C"
            osversion_dict["BuildID"] = "0FD736D6-16A8-11EC-83AB-237CA1EF5A19"
            osversion_dict["ProductCopyright"] = "1983-2021 Apple Inc."
        elif osversion == '15.0.2':
            osversion_dict["osversion"] = "15.0.2"
            osversion_dict["osversionBuild"] = "19A404"
            osversion_dict["osversionNumber"] = "1854"
            osversion_dict["buildTime"] = "2021-10-07 11:06:09.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 21.0.0: Wed Sep 29 08:30:00 PDT 2021; root:xnu-8019.12.5~35/RELEASE_ARM64_T8110"
            osversion_dict["kernosrelease"] = "21.0.0"
            osversion_dict["dylduuid"] = "D7A0282E-93DE-3A1E-9813-27E84517CC96"
            osversion_dict["SystemImageID"] = "C8A92C32-8E44-4782-8405-7616560A5B95"
            osversion_dict["BuildID"] = "239D3DCA-2713-11EC-9C98-70E2489C1635"
            osversion_dict["ProductCopyright"] = "1983-2021 Apple Inc."
        elif osversion == '15.0.1':
            osversion_dict["osversion"] = "15.0.1"
            osversion_dict["osversionBuild"] = "19A348"
            osversion_dict["osversionNumber"] = "1854"
            osversion_dict["buildTime"] = "2021-09-28 19:09:53.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 21.0.0: Sun Aug 15 20:55:58 PDT 2021; root:xnu-8019.12.5~1/RELEASE_ARM64_T8101"
            osversion_dict["kernosrelease"] = "21.0.0"
            osversion_dict["dylduuid"] = "D7A0282E-93DE-3A1E-9813-27E84517CC96"
            osversion_dict["SystemImageID"] = "281FBDC2-0BC2-41DD-8944-E4412ED6BF7F"
            osversion_dict["BuildID"] = "397AEFF0-2044-11EC-9384-D08C742505B7"
            osversion_dict["ProductCopyright"] = "1983-2021 Apple Inc."
        elif osversion == '15.1':
            osversion_dict["osversion"] = "15.1"
            osversion_dict["osversionBuild"] = "19B74"
            osversion_dict["osversionNumber"] = "1855.105000"
            osversion_dict["buildTime"] = "2021-10-15 13:57:35.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 21.1.0: Wed Oct 13 18:16:52 PDT 2021; root:xnu-8019.42.4~1/RELEASE_ARM64_T8110"
            osversion_dict["kernosrelease"] = "21.1.0"
            osversion_dict["dylduuid"] = "5E7EF577-1CC5-369A-A04D-28FBBA883086"
            osversion_dict["SystemImageID"] = "524A74D5-5EAB-461B-A15B-BC4E36E9A9E2"
            osversion_dict["BuildID"] = "69887A86-2D74-11EC-A173-B4EB040748D7"
            osversion_dict["ProductCopyright"] = "1983-2021 Apple Inc."
        elif osversion == '15.2':
            osversion_dict["osversion"] = "15.2"
            osversion_dict["osversionBuild"] = "19C56"
            osversion_dict["osversionNumber"] = "1856.105000"
            osversion_dict["buildTime"] = "2021-12-03 14:27:10.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 21.2.0: Sun Nov 28 20:43:39 PST 2021; root:xnu-8019.62.2~1/RELEASE_ARM64_T8110"
            osversion_dict["kernosrelease"] = "21.2.0"
            osversion_dict["dylduuid"] = "0B12AEC1-CAEF-38AD-8FB7-3CAB3DA30489"
            osversion_dict["SystemImageID"] = "7F19B9A2-ED0F-400E-96EF-02150A2FA3DB"
            osversion_dict["BuildID"] = "AA08C5F6-53F9-11EC-AEA1-89BC549413F1"
            osversion_dict["ProductCopyright"] = "1983-2021 Apple Inc."
        elif osversion == '15.2.1':
            osversion_dict["osversion"] = "15.2.1"
            osversion_dict["osversionBuild"] = "19C63"
            osversion_dict["osversionNumber"] = "1856.105000"
            osversion_dict["buildTime"] = "2022-01-08 12:48:54.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 21.2.0: Sun Nov 28 20:43:39 PST 2021; root:xnu-8019.62.2~1/RELEASE_ARM64_T8110"
            osversion_dict["kernosrelease"] = "21.2.0"
            osversion_dict["dylduuid"] = "0B12AEC1-CAEF-38AD-8FB7-3CAB3DA30489"
            osversion_dict["SystemImageID"] = "49A0E2EA-4213-4DAA-9C95-6CA1E95AF427"
            osversion_dict["BuildID"] = "E63E5132-7035-11EC-93A1-9C3957DBE9D0"
            osversion_dict["ProductCopyright"] = "1983-2022 Apple Inc."
        elif osversion == '15.3':
            osversion_dict["osversion"] = "15.3"
            osversion_dict["osversionBuild"] = "19D50"
            osversion_dict["osversionNumber"] = "1856.105000"
            osversion_dict["buildTime"] = "2022-01-22 17:06:41.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 21.3.0: Wed Jan 5 21:44:44 PST 2022; root:xnu-8019.80.24~23/RELEASE_ARM64_T8110"
            osversion_dict["kernosrelease"] = "21.3.0"
            osversion_dict["dylduuid"] = "2F28A224-0775-36D0-B118-8EACCC225191"
            osversion_dict["SystemImageID"] = "21E0744E-76D1-49E8-8C58-BC8A828CDEAB"
            osversion_dict["BuildID"] = "3B3B4198-7B5A-11EC-956E-40A3ACE7B264"
            osversion_dict["ProductCopyright"] = "1983-2022 Apple Inc."
        elif osversion == '15.3.1':
            osversion_dict["osversion"] = "15.3.1"
            osversion_dict["osversionBuild"] = "19D52"
            osversion_dict["osversionNumber"] = "1856.105000"
            osversion_dict["buildTime"] = "2022-02-04 11:50:31.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 21.3.0: Wed Jan 5 21:44:44 PST 2022; root:xnu-8019.80.24~23/RELEASE_ARM64_T8110"
            osversion_dict["kernosrelease"] = "21.3.0"
            osversion_dict["dylduuid"] = "2F28A224-0775-36D0-B118-8EACCC225191"
            osversion_dict["SystemImageID"] = "70245ECA-E2EE-4BAB-8CF6-E8A21949403A"
            osversion_dict["BuildID"] = "38018522-8565-11EC-948E-C1C9012B3D54"
            osversion_dict["ProductCopyright"] = "1983-2022 Apple Inc."
        elif osversion == '15.4':
            osversion_dict["osversion"] = "15.4"
            osversion_dict["osversionBuild"] = "19E241"
            osversion_dict["osversionNumber"] = "1858.112"
            osversion_dict["buildTime"] = "2022-02-25 20:44:48.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 21.4.0: Mon Feb 21 21:27:57 PST 2022; root:xnu-8020.102.3~1/RELEASE_ARM64_T8110"
            osversion_dict["kernosrelease"] = "21.4.0"
            osversion_dict["dylduuid"] = "5C4972A8-EF81-32DC-A848-42CC7F7874CF"
            osversion_dict["SystemImageID"] = "1DD77CC2-525D-4B33-A485-273C5663447C"
            osversion_dict["BuildID"] = "55FDA52A-9630-11EC-A16D-926371514C11"
            osversion_dict["ProductCopyright"] = "1983-2022 Apple Inc."
        elif osversion == '15.4.1':
            osversion_dict["osversion"] = "15.4.1"
            osversion_dict["osversionBuild"] = "19E258"
            osversion_dict["osversionNumber"] = "1858.112"
            osversion_dict["buildTime"] = "2022-03-26 15:45:38.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 21.4.0: Mon Feb 21 21:27:57 PST 2022; root:xnu-8020.102.3~1/RELEASE_ARM64_T8110"
            osversion_dict["kernosrelease"] = "21.4.0"
            osversion_dict["dylduuid"] = "5C4972A8-EF81-32DC-A848-42CC7F7874CF"
            osversion_dict["SystemImageID"] = "69D00D53-90BA-40A6-A67D-B3DDA5CE5715"
            osversion_dict["BuildID"] = "59005B44-ACD0-11EC-BC82-8A9E29A8C1E3"
            osversion_dict["ProductCopyright"] = "1983-2022 Apple Inc."
        elif osversion == '15.5':
            osversion_dict["osversion"] = "15.5"
            osversion_dict["osversionBuild"] = "19F77"
            osversion_dict["osversionNumber"] = "1863"
            osversion_dict["buildTime"] = "2022-05-10 18:37:43.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 21.5.0: Thu Apr 21 21:51:30 PDT 2022; root:xnu-8020.122.1~1/RELEASE_ARM64_T8110"
            osversion_dict["kernosrelease"] = "21.5.0"
            osversion_dict["dylduuid"] = "0912A37C-9592-34F1-938F-FDBCFCD1CF2F"
            osversion_dict["SystemImageID"] = "59A91D03-5D9A-43D9-ADDD-F382D6F4CAF7"
            osversion_dict["BuildID"] = "D7586ED6-D044-11EC-B17C-553C2BCEED73"
            osversion_dict["ProductCopyright"] = "1983-2022 Apple Inc."
        elif osversion == '15.6':
            osversion_dict["osversion"] = "15.6"
            osversion_dict["osversionBuild"] = "19G71"
            osversion_dict["osversionNumber"] = "1866"
            osversion_dict["buildTime"] = "2022-07-13 18:35:46.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 21.6.0: Sat Jun 18 18:56:54 PDT 2022; root:xnu-8020.140.41~4/RELEASE_ARM64_T8110"
            osversion_dict["kernosrelease"] = "21.6.0"
            osversion_dict["dylduuid"] = "C7B2BEF3-7F6B-36EB-80ED-CC49F96B9BEE"
            osversion_dict["SystemImageID"] = "A0DFE4A0-3627-41DA-98B1-4286B94DC024"
            osversion_dict["BuildID"] = "2C12EBE6-028F-11ED-8A19-B57CA291DBA7"
            osversion_dict["ProductCopyright"] = "1983-2022 Apple Inc."
        elif osversion == '16.0':
            osversion_dict["osversion"] = "16.0"
            osversion_dict["osversionBuild"] = "20A362"
            osversion_dict["osversionNumber"] = "1946.102"
            osversion_dict["buildTime"] = "2022-09-03 09:37:01.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 22.0.0: Thu Aug 11 19:34:50 PDT 2022; root:xnu-8792.3.9~1/RELEASE_ARM64_T8006"
            osversion_dict["kernosrelease"] = "22.0.0"
            osversion_dict["dylduuid"] = "341BBF64-6034-357E-8AA6-E1E4B988E03C"
            osversion_dict["SystemImageID"] = "E463CB7E-1189-4929-B4E5-B669877D7BB7"
            osversion_dict["BuildID"] = "86A59360-2B20-11ED-B0A8-D0C75CB45F7D"
            osversion_dict["ProductCopyright"] = "1983-2022 Apple Inc."
        elif osversion == '16.1':
            osversion_dict["osversion"] = "16.1"
            osversion_dict["osversionBuild"] = "20B82"
            osversion_dict["osversionNumber"] = "1953.1"
            osversion_dict["buildTime"] = "2022-10-19 13:29:49.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 22.1.0: Thu Sep 29 23:20:02 PDT 2022; root:xnu-8792.43.3~6/RELEASE_ARM64_T8006"
            osversion_dict["kernosrelease"] = "22.1.0"
            osversion_dict["dylduuid"] = "41605DC7-F412-37D1-B51B-FEE1A26701E9"
            osversion_dict["SystemImageID"] = "55599997-D030-49C5-8332-A2E24A144A06"
            osversion_dict["BuildID"] = "CB3FF411-4762-34D2-86A4-ECA13F9FB6C3"
            osversion_dict["ProductCopyright"] = "1983-2022 Apple Inc."
        elif osversion == '16.4':
            osversion_dict["osversion"] = "16.4"
            osversion_dict["osversionBuild"] = "20E247"
            osversion_dict["osversionNumber"] = "1971"
            osversion_dict["buildTime"] = "2023-03-23 19:07:13.000000000"
            osversion_dict["kernversion"] = "Darwin Kernel Version 22.4.0: Mon Mar 6 20:23:42 PST 2023; root:xnu-8796.103.6~1/RELEASE_ARM64_T8301"
            osversion_dict["kernosrelease"] = "22.4.0"
            osversion_dict["dylduuid"] = "41605DC7-F412-37D1-B51B-FEE1A26701E9"
            osversion_dict["SystemImageID"] = "669BA8CE-BE4F-420C-AAA5-20FCCF6CA5BA"
            osversion_dict["BuildID"] = "7BAF19DC-C962-11ED-86E0-CAF2576C5965"
            osversion_dict["ProductCopyright"] = "1983-2023 Apple Inc."
        return osversion_dict




if __name__ == '__main__':
    app = QApplication([])
    app.setWindowIcon(QIcon(os.path.join(BASE_DIR, './res/logo.png')))
    gold = RenameOS()
    gold.ui.show()
    app.exec_()


