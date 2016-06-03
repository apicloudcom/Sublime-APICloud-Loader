#-*-coding:utf-8-*- 
import sublime,sublime_plugin
import os,platform,re,logging,subprocess,json,sys,traceback,shutil

curDir = os.path.dirname(os.path.realpath(__file__))

html = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="maximum-scale=1.0,minimum-scale=1.0,user-scalable=0,width=device-width,initial-scale=1.0"/>
    <title>title</title>
    <link rel="stylesheet" type="text/css" href="api.css"/>
    <style>
        body{
            
        }
    </style>
</head>
<body>
    
</body>
<script type="text/javascript" src="api.js"></script>
<script type="text/javascript">
    apiready = function(){
        
    };
</script>
</html>'''
class InsertApicloudHtmlCommand(sublime_plugin.TextCommand):
    def run(self, edit, user_input=None):
        self.edit = edit
        v = self.view
        v.insert(edit, 0, html)
        v.end_edit(edit)

class ApicloudNewHtmlCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        v = self.window.new_file()
        v.run_command('insert_apicloud_html')
 
        if len(dirs) == 1:
            v.settings().set('default_dir', dirs[0])

    def is_visible(self, dirs):
        return len(dirs) == 1

############################################global function############################
def isWidgetPath(path):
    isFound = False
    appFileList=os.listdir(path)
    if 'config.xml' in appFileList and 'index.html' in appFileList:
        with open(os.path.join(path,"config.xml"),encoding='utf-8') as f:
            fileContent=f.read()
            r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
            searchResList=r.findall(fileContent)
            if len(searchResList)>0:
                isFound = True
    return isFound

def getWidgetPath(path):
    rootDir = os.path.abspath(path).split(os.path.sep)[0]+os.path.sep
    dirList = []
    for x in range(0,10):
        path = os.path.dirname(path)
        dirList.append(path)
        if path == rootDir:
            break

    syncPath=''
    for path in dirList:
        if isWidgetPath(path):
            syncPath = path
            break
    return syncPath

def runShellCommand(cmd,cmdLogType):
        import platform
        rtnCode=0
        stdout=''
        stderr=''

        if 'darwin' in platform.system().lower():
            p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
            stdoutbyte,stderrbyte=p.communicate()
            stdout=str(stdoutbyte)
            stderr=str(stderrbyte)
            rtnCode=p.returncode

        elif 'windows' in platform.system().lower():
            if 'logFile'==cmdLogType:
                p=subprocess.Popen(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,shell=True)
                stdoutbyte,stderrbyte=p.communicate()
                stdout=str(stdoutbyte)
                stderr=str(stderrbyte)
                rtnCode=p.returncode
            else:    
                p=subprocess.Popen(cmd,shell=False)
                p.wait()
                rtnCode=p.returncode
        else:
            print('runShellCommand: the platform is not support')
        return (rtnCode,stdout,stderr)  

############################################end global function############################

class ApicloudLoaderAndroidKeyCommand(sublime_plugin.TextCommand):
    """docstring for ApicloudLoaderAndroidKeyCommand"""

    def run(self, edit):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(curDir,'apicloud.log'),
            filemode='a')
        sublime.status_message(u'开始真机同步')
        logging.info('*'*30+'begin android key sync'+'*'*30)

        file_name=self.view.file_name()
        syncPath=getWidgetPath(file_name)
        if len(syncPath) > 0:
            logging.info('key sync dir is '+syncPath)
            try:
                BeforeSystemRequests()
                loader = ApicloudLoaderAndroidCommand('')
                loader.load(syncPath)
            except:
                logging.info('run: exception happened as below')
                errMsg=traceback.format_exc()
                logging.info(errMsg)
                # print(errMsg)
                sublime.error_message(u'真机同步出现异常')
            sublime.status_message(u'真机同步完成')
            logging.info('*'*30+'android sync complete'+'*'*30)
        else:
            sublime.error_message(u'请确保当前文件所在目录正确')
        return

class ApicloudLoaderAndroidCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudLoaderAndroidCommand"""
    __adbExe='' 
    __curDir=''
    __pkgName='com.apicloud.apploader'
    __loaderName='apicloud-loader'
    __pendingVersion=''
    __cmdLogType='' #logFile
    __ignore=[".svn",".git"]
    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
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
        logging.info('*'*30+'begin android sync'+'*'*30)
        logging.info('sync dir is '+dirs[0])
        try:
            BeforeSystemRequests()
            self.load(dirs[0])
        except:
            logging.info('run: exception happened as below')
            errMsg=traceback.format_exc()
            logging.info(errMsg)
            sublime.error_message(u'真机同步出现异常')

        sublime.status_message(u'真机同步完成')
        logging.info('*'*30+'android sync complete'+'*'*30)
        
    def checkBasicInfo(self):
        logging.info('checkBasicInfo: current dir is '+self.__curDir)
        if not os.path.exists(os.path.join(self.__curDir,'tools')) or not os.path.isdir(os.path.join(self.__curDir,'tools')):
            logging.info('checkBasicInfo:cannot find adb tools')
            return -1
        if not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.conf')) or not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.apk')):
            logging.info('checkBasicInfo: cannot find appLoader')
            return -1
        import platform
        if 'darwin' in platform.system().lower() :
            self.__adbExe='"'+os.path.join(self.__curDir,'tools','adb')+'"'    
        elif 'windows' in platform.system().lower():                
            self.__adbExe='"'+os.path.join(self.__curDir,'tools','adb.exe')+'"'
        else:
            logging.info('checkBasicInfo: the platform is not support')
            return -1
        logging.info("checkBasicInfo: adbCmd is "+self.__adbExe)
        with open(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.conf')) as f:
            config=json.load(f)
            logging.info('checkBasicInfo: config content is '+str(config))
            if 'version' in config:
                self.__pendingVersion=config['version']
            if 'cmdLogType' in config:
                self.__cmdLogType=config['cmdLogType']
            if 'ignore' in config:
                self.__ignore=config['ignore']
        return 0

    def getDeviceListCmd(self):
        logging.info('begin getDeviceListCmd')
        sublime.status_message(u'获得设备列表')
        cmd=self.__adbExe+' devices'
        logging.info('getDeviceListCmd: cmd is '+cmd)
        output=os.popen(cmd)
        deviceList=[]
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
        appId=-1
        if not os.path.exists(srcPath) or not os.path.isdir(srcPath):
            logging.info('getAppId:file no exist or not a folder!')
            return appId
        appFileList=os.listdir(srcPath)
        if 'config.xml' not in appFileList:
            logging.info('getAppId: please make sure sync the correct folder!')
            return -1
        with open(os.path.join(srcPath,"config.xml"),encoding='utf-8') as f:
            fileContent=f.read()
            r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
            searchResList=r.findall(fileContent)  
        if len(searchResList)>0:
            appId=searchResList[0]
        logging.info('getAppId: appId is '+appId)
        return appId

    def getLoaderType(self,appId):
        logging.info('begin getLoaderType')
        appIdPath=os.path.join(self.__curDir,'appLoader','custom-loader',appId)
        logging.info('getLoaderType: appIdPath is '+os.path.join(appIdPath,'load.conf'))
        
        if os.path.exists(os.path.join(appIdPath,'load.conf')) and os.path.exists(os.path.join(appIdPath,'load.apk')):
            logging.info('getLoaderType: It is may a customerized loader.')
            with open(os.path.join(appIdPath,'load.conf')) as f:
                config=json.load(f)
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

    def pushDirOrFileCmd(self, serialNumber, srcPath, appId):
        fulldirname=os.path.abspath(srcPath)  
        tmpPathName='tmp-apicloud-folder'
        tmpPath=os.path.join(os.path.dirname(srcPath),tmpPathName)
        # force delete .git which is read only
        for (p,d,f) in os.walk(tmpPath):  
            if p.find('.git')>0:  
                if 'windows' in platform.system().lower():
                    os.popen('rd /s /q %s'%p) 
                elif 'darwin' in platform.system().lower():
                    os.popen('rm -rf %s'%p) 
        if os.path.exists(tmpPath):
            self.CleanDir(tmpPath)
            os.rmdir(tmpPath)

        shutil.copytree(srcPath,tmpPath,ignore = shutil.ignore_patterns(*self.__ignore))
        logging.info('begin pushDirOrFileCmd from '+srcPath+' for appId '+appId)
        sublime.status_message(u'开始推送widget包')
        desPath='/sdcard/UZMap/wgt/'+appId
        pushCmd=self.__adbExe+' -s '+serialNumber+' push "'+tmpPath+'" '+desPath
        logging.info('pushDirOrFileCmd: pushCmd is '+pushCmd)
        (rtnCode,stdout,stderr)=runShellCommand(pushCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.info('pushDirOrFileCmd: outputMsg is '+outputMsg)    
        if 'error: device not found' in outputMsg:
            logging.info('pushDirOrFileCmd: failed to run pushDirOrFileCmd')
            return False
        self.CleanDir(tmpPath)
        os.rmdir(tmpPath)
        logging.info('pushDirOrFileCmd: pushDirOrFileCmd success!')
        return True
        
    def CleanDir(self, Dir):
        if os.path.isdir( Dir ):
            paths = os.listdir( Dir )
            for path in paths:
                filePath = os.path.join( Dir, path )
                if os.path.isfile( filePath ):
                    try:
                        os.remove( filePath )
                    except os.error:
                        autoRun.exception( "remove %s error." %filePath )
                elif os.path.isdir( filePath ):
                    shutil.rmtree(filePath,True)
        return True

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
        (rtnCode,stdout,stderr)=runShellCommand(pushCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.info('pushStartInfo: outputMsg is '+outputMsg)    
        if 'error: device not found' in outputMsg:
            logging.info('pushStartInfo: failed to run pushStartInfo')
            return False
        logging.info('pushStartInfo: pushStartInfo success!')
        return True

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

        (rtnCode,stdout,stderr)=runShellCommand(installCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.info('installCmd: outputMsg is '+outputMsg)    
        if len(outputMsg)>0 and 'Success' not in outputMsg:
            logging.info('installAppLoaderCmd: failed to run installAppLoader!')
            return False
        elif 'logFile'!=self.__cmdLogType:
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
        (rtnCode,stdout,stderr)=runShellCommand(startCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.info('startApploaderCmd: outputMsg is '+outputMsg)
        if 'error' in outputMsg:
            logging.info('startApploaderCmd: failed to run startApploaderCmd!')
            return False
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
        logging.info('uninstallApploaderCmd: output is '+uninstallOutput)
        if 'Success' not in uninstallOutput:
            logging.info('uninstallApploaderCmd: failed to run uninstallApploaderCmd!')
            return False
        logging.info('uninstallApploaderCmd: uninstallApploaderCmd finished!')
        return True

    def load(self,srcPath):
        isNeedInstall=False
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
            if not self.pushDirOrFileCmd(serialNo,srcPath,appId):
                sublime.error_message(u'向手机拷贝文件失败，请检查连接设备')
                return
            if self.__pkgName=='com.apicloud.apploader':
                if not self.pushStartInfo(serialNo,appId):
                    sublime.error_message(u'向手机拷贝启动文件失败，请检查连接设备')
                    return

            currentVersion=self.getApploaderVersionCmd(serialNo)
            if -1!=currentVersion :
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
                import time
                time.sleep(1)

            if not self.startApploaderCmd(serialNo):
                sublime.error_message(u'真机同步启动appLoader失败')
                continue
        pass

##############################################################################################

class ApicloudLoaderIosKeyCommand(sublime_plugin.TextCommand):
    """docstring for ApicloudLoaderIosKeyCommand"""

    def run(self, edit):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(curDir,'apicloud.log'),
            filemode='a')
        sublime.status_message(u'开始IOS真机同步')
        logging.info('*'*30+'begin ios key sync'+'*'*30)

        file_name=self.view.file_name()
        syncPath=getWidgetPath(file_name)
        if len(syncPath) > 0:
            logging.info('key sync dir is '+syncPath)
            try:
                BeforeSystemRequests()
                loader = ApicloudLoaderIosCommand('')
                loader.loadIos(syncPath)
            except:
                logging.info('run: exception happened as below')
                errMsg=traceback.format_exc()
                logging.info(errMsg)
                print(errMsg)
                sublime.error_message(u'IOS真机同步出现异常')
            sublime.status_message(u'IOS真机同步完成')
            logging.info('*'*30+'ios key sync complete'+'*'*30)
        else:
            sublime.error_message(u'请确保当前文件所在目录正确')
        return

class ApicloudLoaderIosCommand(sublime_plugin.WindowCommand):
    """docstring for ApicloudIOSLoaderCommand"""
    __adbExe='' 
    __curDir=''
    __pkgName='com.apicloud.apploader'
    __loaderName='apicloud-loader'
    __cmdLogType='' #logFile
    __ignore=['.svn','.git']

    def __init__(self,arg):
        self.__curDir=curDir
    
    def is_visible(self, dirs): 
        return len(dirs) > 0

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False

    def run(self, dirs):
        logging.basicConfig(level=logging.DEBUG,
            format='%(asctime)s %(message)s',
            datefmt='%Y %m %d  %H:%M:%S',
            filename=os.path.join(self.__curDir,'apicloud.log'),
            filemode='a')
        sublime.status_message(u'IOS开始真机同步')
        logging.info('*'*30+'begin ios sync'+'*'*30)
        logging.info('sync dir is '+dirs[0])
        try:
            BeforeSystemRequests()
            self.loadIos(dirs[0])
        except:
            logging.info('run: exception happened as below')
            errMsg=traceback.format_exc()
            logging.info(errMsg)
            print(errMsg)
            sublime.error_message(u'IOS真机同步出现异常')

        sublime.status_message(u'真机同步完成')
        logging.info('*'*30+'ios sync complete'+'*'*30)

    def CleanDir(self, Dir):
        if os.path.isdir( Dir ):
            paths = os.listdir( Dir )
            for path in paths:
                filePath = os.path.join( Dir, path )
                if os.path.isfile( filePath ):
                    try:
                        os.remove( filePath )
                    except os.error:
                        autoRun.exception( "remove %s error." %filePath )
                elif os.path.isdir( filePath ):
                    shutil.rmtree(filePath,True)
        return True        

    def loadIos(self, srcPath):
        logging.info('loadIos: current dir is ')
        if 'windows' in platform.system().lower():
            if not os.path.exists(os.path.join(self.__curDir,'tools','jre','bin')) :
                logging.info('loadIos: cannot find load.conf')
                sublime.error_message(u'缺少JRE环境')
                return
        else: 
            (rtnCode,stdout,stderr)=runShellCommand('java -version',self.__cmdLogType)
            outputMsg=stdout+stderr
            if 'version' not in outputMsg:
                sublime.error_message(u'缺少JRE环境')
                return
        if not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader-ios','load.conf')) or not os.path.exists(os.path.join(self.__curDir,'appLoader','apicloud-loader','load.apk')):
            logging.info('loadIos: cannot find load.conf')
            sublime.error_message(u'真机同步缺少文件')
            return
        appId=self.getAppId(srcPath)
        self.getIosLoaderType(appId)
        logging.info('loadIos: appId is '+ str(appId))
        if -1==appId:
            sublime.error_message(u'请确保目录正确')
            return

        if 'windows' in platform.system().lower():
            javaCmd=os.path.join(self.__curDir,'tools','jre','bin','java')
        else:
            javaCmd='java'

        fulldirname=os.path.abspath(srcPath)  
        tmpPathName='tmp-apicloud-folder'
        tmpPath=os.path.join(os.path.dirname(srcPath),tmpPathName)
        # force delete .git which is read only
        for (p,d,f) in os.walk(tmpPath):  
            if p.find('.git')>0:  
                if 'windows' in platform.system().lower():
                    os.popen('rd /s /q %s'%p) 
                elif 'darwin' in platform.system().lower():
                    os.popen('rm -rf %s'%p) 
        if os.path.exists(tmpPath):
            self.CleanDir(tmpPath)
            os.rmdir(tmpPath)
        shutil.copytree(srcPath,tmpPath,ignore = shutil.ignore_patterns(*self.__ignore))

        jarFile=os.path.join(self.__curDir,'tools','syncapp.jar')
        iosLoaderPath=os.path.join(self.__curDir,'appLoader',self.__loaderName)
        versionFile=os.path.join(iosLoaderPath,'load.conf')
        iosLoaderFile=os.path.join(iosLoaderPath,'load.ipa')

        iosSyncCmd='"'+javaCmd+'" -jar "'+jarFile+'" "'+srcPath+'" "'+iosLoaderPath+'" "'+iosLoaderFile+'" "'+versionFile+'"'
        logging.info('loadIos: cmd is'+iosSyncCmd)
        (rtnCode,stdout,stderr)=runShellCommand(iosSyncCmd,self.__cmdLogType)
        outputMsg=stdout+stderr
        logging.info('loadIos: outputMsg is '+outputMsg)
        self.CleanDir(tmpPath)
        os.rmdir(tmpPath)
        
        if 'No iOS device attached' in outputMsg:
            sublime.error_message(u'未发现连接的设备')
            logging.info('loadIos: no ios device found !')
        elif 'error' in outputMsg or 'failed' in outputMsg:
            logging.info('loadIos: failed to sync ios')
            sublime.error_message(u'IOS真机同步失败')
        else:
            logging.info('loadIos: ios sync success.')
            sublime.message_dialog(u'IOS真机同步完成')

    def getAppId(self, srcPath):
        logging.info('begin getAppId: srcPath is '+srcPath)
        appId=-1
        if not os.path.exists(srcPath) or not os.path.isdir(srcPath):
            logging.info('getAppId:file no exist or not a folder!')
            return appId
        appFileList=os.listdir(srcPath)
        if 'config.xml' not in appFileList:
            logging.info('getAppId: please make sure sync the correct folder!')
            return -1
        with open(os.path.join(srcPath,"config.xml"),encoding='utf-8') as f:
            fileContent=f.read()
            r=re.compile(r"widget.*id.*=.*(A[0-9]{13})\"")
            searchResList=r.findall(fileContent)  
        if len(searchResList)>0:
            appId=searchResList[0]
        logging.info('getAppId: appId is '+appId)
        return appId       

    def getIosLoaderType(self,appId):
        logging.info('getIosLoaderType: begin getIosLoaderType')
        appIdPath=os.path.join(self.__curDir,'appLoader','custom-loader-ios',appId)
        logging.info('getIosLoaderType: appIdPath is '+os.path.join(appIdPath,'load.conf'))
        
        if os.path.exists(os.path.join(appIdPath,'load.conf')) and os.path.exists(os.path.join(appIdPath,'load.ipa')):
            logging.info('getIosLoaderType: It is may a customerized loader.')
            with open(os.path.join(appIdPath,'load.conf')) as f:
                config=json.load(f)
                logging.info('getIosLoaderType: load.conf content is '+str(config))
                if 'version' in config:
                    version=config['version'].strip()
                if 'packageName' in config:
                    pkgName=config['packageName'].strip()
                if 'ignore' in config:
                    self.__ignore==config['ignore']

                if len(version)>0 and len(pkgName)>0:
                    self.__pkgName=pkgName
                    self.__loaderName='custom-loader-ios'+os.path.sep+appId
                logging.info('getIosLoaderType: pkgName is '+self.__pkgName)
        else:
            self.__pkgName='com.apicloud.apploader'
            self.__loaderName='apicloud-loader-ios'    
            logging.info('getIosLoaderType: path not exiest, will use default appLoader') 
        pass         

import os,platform,uuid,urllib.parse,urllib.request,json
def BeforeSystemRequests():
    '''
    the systeminfo uploads to api of ..
    '''
    def get_system_version():
        system_name = platform.system()
        if system_name == 'Windows' and os.name == 'nt':
            system_machine = platform.platform().split('-')[0] + platform.platform().split('-')[1]
        elif system_name == 'Darwin':
            system_machine = 'Mac-os'
        else:
            system_machine = system_name
        return system_machine

    def post(url,data):
        data = urllib.parse.urlencode({'info':data}).encode('utf-8')
        req = urllib.request.Request(url,data)
        urllib.request.urlopen(req)
        return
    def index():
        apiUrl = 'http://www.apicloud.com/setSublimeInfo'
        systemInfo = {
            "system": get_system_version(),
            "uuid": hex(uuid.getnode())
        }
        try:
            systemInfo = json.dumps(systemInfo) 
            post(apiUrl,systemInfo)
        except Exception as e:
            print('exception is :',e)
        finally:
            pass
    try:        
        index()
    except Exception as e:
        pass   

import functools
class NewApicloudDefaultAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("新建 APICloud 项目名称:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','default'),os.path.join(dir, name))
        desFile=os.path.join(dir, name)+"\\config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='    <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1

class NewApicloudBottomAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("新建 APICloud 项目名称:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','bottom'),os.path.join(dir, name))
        desFile=os.path.join(dir, name)+"\\config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='  <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1

class NewApicloudHomeAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("新建 APICloud 项目名称:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','home'),os.path.join(dir, name))
        desFile=os.path.join(dir, name)+"\\config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='  <name>'+name+'</name>\n'
                outputFile.write(line) 
            else:    
                outputFile.write(line) 
        outputFile.close()      

    def is_visible(self, dirs):
        return len(dirs) == 1                

class NewApicloudSlideAppCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("新建 APICloud 项目名称:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        import shutil
        shutil.copytree(os.path.join(curDir,'appLoader','widget','slide'),os.path.join(dir, name))
        desFile=os.path.join(dir, name)+"\\config.xml"
        inputFile=open(desFile,encoding='utf-8')  
        lines=inputFile.readlines()  
        inputFile.close()
        outputFile =open(desFile,'w',encoding='utf-8'); 
        for line in lines:
            if '<name>' in line: 
                line='  <name>'+name+'</name>\n'
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
            filename=os.path.join(curDir,'apicloud.log'),
            filemode='a')
        dirname=dirs[0]
        filelist=[]  
        fulldirname=os.path.abspath(dirname)  
        zipfilename=os.path.basename(fulldirname)+'.zip'
        fullzipfilename=os.path.join(os.path.dirname(fulldirname),zipfilename)  
        logging.info('*'*30+'begin CompressWidgetCommand'+'*'*30)
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

        destZip=zipfile.ZipFile(fullzipfilename, "w")  
        for eachfile in filelist:  
            destfile=eachfile[len(dirname):]  
            sublime.status_message(u"正在压缩文件 file %s." % destfile )
            logging.info("CompressWidgetCommand: Zip file %s." % destfile  )
            destZip.write(eachfile, 'widget'+destfile)  
        destZip.close()  
        sublime.status_message(u'压缩完成')
        logging.info("CompressWidgetCommand: Zip folder succeed!")        
        logging.info('*'*30+'CompressWidgetCommand complete'+'*'*30)

    def is_visible(self, dirs):
        return len(dirs) == 1        

    def is_enabled(self, dirs):
        if 0==len(dirs):
            return False
        appFileList=os.listdir(dirs[0])
        if 'config.xml' in appFileList:
            return True
        return False
