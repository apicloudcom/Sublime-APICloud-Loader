#-*-coding:utf-8-*- 
import sublime,sublime_plugin
import os,platform,re,logging,subprocess,json

class ApicloudLoaderCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudLoaderCommand"""
    __adbExe='' 
    __curDir=''
    __pkgName='com.apicloud.apploader'
    __loaderName='apicloud-loader'
    __pendingVersion=''
    __cmdLogType=''
    def __init__(self,arg):
        self.__curDir = os.path.join(sublime.packages_path(),'apicloud-load')
    
    def is_visible(self, dirs): 
        return len(dirs) > 0

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList = os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(self.__curDir,'apicloud.log'),
            filemode='a')
        sublime.status_message(u'开始真机同步')
        logging.info('******************************begin sync********************************')
        logging.info('sync dir is '+dirs[0])
        self.load(dirs[0])
        sublime.status_message(u'真机同步完成')
        logging.info('******************************sync complete********************************')
        
    def checkBasicInfo(self):
        logging.info('checkBasicInfo: current dir is '+self.__curDir)
        if not os.path.exists(os.path.join(self.__curDir,'tools')) or not os.path.isdir(os.path.join(self.__curDir,'tools')):
            logging.info('checkBasicInfo:cannot find adb tools')
            return -1
        if not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.conf')) or not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.apk')):
            logging.info('checkBasicInfo: cannot find appLoader')
            return -1
        import platform
        if 'Darwin' in platform.system() or 'Linux' in platform.system():
            self.__adbExe='"'+os.path.join(self.__curDir,'tools','adb')+'"'    
        else:                
            self.__adbExe='"'+os.path.join(self.__curDir,'tools','adb.exe')+'"'
        logging.info("checkBasicInfo: adbCmd is "+self.__adbExe)
        with open(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.conf')) as f:
            config = json.load(f)
            logging.info('checkBasicInfo: config content is '+str(config))
            if 'version' in config:
                self.__pendingVersion=config['version']
            if 'cmdLogType' in config:
                self.__cmdLogType=config['cmdLogType']
        return 0

    def getDeviceListCmd(self):
        logging.info('begin getDeviceListCmd')
        sublime.status_message(u'获得设备列表')
        cmd = self.__adbExe+' devices'
        logging.info('getDeviceListCmd: cmd is '+cmd)
        output = os.popen(cmd)
        deviceList = []
        lines=output.readlines()
        for line in lines:
            if 'List of devices attached' not in line:
                if 'device' in line:
                    deviceList.append(line.split('\tdevice')[0].strip())
        logging.info('getDeviceListCmd: output is \n'+(''.join(lines)))
        logging.info('getDeviceListCmd: deviceList is '+str(deviceList))
        return deviceList

    def getAppId(self, srcPath):
        logging.info('begin getAppId: srcPath is '+srcPath)
        appId = -1
        if not os.path.exists(srcPath) or not os.path.isdir(srcPath):
            logging.info('getAppId:file no exist or not a folder!')
            return appId
        appFileList = os.listdir(srcPath)
        if 'config.xml' not in appFileList:
            logging.info('getAppId: please make sure sync the correct folder!')
            return -1
        with open(os.path.join(srcPath,"config.xml"),encoding='utf-8') as f:
            fileContent = f.read()
            r = re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
            searchResList = r.findall(fileContent)  
        if len(searchResList)>0:
            appId = searchResList[0]
        logging.info('getAppId: appId is '+appId)
        return appId

    def getLoaderType(self,appId):
        logging.info('begin getLoaderType')
        appIdPath=os.path.join(sublime.packages_path(),'apicloud-load','appLoader','custom-loader',appId)
        logging.info('getLoaderType: appIdPath is '+os.path.join(appIdPath,'load.conf'))
        
        if os.path.exists(os.path.join(appIdPath,'load.conf')) and os.path.exists(os.path.join(appIdPath,'load.apk')):
            logging.info('getLoaderType: It is may a customerized loader.')
            with open(os.path.join(appIdPath,'load.conf')) as f:
                config = json.load(f)
                logging.info('getLoaderType: load.conf content is '+str(config))
                if 'version' in config:
                    version=config['version'].strip()
                if 'packageName' in config:
                    pkgName=config['packageName'].strip()

                if len(version)>0 and len(pkgName)>0:
                    self.__pendingVersion=version
                    self.__pkgName=pkgName
                    self.__loaderName='custom-loader'+os.path.sep+appId
                logging.info('getLoaderType: pendingVerion is '+self.__pendingVersion)
                logging.info('getLoaderType: pkgName is '+self.__pkgName)
        else:
            self.__pkgName='com.apicloud.apploader'
            self.__loaderName='apicloud-loader'    
            logging.info('getLoaderType: path not exiest, will use default appLoader') 
        pass

    def runShellCommand(self, cmd, cmdFuncName):
        rtnCode=0
        import platform
        if 'Darwin' in platform.system():
            output=os.popen(cmd)
            logging.info('%s: stdout is \n%s' %(cmdFuncName,str(output.read())))
        else:
            if 'logFile'==self.__cmdLogType:
                p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
                stdout,stderr = p.communicate()
                rtnCode=p.returncode
                if 0==rtnCode:
                    stdoutput=str(stdout)
                    logging.info('%s: stdout is \n%s' %(cmdFuncName, stdoutput))
                    if 'installAppLoaderCmd'==cmdFuncName:
                        if 'Success' not in stdoutput:
                            rtnCode=1
                else:
                    logging.info('%s: stderr is \n%s' %(cmdFuncName, str(stderr)))
            else:    
                p=subprocess.Popen(cmd,shell=False)
                p.wait()
                rtnCode=p.returncode
                
        logging.info('%s: returnCode is %d' %(cmdFuncName,rtnCode))
        return rtnCode

    def pushDirOrFileCmd(self, serialNumber, srcPath, appId):
        srcPath='"'+srcPath+'"'
        logging.info('begin pushDirOrFileCmd from '+srcPath+' for appId '+appId)
        sublime.status_message(u'开始推送widget包')
        desPath='/sdcard/UZMap/wgt/'+appId
        pushCmd=self.__adbExe+' -s '+serialNumber+' push '+srcPath+' '+desPath
        logging.info('pushDirOrFileCmd: pushCmd is '+pushCmd)
        self.runShellCommand(pushCmd,'pushDirOrFileCmd')
        pass

    def pushStartInfo(self, serialNumber, appId):
        logging.info('begin pushStartInfo for appId '+appId)
        sublime.status_message(u'开始推送启动文件')
        desPath='/sdcard/UZMap/A6965066952332/'
        srcPath=os.path.join(self.__curDir,'appLoader','startInfo.txt')
        with open(srcPath,"w") as file:
            file.write(appId)
        srcPath='"'+srcPath+'"'
        logging.info('pushStartInfo: srcPath is '+srcPath+'startInfo.txt')
        pushCmd=self.__adbExe+' -s '+serialNumber+' push '+srcPath+' '+desPath
        logging.info('pushStartInfo: pushCmd is '+pushCmd)
        self.runShellCommand(pushCmd,'pushStartInfo')
        pass

    def compareAppLoaderVer(self,deviceVersion,appLoaderVersion):
        logging.info('begin compareAppLoaderVer '+deviceVersion+' '+appLoaderVersion)
        deviceVersionArray=deviceVersion.split('.')
        appLoaderVersionArray=appLoaderVersion.split('.')
        for i in range(3):
            if appLoaderVersionArray[i]>deviceVersionArray[i]:
                logging.info('compareAppLoaderVer: need update appLoader.')
                return True
        logging.info('compareAppLoaderVer: no need to update appLoader.')
        return False

    def getApploaderVersionCmd(self,serialNumber):
        logging.info('begin getApploaderVersionCmd for device '+serialNumber)
        version=-1
        cmd=self.__adbExe+' -s '+serialNumber+' shell dumpsys package '+self.__pkgName
        logging.info('getApploaderVersionCmd: cmd is '+cmd)
        output=os.popen(cmd)
        verserOutput=output.read()
        r=re.compile("versionName=([0-9]{1,}.[0-9]{1,}.[0-9]{1,})")
        versionList=r.findall(verserOutput)
        if len(versionList)>0:
            version=versionList[0]
        return version

    def installAppLoaderCmd(self, serialNumber):
        logging.info('begin installAppLoaderCmd')
        sublime.status_message(u'开始安装loader')
        appLoader='"'+os.path.join(self.__curDir,'appLoader',self.__loaderName,'load.apk')+'"'
        installCmd=self.__adbExe+' -s '+serialNumber+' install '+appLoader
        logging.info('installAppLoaderCmd: cmd is '+installCmd)
        rtnCode=self.runShellCommand(installCmd,'installAppLoaderCmd')

        if 0!=rtnCode:
            logging.info('installAppLoaderCmd: failed to run installAppLoader!')
            return False
        else:
            if 'logFile'!=self.__cmdLogType:
                if -1==self.getApploaderVersionCmd(serialNumber):
                    logging.info('installAppLoaderCmd: failed to run installAppLoader!')
                    return False
            logging.info('installAppLoaderCmd: installAppLoader success!')
            return True

    def startApploaderCmd(self, serialNumber):
        logging.info('begin startApploaderCmd for device '+serialNumber)
        sublime.status_message(u'正在启动loader')
        appLoaderPkg=self.__pkgName+'/com.uzmap.pkg.EntranceActivity'
        logging.info('startApploaderCmd: pkg name is '+appLoaderPkg)
        startCmd=self.__adbExe +' -s '+serialNumber+' shell am start -W -n '+appLoaderPkg
        logging.info('startApploaderCmd: cmd is '+startCmd)
        rtnCode=self.runShellCommand(startCmd,'startApploaderCmd')
        if 0!=rtnCode:
            logging.info('startApploaderCmd: failed to run startApploaderCmd!')
            return False
        else:
            logging.info('startApploaderCmd: startApploaderCmd success!')
            return True

    def stopApploaderCmd(self, serialNumber):
        logging.info('begin stopApploaderCmd for device '+serialNumber)
        sublime.status_message(u'停止设备上的loader')
        stopCmd=self.__adbExe +' -s '+serialNumber+' shell am force-stop '+self.__pkgName
        logging.info('stopApploaderCmd: cmd is '+stopCmd)
        output=os.popen(stopCmd)
        logging.info('stopApploaderCmd: stopApploaderCmd success!')
        pass

    def uninstallApploaderCmd(self, serialNumber):
        logging.info('begin uninstallApploaderCmd for device '+serialNumber)
        sublime.status_message(u'正在卸载loader')
        uninstallCmd=self.__adbExe+' -s '+serialNumber+' uninstall '+self.__pkgName
        logging.info(uninstallCmd)
        output=os.popen(uninstallCmd)
        uninstallOutput=str(output.read())
        logging.info('uninstallApploaderCmd: output is \n'+uninstallOutput)
        if 'Failure' in uninstallOutput:
            logging.info('uninstallApploaderCmd: failed to run uninstallApploaderCmd!')
            return False
        logging.info('uninstallApploaderCmd: uninstallApploaderCmd finished!')
        return True

    def load(self,srcPath):
        isNeedInstall=False; 
        retVal=self.checkBasicInfo()
        if -1==retVal:
            logging.info('load: failed to checkBasicInfo.')
            sublime.error_message(u'真机同步缺少文件')
            return
        deviceSerialList=self.getDeviceListCmd()
        if 0==len(deviceSerialList):
            logging.info('load: no mobile device found on the computer.')
            sublime.error_message(u'未发现连接的设备')
            return
        appId=self.getAppId(srcPath)
        self.getLoaderType(appId)
        logging.info('load: appId is '+ str(appId))
        if -1==appId:
            sublime.error_message(u'请确保目录正确')
            return 
        for serialNo in deviceSerialList:
            logging.info('load: begin to sync machine '+serialNo)
            self.pushDirOrFileCmd(serialNo,srcPath,appId)

            if self.__pkgName=='com.apicloud.apploader':
                self.pushStartInfo(serialNo,appId)
            currentVersion=self.getApploaderVersionCmd(serialNo)

            if -1!=currentVersion :
                # isNeedInstall=self.compareAppLoaderVer('1.1.28',self.__pendingVersion)
                # isNeedInstall=self.compareAppLoaderVer(currentVersion,'00.00.05')
                isNeedInstall=self.compareAppLoaderVer(currentVersion,self.__pendingVersion)                
            else:
                logging.info('load: no appLoader found on the devices')
                isNeedInstall=True
            
            logging.info('loader: the isNeedInstall flag is '+str(isNeedInstall))
            if isNeedInstall:
                if -1!=currentVersion:
                    if not self.uninstallApploaderCmd(serialNo):
                        logging.info('load: failed to excute uninstallApploaderCmd')
                        sublime.error_message(u'卸载appLoader失败')
                        continue
                if not self.installAppLoaderCmd(serialNo):
                    logging.info('load: failed to excute installAppLoaderCmd')
                    sublime.error_message(u'安装appLoader失败')
                    continue
            else:
                self.stopApploaderCmd(serialNo)

            if not self.startApploaderCmd(serialNo):
                sublime.error_message(u'真机同步启动appLoader失败')
                continue
        pass

import functools
class NewApicloudAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("新建 APICloud 项目名称:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(sublime.packages_path(),'apicloud-load','appLoader','default'),os.path.join(dir, name))
        desFile=os.path.join(dir, name)+"\\config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile  = open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='    <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1

import zipfile
class CompressWidgetCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(sublime.packages_path(),'apicloud-load','apicloud.log'),
            filemode='a')
        dirname=dirs[0]
        filelist = []  
        fulldirname = os.path.abspath(dirname)  
        zipfilename=os.path.basename(fulldirname)+'.zip'
        fullzipfilename = os.path.join(os.path.dirname(fulldirname),zipfilename)  
        logging.info('******************************begin CompressWidgetCommand********************************')
        logging.info("CompressWidgetCommand: Begin to zip %s to %s ..." % (fulldirname, fullzipfilename)  )
        if not os.path.exists(fulldirname):  
            logging.info( "CompressWidgetCommand: Folder %s is not exist" % fulldirname  )
            sublime.error_message(u"文件夹 %s 不存在!" % fulldirname)
            return  
        if os.path.exists(fullzipfilename):      
            flag=sublime.ok_cancel_dialog(u"文件%s 已存在，确定覆盖该文件 ? [Y/N]" % fullzipfilename)
            logging.info("CompressWidgetCommand: %s has already exist" % fullzipfilename  )
            if not flag:
                logging.info('CompressWidgetCommand: cancel zip the folder')
                return

        for root, dirlist, files in os.walk(dirname):  
            for filename in files:  
                filelist.append(os.path.join(root,filename))  

        destZip = zipfile.ZipFile(fullzipfilename, "w")  
        for eachfile in filelist:  
            destfile = eachfile[len(dirname):]  
            sublime.status_message(u"正在压缩文件 file %s." % destfile )
            logging.info("CompressWidgetCommand: Zip file %s." % destfile  )
            destZip.write(eachfile, 'widget'+destfile)  
        destZip.close()  
        sublime.status_message(u'压缩完成')
        logging.info("CompressWidgetCommand: Zip folder succeed!")        
        logging.info('******************************CompressWidgetCommand complete********************************')

    def is_visible(self, dirs):
        return len(dirs) == 1        

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList = os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False