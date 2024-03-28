import concurrent.futures
import datetime as dt
import os
import plistlib
import re
import shutil
import sys
import threading
import zipfile
import time
from plistlib import load, dump

from PySide2.QtCore import Signal, QObject, QThread
from PySide2.QtGui import QIcon
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication

# 工作路径
BASE_DIR = os.path.dirname(os.path.relpath(sys.argv[0]))
FILES_PATH = os.path.join(BASE_DIR, './ir')
VPNPLIST_PATH = 'com.ss.iphone.ugc.Aweme/Documents/vpn.plist'
UID_PATH = 'com.ss.iphone.ugc.Aweme/Library/Preferences/com.ss.iphone.ugc.Aweme.plist'
APM_PATH = 'com.ss.iphone.ugc.Aweme/Library/Preferences/apm.heimdallr.userdefaults.plist'
IR_PATH = 'IR.plist'
ABS_VPNPLIST_PATH = os.path.join(BASE_DIR, './res/vpn.plist')
THREAD_NUM = 0
CHANGE_NUM = 0

WORK_NUM = 0
CHANGE_WORK_NUM = 0
REPEAT_TIME = 1


class MySignal(QObject):
    signal = Signal(str)

class WorkerThread(QThread):
    countChanged = Signal()
    error_occurred = Signal()
    province_found = Signal(str)
    def __init__(self, work_files,parent,query_type,message,city):
        super().__init__()
        self.work_files = work_files
        self.parent = parent
        self.query_type = query_type
        self.message = message
        self.city = city
        self.unknown_count = 0  # 记录未知UID的数量
        self.found_uids = []  # 存储已经找到的UID
    def run(self):
        if self.query_type == 'query_os':
            for file in self.work_files:
                self.query_os_thread(file)
        elif self.query_type == 'query_createtime':
            for file in self.work_files:
                self.query_createtime_thread(file)
        elif self.query_type == 'query_model':
            for file in self.work_files:
                self.query_model_thread(file)
        elif self.query_type == 'query_province':
            for file in self.work_files:
                self.query_province_thread(file)
        elif self.query_type == 'query_uid':
            for file in self.work_files:
                self.query_uid_thread(file)
        elif self.query_type == 'restore_zipname':
            for file in self.work_files:
                self.restore_zipname_thread(file)
        elif self.query_type == 'custom_os_version':
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = [executor.submit(self.custom_os_version_thread, file) for file in self.work_files]
            # for file in self.work_files:
            #     self.custom_os_version_thread(file)
        elif self.query_type == 'custom_province':
            # with concurrent.futures.ThreadPoolExecutor() as executor:
            #     futures = [executor.submit(self.custom_province_thread, file) for file in self.work_files]
            for file in self.work_files:
                self.custom_province_thread(file)
        self.countChanged.emit()

    def edit_plist(self, province, city):
        plist_msg = {}
        with open(ABS_VPNPLIST_PATH, 'rb') as p:
            plist_msg = load(p)
            print(plist_msg)
        plist_msg['province'] = province
        plist_msg['city'] = city
        print(plist_msg)
        with open(ABS_VPNPLIST_PATH, 'wb') as p:
            dump(plist_msg, p)

    def mycopyfile(self, srcfile, dstpath):  # 复制文件函数
        if not os.path.isfile(srcfile):
            print("%s not exist!" % (srcfile))
        else:
            fpath, fname = os.path.split(srcfile)  # 分离文件名和路径
            if not os.path.exists(dstpath):
                os.makedirs(dstpath)  # 创建路径
            shutil.copy(srcfile, dstpath + fname)  # 复制文件
            print("copy %s -> %s" % (srcfile, dstpath + fname))

    def custom_province_thread(self, file):
        self.emit_message(f'文件{file}开始工作')
        zip_file_path = os.path.join(FILES_PATH, file)
        extract_to = os.path.join(FILES_PATH, "TEMP-" + file[:-4])

        self.edit_plist(self.message, self.city)
        is_hasir = "YES"
        # 解压缩 .zip 文件
        try:
            self.extract_zip(zip_file_path, extract_to)
        except Exception as e:
            self.emit_message(f'发生错误*****解压缩********: {e} ')
            self.error_occurred.emit()  # 发射错误信号
            is_hasir = "NULL"
        else:
            self.emit_message(f'文件{file}解压成功')

        # 修改 vpn.plist 文件
        # 覆盖vpn，plist文件
        plist_file = os.path.join(extract_to, VPNPLIST_PATH)  # 找到 vpn.plist 文件路径
        if os.path.exists(plist_file):
            print("文件存在")
            try:
                self.modify_vpn_plist(plist_file, self.message, self.city)
            except Exception as e:
                self.emit_message(f'发生错误******修改 vpn.plist*******: {e} ')
                self.error_occurred.emit()  # 发射错误信号
                is_hasir = "NULL"
            else:
                self.emit_message(f'文件{file}修改VPN.plist成功')
        else:
            print("文件不存在")
            try:
                plist_file = os.path.join(extract_to, VPNPLIST_PATH.strip('vpn.plist'))  # 找到 vpn.plist 文件路径
                self.mycopyfile(ABS_VPNPLIST_PATH, plist_file)
            except Exception as e:
                self.emit_message(f'发生错误******修改 vpn.plist*******: {e} ')
                self.error_occurred.emit()  # 发射错误信号
                is_hasir = "NULL"
            else:
                self.emit_message(f'文件{file}写入VPN.plist成功')

        self.emit_message(f'文件{file}开始压缩')
        # 压缩文件夹为 .zip 文件
        modified_zip_file = os.path.join(FILES_PATH, self.message + "-自定义-" + file)
        if is_hasir == "NULL":
            modified_zip_file = os.path.join(FILES_PATH, "修改失败" + "-" + file)
        try:
            self.zip_folder(extract_to, modified_zip_file)
        except Exception as e:
            self.emit_message(f'发生错误******压缩文件夹*******: {e} ')
            self.error_occurred.emit()  # 发射错误信号
        else:
            self.emit_message(f'文件{file}压缩成功')

        # 删除原文件
        try:
            os.remove(zip_file_path)
        except Exception as e:
            self.emit_message(f'发生错误****删除原文件*********: {e} ')
            self.error_occurred.emit()  # 发射错误信号

        # 删除解压文件夹
        abs_path = os.path.abspath('./' + extract_to + '/')
        new_abs_path = '\\\\?\\' + abs_path
        print(new_abs_path)
        try:
            shutil.rmtree(new_abs_path)
        except Exception as e:
            self.emit_message(f'发生错误*******删除解压文件夹******: {e} ')
            self.error_occurred.emit()  # 发射错误信号
        else:
            self.emit_message(f'文件{file}处理完毕')

        # self.edit_plist(province, city)
        # global THREAD_NUM
        # 1.获取需要更改的省份
        # 2.读取res中的plist文件 更改省份的值为获取到的省份
        # 3.获取需要更改的文件列表
        # 4.列表循环 解压一个文件到当前目录
        # 5.复制res中的plist文件到指定目录
        # 6.压缩文件夹全部内容到当前目录 并且命名为 省份-自定义省份-uid
        # 7.删除原文件
        # 1.获取需要更改的省份
        # self.log.append(f'[{self.now_time()}]: ' + '写入自定义省份文件开始')
        # self.setButton(False)
        # province = self.choose_pro.currentText()
        # city = self.addcity_input.text()
        # if city:
        #     # 2.读取res中的plist文件 更改省份的值为获取到的省份
        #     self.edit_plist(province, city)
        #     # 3.获取需要更改的文件列表
        #     filelist = self.work_file()
        #     self.log.append(f'[{self.now_time()}]: ' + f'本次需要注入的备份包数量为 {len(filelist)}')
        #     if len(filelist) == 0:
        #         self.setButton(True)
        #         self.log.append(f'[{self.now_time()}]: ' + '写入自定义省份文件完毕')
        #         return
        #     THREAD_NUM = len(filelist)
        #     # 4.列表循环 解压一个文件到当前目录
        #     filepath = os.path.join(BASE_DIR, './ir')
        #     for file in filelist:
        #         # 创建线程请求
        #         argms_plist = [filepath, province, file]
        #         t = threading.Thread(target=self.add_plist, args=(argms_plist,))
        #         t.start()
        # else:
        #     self.my_signal.signal.emit('请先填写城市')
        #     self.setButton(True)

    def custom_os_version_thread(self,file):

        zip_file_path = os.path.join(FILES_PATH, file)
        extract_to = os.path.join(FILES_PATH, "TEMP-"+file[:-4])

        is_hasir = "YES"

        # 解压缩 .zip 文件
        try:
            self.extract_zip(zip_file_path, extract_to)
        except Exception as e:
            self.emit_message(f'发生错误***解压缩****: {e} ')
            self.error_occurred.emit()  # 发射错误信号
            is_hasir = "NULL"
        else:
            self.emit_message(f'文件{file}解压成功')

        # 修改 ir.plist 文件

        plist_file = os.path.join(extract_to, 'IR.plist') # 找到 ir.plist 文件路径
        try:
            self.modify_plist(plist_file, self.message)
        except Exception as e:
            self.emit_message(f'发生错误**修改ir.plist***: {e} ')
            self.error_occurred.emit()  # 发射错误信号
            is_hasir = "NULL"
        else:
            self.emit_message(f'文件{file}修改IR.plist成功')


        self.emit_message(f'文件{file}开始压缩')

        # 压缩文件夹为 .zip 文件
        modified_zip_file = os.path.join(FILES_PATH, self.message + "-" + file)
        if is_hasir == "NULL":
            modified_zip_file = os.path.join(FILES_PATH, "修改失败" + "-" + file)
        try:
            self.zip_folder(extract_to, modified_zip_file)
        except Exception as e:
            self.emit_message(f'发生错误****压缩文件夹****: {e} ')
            self.error_occurred.emit()  # 发射错误信号
        else:
            self.emit_message(f'文件{file}压缩成功')

        # 删除原文件
        try:
            os.remove(zip_file_path)
        except Exception as e:
            self.emit_message(f'发生错误****删除原文件****: {e} ')
            self.error_occurred.emit()  # 发射错误信号


        # 删除解压文件夹
        abs_path = os.path.abspath('./' + extract_to + '/')
        new_abs_path = '\\\\?\\' + abs_path
        print(new_abs_path)
        try:
            shutil.rmtree(new_abs_path)
        except Exception as e:
            self.emit_message(f'发生错误***删除解压文件夹****: {e} ')
            self.error_occurred.emit()  # 发射错误信号
        else:
            self.emit_message(f'文件{file}处理完毕')

    def restore_zipname_thread(self, file):
        file_path = os.path.join(FILES_PATH, file)
        new_name = self.regex_name(file)
        if new_name:
            new_file_path = os.path.join(FILES_PATH, new_name)
        else:
            new_file_path = os.path.join(FILES_PATH, "还原备份命名失败"+file)
            self.error_occurred.emit()
        print(file_path)
        print(new_file_path)
        try:
            os.rename(file_path, new_file_path)
        except Exception as e:
            self.emit_message(f'发生错误*************: {e} ')
            self.error_occurred.emit()  # 发射错误信号
        else:
            self.emit_message(f'文件{file}还原命名成功')

    def regex_name(self, str):
        regex = r"(\d+.zip)"
        find_str = ''
        matches = re.finditer(regex, str, re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1
                # print(match.group(groupNum))
                find_str = match.group(groupNum)
        return find_str

    def query_province_thread(self, file):
        file_path = os.path.join(FILES_PATH, file)
        province = ''
        city = ''
        is_hasvpn = False
        # 读取zip文件
        with zipfile.ZipFile(file_path, 'r') as myzip:
            # zip文件的路径列表
            zip_files = myzip.namelist()
            # 判断是否存在vpn列表
            for i in range(0, len(zip_files)):
                zip_file = zip_files[i]
                if zip_file == VPNPLIST_PATH:
                    is_hasvpn = True
                if is_hasvpn:
                    break
            # 读取省份
            if is_hasvpn:
                # vpn = myzip.open(vpn_path, 'r')
                with myzip.open(VPNPLIST_PATH, 'r') as vpn:
                    pl = load(vpn)
                    province = pl['province']
                    city = pl['phone']
                    self.province_found.emit(province)
            myzip.close()
        new_file_path = ''
        if province == '':
            province = '未知省份'
        if city == '18888888888':
            new_file_path = os.path.join(FILES_PATH, province + '-自定义-' + file)
        else:
            new_file_path = os.path.join(FILES_PATH, province + '-' + file)
        try:
            os.rename(file_path, new_file_path)
        except Exception as e:
            self.emit_message(f'发生错误*************: {e} ')
            self.error_occurred.emit()  # 发射错误信号
        else:
            self.emit_message(f'文件{file}查询成功')

    def query_uid_thread(self, file):
        file_path = os.path.join(FILES_PATH, file)
        is_hasUID = False
        is_hasApm = False
        UID = ''
        # 读取zip文件
        with zipfile.ZipFile(file_path, 'r') as myzip:
            # zip文件的路径列表
            all_filelist = myzip.namelist()
            # 判断是否存在vpn列表
            for i in range(0, len(all_filelist)):
                filelist_name = all_filelist[i]
                if filelist_name == UID_PATH:
                    is_hasUID = True
                if filelist_name == APM_PATH:
                    is_hasApm = True
                if is_hasUID and is_hasApm:
                    break
            # 读取uid
            if is_hasUID:
                with myzip.open(UID_PATH, 'r') as keypath:
                    pl = load(keypath)
                    keybool = 'ABTestCurrentUserKey' in pl.keys()
                    if keybool:
                        UID = pl['ABTestCurrentUserKey']
                    else:
                        for key in pl.keys():
                            tmp_uid = self.regex_version_key(key)
                            print(tmp_uid)
                            if tmp_uid:
                                UID = tmp_uid
                                break
            if is_hasApm and UID == '':
                with myzip.open(APM_PATH, 'r') as apm:
                    pl = load(apm)
                    str_pl = str(pl)
                    print(str_pl)
                    UID = self.regex_uid(str_pl)
            # 关闭文件对象
            myzip.close()

        if UID == '':
            self.unknown_count += 1
        else:
            self.found_uids.append(UID)
        new_file_path = self.get_new_file_path(file,UID)
        try:
            os.rename(file_path, new_file_path)
        except Exception as e:
            self.emit_message(f'发生错误*************: {e} ')
            self.error_occurred.emit()  # 发射错误信号
        else:
            self.emit_message(f'文件{file}查询成功')

    def query_model_thread(self, file):
        file_path = os.path.join(FILES_PATH, file)
        model = ""
        is_hasir = False
        # 读取zip文件
        with zipfile.ZipFile(file_path, 'r') as myzip:
            # zip文件的路径列表
            all_filelist = myzip.namelist()
            # 判断是否存在IR文件
            for filelist_name in all_filelist:
                if filelist_name == IR_PATH:
                    is_hasir = True
                    break
            if is_hasir:
                with myzip.open(IR_PATH, 'r') as ir:
                    try:
                        pl = load(ir)
                        model = pl['Model']
                    except Exception as e:
                        self.emit_message(f'发生错误*************: {e} 文件{file}')
            myzip.close()

        if model == "":
            model = "未知机型"
        new_file_path = os.path.join(FILES_PATH, model + '-' + file)
        try:
            os.rename(file_path, new_file_path)
        except Exception as e:
            self.emit_message(f'发生错误*************: {e} ')
            self.error_occurred.emit()  # 发射错误信号
        else:
            self.emit_message(f'文件{file}查询成功')

    def query_os_thread(self, file):
        file_path = os.path.join(FILES_PATH, file)
        os_version = ""
        is_hasir = False
        # 读取zip文件
        with zipfile.ZipFile(file_path, 'r') as myzip:
            # zip文件的路径列表
            all_filelist = myzip.namelist()
            # 判断是否存在IR文件
            for filelist_name in all_filelist:
                if filelist_name == IR_PATH:
                    is_hasir = True
                    break
            if is_hasir:
                with myzip.open(IR_PATH, 'r') as ir:
                    try:
                        pl = load(ir)
                        RandomOSversion = pl['RandomOSversion']
                        # print(RandomOSversion)
                        if RandomOSversion:
                            # print("存在自定义系统")
                            os_version = pl["osversionItem"]["osversion"]
                            # print(os_version)
                    except Exception as e:
                        self.emit_message(f'发生错误*************: {e} 文件{file}')
            myzip.close()

        if os_version == "":
            os_version = "未自定义系统"
        new_file_path = os.path.join(FILES_PATH, os_version + '-' + file)
        # FILES_PATH + '/' + create_time + '-' + file
        try:
            os.rename(file_path, new_file_path)
        except Exception as e:
            self.emit_message(f'发生错误*************: {e} ')
            self.error_occurred.emit()  # 发射错误信号
        else:
            self.emit_message(f'文件{file}查询成功')

    def query_createtime_thread(self, file):
        file_path = os.path.join(FILES_PATH, file)
        create_time = ""
        with zipfile.ZipFile(file_path, 'r') as myzip:
            all_filelist = myzip.namelist()
            # 判断是否存在Vpn.plist文件
            for i in range(0, len(all_filelist)):
                filelist_name = all_filelist[i]
                if filelist_name == VPNPLIST_PATH:
                    zip_info = myzip.getinfo(VPNPLIST_PATH)
                    create_time = str(zip_info.date_time[0]) + "-" + str(zip_info.date_time[1]) + "-" + str(
                        zip_info.date_time[2])
                    break
            myzip.close()
        if create_time == "":
            create_time = "未知注册时间"
        new_file_path = os.path.join(FILES_PATH, create_time + '-' + file)
        # FILES_PATH + '/' + create_time + '-' + file
        try:
            os.rename(file_path, new_file_path)
        except Exception as e:
            self.emit_message(f'发生错误*************: {e} ')
            self.error_occurred.emit()  # 发射错误信号
        else:
            self.emit_message(f'文件{file}查询成功')

    def emit_message(self, message):
        self.parent.my_signal.signal.emit(message)

    def get_new_file_path(self, file, uid):
        new_file_path = ""
        count = 0
        if uid:
            # 如果找到了uid，则使用uid作为文件名
            # new_file_name = f"{uid}-{file}"
            new_file_path = os.path.join(FILES_PATH, uid + '.zip')
        else:
            # 如果没有找到uid，则使用 "UID未知" 作为前缀，并添加一个计数来确保文件名的唯一性
            new_file_path = os.path.join(FILES_PATH, f"UID未知-{self.unknown_count}-原文件名{file}")

        # 如果发现相同的UID，添加一些额外的信息确保文件名的唯一性
        for item in self.found_uids:
            if item == uid:
                count += 1
        if count > 1:
            new_file_path = os.path.join(FILES_PATH, f"UID重复{count-1}次-查询出的uid-{uid}-原文件名{file}")

        return new_file_path

    def extract_zip(self, zip_file, extract_to):
        print("解压缩文件")
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

    def regex_version_key(self, str):
        regex = r"kTIMConvLastMsgBatchUpdateProcesserVersionKey_(\d+)"
        find_str = ''
        matches = re.finditer(regex, str, re.MULTILINE)
        for matchNum, match in enumerate(matches, start=1):
            for groupNum in range(0, len(match.groups())):
                groupNum = groupNum + 1
                # print(match.group(groupNum))
                find_str = match.group(groupNum)
        return find_str

    def regex_uid(self, str):
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

    def modify_plist(self, plist_file, osversion):
        print("开始修改plist")
        print("文件路径" + plist_file)
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

    def modify_vpn_plist(self, plist_file , province, city):
        with open(plist_file, 'rb')as f:
            plist_data = plistlib.load(f)
            plist_data['province'] = province
            plist_data['city'] = city
            plist_data['phone'] = '18888888888'

        # 保存修改后的 plist 数据到文件
        with open(plist_file, 'wb') as f:
            plistlib.dump(plist_data, f)

    def zip_folder(self, folder_path, zip_file):
        print("开始压缩文件：文件路径" + folder_path + "文件名" + zip_file)
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, folder_path)
                    zip_ref.write(file_path, arcname)




class RenameOS:
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.province_dict = {}  # 存储系统版本号及其出现次数的字典

    def init_ui(self):
        # 从文件中加载ui定义
        self.ui = QUiLoader().load(os.path.join(BASE_DIR, './res/rename.ui'))
        # 初始化控件内容
        self.query_uid_btn = self.ui.renameBT  # UID命名
        self.query_province_btn = self.ui.chaxunBT  # 查询省份
        self.query_model_btn = self.ui.chaxunMD  # 查询机型
        self.query_createtime_btn = self.ui.chaxunZC  # 查询注册时间
        self.query_os_btn = self.ui.chaxunOS  # 查询系统

        self.choose_pro = self.ui.choseprovince  # 省份选择框
        self.addcity_input = self.ui.changecity  # 添加城市输入框
        self.addpro_btn = self.ui.addprovince  # 添加省份按钮

        self.choose_os_btn = self.ui.oscomboBox  # 系统选择框
        self.addos_btn = self.ui.ospushButton  # 添加系统按钮

        self.restore_zipname_btn = self.ui.regexNameBT # 还原备份命名
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

        self.error_count = 0  # 错误计数器
        # 信号绑定
        self.query_uid_btn.clicked.connect(self.query_uid)  # 查询UID
        
        self.query_province_btn.clicked.connect(self.query_province)  # 查询省份
        self.query_model_btn.clicked.connect(self.query_model)  # 查询机型
        self.query_createtime_btn.clicked.connect(self.query_createtime)  # 查询注册时间
        self.query_os_btn.clicked.connect(self.query_os)  # 查询系统版本
        self.restore_zipname_btn.clicked.connect(self.restore_zipname)  # 还原备份命名

        self.addpro_btn.clicked.connect(self.custom_province)  # 添加省份
        self.addos_btn.clicked.connect(self.custom_os_version)  # 添加系统

        # 信号绑定
        self.my_signal = MySignal()
        self.my_signal.signal.connect(self.update)

    def query_os(self):
        # 查询注册时间
        self.my_signal.signal.emit('查询系统开始')
        self.setButton(False)
        # 文件列表
        work_files = self.work_file()
        self.my_signal.signal.emit(f'本次查询 {len(work_files)} 个文件')
        # 遍历文件
        if len(work_files) == 0:
            self.setButton(True)
            self.my_signal.signal.emit(f'查询完毕')
            return

        self.worker_thread = WorkerThread(work_files, self,"query_os","NULL","NULL")
        self.worker_thread.countChanged.connect(self.check_threads)
        self.worker_thread.error_occurred.connect(self.increment_error_count)  # 连接错误信号
        self.worker_thread.start()

    def query_createtime(self):
        # 查询注册时间
        self.my_signal.signal.emit('查询开始')
        self.setButton(False)
        # 文件列表
        work_files = self.work_file()
        self.my_signal.signal.emit(f'本次查询 {len(work_files)} 个文件')

        if len(work_files) == 0:
            self.setButton(True)
            self.my_signal.signal.emit(f'查询完毕')
            return
        self.worker_thread = WorkerThread(work_files, self, "query_createtime","NULL","NULL")
        self.worker_thread.countChanged.connect(self.check_threads)
        self.worker_thread.error_occurred.connect(self.increment_error_count)  # 连接错误信号
        self.worker_thread.start()

    def query_model(self):
        # 查询机型
        self.my_signal.signal.emit('查询开始')
        self.setButton(False)
        # 文件列表
        work_files = self.work_file()
        self.my_signal.signal.emit(f'本次查询 {len(work_files)} 个文件')

        if len(work_files) == 0:
            self.setButton(True)
            self.my_signal.signal.emit(f'查询完毕')
            return
        self.worker_thread = WorkerThread(work_files, self, "query_model","NULL","NULL")
        self.worker_thread.countChanged.connect(self.check_threads)
        self.worker_thread.error_occurred.connect(self.increment_error_count)  # 连接错误信号
        self.worker_thread.start()

    def query_province(self):
        # 查询省份
        self.my_signal.signal.emit('查询开始')
        self.setButton(False)
        # 文件列表
        work_files = self.work_file()
        self.my_signal.signal.emit(f'本次查询 {len(work_files)} 个文件')

        if len(work_files) == 0:
            self.setButton(True)
            self.my_signal.signal.emit(f'查询完毕')
            return
        self.worker_thread = WorkerThread(work_files, self, "query_province","NULL","NULL")
        self.worker_thread.countChanged.connect(self.check_threads)
        self.worker_thread.error_occurred.connect(self.increment_error_count)  # 连接错误信号
        self.worker_thread.province_found.connect(self.handle_province)  # 连接系统版本号发现信号
        self.worker_thread.start()

    def query_uid(self):
        # 查询UID
        self.my_signal.signal.emit('查询开始')
        self.setButton(False)
        # 文件列表
        work_files = self.work_file()
        self.my_signal.signal.emit(f'本次查询 {len(work_files)} 个文件')

        if len(work_files) == 0:
            self.setButton(True)
            self.my_signal.signal.emit(f'查询完毕')
            return
        self.worker_thread = WorkerThread(work_files, self, "query_uid","NULL","NULL")
        self.worker_thread.countChanged.connect(self.check_threads)
        self.worker_thread.error_occurred.connect(self.increment_error_count)  # 连接错误信号
        self.worker_thread.start()

    def restore_zipname(self):
        # 查询UID
        self.my_signal.signal.emit('查询开始')
        self.setButton(False)
        # 文件列表
        work_files = self.work_file()
        self.my_signal.signal.emit(f'本次查询 {len(work_files)} 个文件')

        if len(work_files) == 0:
            self.setButton(True)
            self.my_signal.signal.emit(f'查询完毕')
            return
        self.worker_thread = WorkerThread(work_files, self, "restore_zipname","NULL","NULL")
        self.worker_thread.countChanged.connect(self.check_threads)
        self.worker_thread.error_occurred.connect(self.increment_error_count)  # 连接错误信号
        self.worker_thread.start()

    def custom_os_version(self):
        # 查询UID
        self.my_signal.signal.emit('修改系统开始')
        self.setButton(False)
        # 文件列表
        work_files = self.work_file()
        self.my_signal.signal.emit(f'本次修改 {len(work_files)} 个文件')

        if len(work_files) == 0:
            self.setButton(True)
            self.my_signal.signal.emit(f'修改完毕')
            return
        choose_os_version = self.choose_os_btn.currentText()
        self.worker_thread = WorkerThread(work_files, self, "custom_os_version",choose_os_version,"NULL")
        self.worker_thread.countChanged.connect(self.check_threads)
        self.worker_thread.error_occurred.connect(self.increment_error_count)  # 连接错误信号
        self.worker_thread.start()

    def custom_province(self):
        # 查询UID
        self.my_signal.signal.emit('修改省份开始')
        self.setButton(False)
        # 文件列表
        work_files = self.work_file()
        self.my_signal.signal.emit(f'本次修改 {len(work_files)} 个文件')

        if len(work_files) == 0:
            self.setButton(True)
            self.my_signal.signal.emit(f'修改完毕')
            return
        # 获取需要修改的省份和城市
        province = self.choose_pro.currentText()
        city = self.addcity_input.text()
        if city:
            self.worker_thread = WorkerThread(work_files, self, "custom_province",province,city)
            self.worker_thread.countChanged.connect(self.check_threads)
            self.worker_thread.error_occurred.connect(self.increment_error_count)  # 连接错误信号
            self.worker_thread.start()
        else:
            self.setButton(True)
            self.my_signal.signal.emit(f'请先填写城市')

    def handle_province(self, province):
        if province in self.province_dict:
            self.province_dict[province] += 1
        else:
            self.province_dict[province] = 1

    def check_threads(self):
        self.my_signal.signal.emit(f'查询完毕 失败文件数:{self.error_count}')
        self.update_province_info(self.province_dict)
        self.province_dict = {}
        self.setButton(True)
        self.error_count = 0

    def increment_error_count(self):
        self.error_count += 1

    def update_province_info(self, dict):
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

    def work_file(self):
        files_list = os.listdir(FILES_PATH)
        new_files_list = []
        for i in range(0, len(files_list)):
            file_name = files_list[i]
            newpath = os.path.join(FILES_PATH,file_name)
            # 跳过非zip文件
            if zipfile.is_zipfile(newpath) == False:
                print(newpath)
                continue
            new_files_list.append(file_name)
        return new_files_list

    def now_time(self):
        return dt.datetime.now().strftime('%T')

    def setButton(self, type):
        self.query_uid_btn.setEnabled(type)
        self.query_province_btn.setEnabled(type)
        self.query_model_btn.setEnabled(type)
        self.query_createtime_btn.setEnabled(type)
        self.query_os_btn.setEnabled(type)
        self.addos_btn.setEnabled(type)
        self.addpro_btn.setEnabled(type)
        self.restore_zipname_btn.setEnabled(type)

    def update(self, message):
        self.log.append(f'[{self.now_time()}]: ' + message)


if __name__ == '__main__':
    app = QApplication([])
    app.setWindowIcon(QIcon(os.path.join(BASE_DIR, './res/logo.png')))
    gold = RenameOS()
    gold.ui.show()
    app.exec_()
